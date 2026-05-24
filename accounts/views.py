"""Authentication views for user login and logout."""
import logging
from django.conf import settings
from django.contrib.auth import authenticate, login as auth_login, logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from urllib.parse import quote

from django.shortcuts import render, redirect
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_http_methods
from rest_framework.authtoken.models import Token

from accounts.models import (
    UserEmailVerification,
    generate_verification_token,
    get_or_create_email_verification,
    get_or_create_onboarding_state,
    is_email_verification_token_expired,
    mark_email_verified,
    mark_onboarding_completed,
)
from accounts.services.email_service import EmailService
from methodology.models import Playbook, ProcessImprovementProposal

logger = logging.getLogger(__name__)

_PROFILE_PLAYBOOKS_LIMIT = 50
_PROFILE_PIPS_LIMIT = 50


def _redirect_if_authenticated(request):
    """Send logged-in users away from guest-only auth pages (login/register).

    :param request: Django request object
    :return: Redirect to profile when authenticated, else ``None``.
    """
    if request.user.is_authenticated:
        logger.info(
            "Authenticated user %s redirected from guest auth page to profile",
            request.user.username,
        )
        return redirect(reverse("profile"))
    return None


def _profile_playbooks_for(user):
    """Return playbooks authored by user (newest first), capped for the profile page."""
    return list(
        Playbook.objects.filter(author=user)
        .order_by("-updated_at")[:_PROFILE_PLAYBOOKS_LIMIT]
    )


def _profile_pips_for(user):
    """Return PIPs created by user (newest first), capped for the profile page."""
    return list(
        ProcessImprovementProposal.objects.filter(created_by=user)
        .select_related("playbook")
        .order_by("-updated_at")[:_PROFILE_PIPS_LIMIT]
    )


def _regenerate_api_token_for_user(user):
    """Replace the user's DRF API token; old key is invalidated immediately."""
    Token.objects.filter(user=user).delete()
    new_token = Token.objects.create(user=user)
    return new_token


def _validate_login_data(username, password):
    """
    Validate login form data.
    
    Internal helper for login_view.
    
    :param username: str - Username from form. Example: "maria"
    :param password: str - Password from form. Example: "test123"
    :return: dict - Validation errors. Example: {"username": ["This field is required."]}
    
    Validation Rules:
        - Username: Required, non-empty
        - Password: Required, non-empty
    """
    errors = {}
    
    if not username:
        errors['username'] = ['This field is required.']
        logger.debug("Validation error: Username is empty")
    
    if not password:
        errors['password'] = ['This field is required.']
        logger.debug("Validation error: Password is empty")
    
    return errors


def _handle_remember_me(request, remember_me):
    """
    Configure session expiry based on remember me checkbox.
    
    Internal helper for login_view.
    
    :param request: Django request object with authenticated user
    :param remember_me: bool - Remember me checkbox state. Example: True  
    :return: None
    
    Side Effects:
        - Sets request.session.set_expiry(2592000) if remember_me=True (30 days)
        - Sets request.session.set_expiry(1209600) if remember_me=False (2 weeks)
    """
    if remember_me:
        request.session.set_expiry(2592000)  # 30 days
        logger.info(f"User {request.user.username} logged in with remember me (30 days session)")
    else:
        request.session.set_expiry(1209600)  # 2 weeks  
        logger.info(f"User {request.user.username} logged in without remember me (2 weeks session)")


def _user_bypasses_email_verification_gate(user: User) -> bool:
    """Staff and superusers may sign in without an email verification check."""
    return bool(user.is_staff or user.is_superuser)


def _email_verification_login_block(request, user: User, username: str):
    """Return a response that blocks login when email is not verified, or ``None`` to allow.

    :param request: HTTP request.
    :param user: Authenticated user instance.
    :param username: Submitted username (preserved in the form).
    :return: Rendered login page for unverified users, or ``None``.
    """
    if _user_bypasses_email_verification_gate(user):
        return None
    verification = get_or_create_email_verification(user)
    if verification.is_verified:
        return None
    logger.info("[LOGIN] Blocked unverified user_id=%s username=%s", user.pk, username)
    return render(
        request,
        "accounts/login.html",
        {
            "errors": {},
            "username": username,
            "show_resend": True,
            "resend_email": user.email or "",
            "resend_success": False,
        },
    )


def _login_page_context(
    *,
    errors=None,
    username: str = "",
    show_resend: bool = False,
    resend_email: str = "",
    resend_success: bool = False,
):
    """Build standard context dict for ``accounts/login.html``."""
    return {
        "errors": errors or {},
        "username": username,
        "show_resend": show_resend,
        "resend_email": resend_email,
        "resend_success": resend_success,
    }


@never_cache
@require_http_methods(["GET", "POST"])
def login_view(request):
    """
    Display login form and handle authentication.
    
    Custom implementation without Django Forms per SAO.md architecture.
    
    Template: accounts/login.html
    Context:
        errors: dict - Field-specific and non-field errors
        username: str - Preserved username on error
    
    :param request: Django request object
    :return: Rendered login template or redirect to dashboard
    """
    logger.info(f"Login page accessed via {request.method}")

    redirect_response = _redirect_if_authenticated(request)
    if redirect_response is not None:
        return redirect_response
    
    # GET request - display form
    if request.method == 'GET':
        logger.info("Displaying login form")
        resent = request.GET.get("resent") == "1"
        email_changed = request.GET.get("email_changed") == "1"
        pending_resend = (request.GET.get("resend_email") or "").strip()
        return render(
            request,
            "accounts/login.html",
            _login_page_context(
                resend_success=resent,
                show_resend=email_changed and bool(pending_resend),
                resend_email=pending_resend,
            ),
        )
    
    # POST request - handle login
    username = request.POST.get('username', '').strip()
    password = request.POST.get('password', '')
    remember_me = request.POST.get('remember_me') == 'on'
    
    logger.info(f"Login attempt for username: {username}, remember_me: {remember_me}")
    
    # Validate input
    errors = _validate_login_data(username, password)
    if errors:
        logger.warning(f"Login validation failed for username: {username}, errors: {list(errors.keys())}")
        return render(
            request,
            "accounts/login.html",
            _login_page_context(errors=errors, username=username),
        )
    
    # Authenticate
    user = authenticate(request, username=username, password=password)
    
    if user is not None:
        block = _email_verification_login_block(request, user, username)
        if block is not None:
            return block

        auth_login(request, user)
        Token.objects.get_or_create(user=user)
        logger.info(f"User {username} authenticated successfully")

        # Handle remember me
        _handle_remember_me(request, remember_me)

        # Redirect to dashboard
        logger.info(f"Redirecting user {username} to dashboard")
        return redirect('/dashboard/')
    else:
        # Authentication failed
        logger.warning(f"Authentication failed for username: {username}")
        errors = {
            'non_field_errors': ['Invalid username or password. Please try again.']
        }
        return render(
            request,
            "accounts/login.html",
            _login_page_context(errors=errors, username=username),
        )


def custom_logout_view(request):
    """Custom logout view with success message."""
    if request.user.is_authenticated:
        username = request.user.username
        logout(request)
        messages.success(request, "You have been logged out successfully")
        logger.info(f"User {username} logged out successfully")
    else:
        logger.warning("Logout attempted by unauthenticated user")
    
    return redirect(reverse('login'))


@login_required
def profile_view(request):
    """FOB profile: account fields, API token, PIPs and playbooks for the current user."""
    user = request.user
    logger.info(
        "[PROFILE] Page GET user_id=%s username=%s",
        user.pk,
        user.username,
    )
    token, _ = Token.objects.get_or_create(user=user)
    playbooks = _profile_playbooks_for(user)
    pips = _profile_pips_for(user)
    logger.info(
        "[PROFILE] Render user_id=%s playbook_count=%s pip_count=%s",
        user.pk,
        len(playbooks),
        len(pips),
    )
    return render(
        request,
        "accounts/profile.html",
        {
            "first_name": user.first_name,
            "last_name": user.last_name,
            "email": user.email,
            "username": user.username,
            "api_token": token.key,
            "playbooks": playbooks,
            "pips": pips,
        },
    )


def _validate_profile_edit(first_name, last_name, email, current_user):
    """Validate profile edit fields; return errors dict (empty = valid)."""
    errors = {}
    if not email:
        errors["email"] = ["Email is required."]
    elif "@" not in email or "." not in email.split("@")[-1]:
        errors["email"] = ["Enter a valid email address."]
    elif User.objects.filter(email__iexact=email).exclude(pk=current_user.pk).exists():
        errors["email"] = ["That email is already used by another account."]
    return errors


def _profile_email_changed(old_email: str, new_email: str) -> bool:
    """Return True when the normalized email value differs from the prior one."""
    prior = (old_email or "").strip().lower()
    candidate = (new_email or "").strip().lower()
    return prior != candidate


def _complete_email_change_reverification(request, user: User):
    """Invalidate API token, send verification to new address, end session."""
    logger.info("[PROFILE-EDIT] Email change lockout user_id=%s", user.pk)
    token = generate_verification_token(user)
    EmailService.send_verification_email(
        user,
        token,
        base_url=_registration_public_base_url(request),
    )
    Token.objects.filter(user=user).delete()
    messages.warning(
        request,
        "Email updated. Please verify your new address before logging in again.",
    )
    logout(request)
    login_url = (
        f"{reverse('login')}?email_changed=1"
        f"&resend_email={quote(user.email)}"
    )
    return redirect(login_url)


@login_required
@require_http_methods(["GET", "POST"])
def profile_edit_view(request):
    """Edit profile: first name, last name, email."""
    user = request.user
    logger.info("[PROFILE-EDIT] %s user_id=%s", request.method, user.pk)

    if request.method == "GET":
        return render(request, "accounts/profile_edit.html", {
            "first_name": user.first_name,
            "last_name": user.last_name,
            "email": user.email,
            "username": user.username,
            "errors": {},
        })

    first_name = (request.POST.get("first_name") or "").strip()
    last_name = (request.POST.get("last_name") or "").strip()
    email = (request.POST.get("email") or "").strip()

    errors = _validate_profile_edit(first_name, last_name, email, user)
    if errors:
        logger.warning("[PROFILE-EDIT] validation failed user_id=%s errors=%s", user.pk, list(errors))
        return render(request, "accounts/profile_edit.html", {
            "first_name": first_name,
            "last_name": last_name,
            "email": email,
            "username": user.username,
            "errors": errors,
        })

    old_email = user.email
    email_changed = _profile_email_changed(old_email, email)

    user.first_name = first_name
    user.last_name = last_name
    user.email = email
    user.save(update_fields=["first_name", "last_name", "email"])
    logger.info(
        "[PROFILE-EDIT] saved user_id=%s email=%s changed=%s",
        user.pk,
        email,
        email_changed,
    )

    if email_changed and _user_bypasses_email_verification_gate(user):
        mark_email_verified(user)
        messages.success(request, "Profile updated.")
        return redirect(reverse("profile"))

    if email_changed:
        return _complete_email_change_reverification(request, user)

    messages.success(request, "Profile updated.")
    return redirect(reverse("profile"))


@login_required
@require_http_methods(["POST"])
def profile_regenerate_token(request):
    """Invalidate the current API token and issue a new one (password required)."""
    user = request.user
    password = (request.POST.get("current_password") or "").strip()
    logger.info(
        "[PROFILE] Token regenerate POST user_id=%s username=%s password_provided=%s",
        user.pk,
        user.username,
        bool(password),
    )
    if not password:
        messages.error(
            request,
            "Enter your current password to regenerate the API token.",
        )
        logger.warning(
            "[PROFILE] Token regenerate rejected: missing password user_id=%s",
            user.pk,
        )
        return redirect(reverse("profile"))
    if not user.check_password(password):
        messages.error(request, "Incorrect password. Your API token was not changed.")
        logger.warning(
            "[PROFILE] Token regenerate rejected: invalid password user_id=%s",
            user.pk,
        )
        return redirect(reverse("profile"))
    _regenerate_api_token_for_user(user)
    messages.success(
        request,
        "Your API token was regenerated. Update MCP, scripts, and any clients that use the old token.",
    )
    logger.info(
        "[PROFILE] Token regenerated successfully user_id=%s username=%s",
        user.pk,
        user.username,
    )
    return redirect(reverse("profile"))


@login_required
def onboarding(request):
    """
    Onboarding stub page (FOB-ONBOARDING-1).
    
    Placeholder view for first-time user onboarding. Full implementation
    tracked separately in onboarding.feature issues #12-16.
    
    Template: onboarding/welcome.html
    Context: None
    
    :param request: Django request object
    :return: Rendered onboarding stub template
    """
    logger.info(f"User {request.user.username} accessed onboarding stub")
    return render(request, 'onboarding/welcome.html')


@login_required
@require_http_methods(["POST"])
def skip_onboarding(request):
    """Mark onboarding as completed for current user and redirect to dashboard.

    Scenario: ONBOARD-04 Skip onboarding

    Behavior:
        - Ensures onboarding state exists for request.user
        - Sets is_completed=True and current_step=0
        - Redirects to FOB-DASHBOARD-1 (/dashboard/)

    :param request: Django request object
    :return: Redirect response to dashboard
    """
    username = request.user.username
    logger.info("[ONBOARD-04] Skip onboarding requested by user %s", username)

    state = mark_onboarding_completed(request.user, step=0)

    logger.info(
        "[ONBOARD-04] Onboarding marked completed for user %s (is_completed=%s, current_step=%s)",
        username,
        state.is_completed,
        state.current_step,
    )

    logger.info("[ONBOARD-04] Redirecting user %s to dashboard after skip", username)
    return redirect('/dashboard/')


def _registration_public_base_url(request):
    """Return absolute site origin for links inside outbound email.

    Prefer ``settings.FRONTEND_URL`` when set; otherwise derive from request.

    :param request: Current HTTP request.
    :return: Base URL without trailing slash.
    """
    explicit = getattr(settings, "FRONTEND_URL", "").strip()
    if explicit:
        return explicit.rstrip("/")
    return request.build_absolute_uri("/").rstrip("/")


def _find_verification_row(token: str) -> UserEmailVerification | None:
    """Load ``UserEmailVerification`` for a URL token segment, if found.

    :param token: Verification token from the emailed URL segment.
    :return: Row with related ``user`` (via select_related), or ``None`` when
             the segment is blank or unknown (show resend/expired UX).
    """
    trimmed = (token or "").strip()
    if not trimmed:
        logger.warning("[VERIFY_EMAIL] Empty verification token in URL")
        return None
    try:
        return UserEmailVerification.objects.select_related("user").get(
            verification_token=trimmed
        )
    except UserEmailVerification.DoesNotExist:
        logger.warning("[VERIFY_EMAIL] Unknown token (prefix=%s)", trimmed[:8])
        return None


def _resend_verification_if_needed(request, user: User | None) -> None:
    """Send a fresh verification email when *user* exists and still requires it.

    Staff/superuser and already-verified users are skipped. Unknown *user* is a no-op.

    :param request: Current HTTP request (for building email base URL).
    :param user: Target user or ``None``.
    """
    if user is None:
        logger.info("[RESEND_VERIFY] No user match; skipping send")
        return
    if user.is_staff or user.is_superuser:
        logger.info("[RESEND_VERIFY] Staff/superuser skip user_id=%s", user.pk)
        return
    ev = get_or_create_email_verification(user)
    if ev.is_verified:
        logger.info("[RESEND_VERIFY] Already verified skip user_id=%s", user.pk)
        return
    token = generate_verification_token(user)
    EmailService.send_verification_email(
        user,
        token,
        base_url=_registration_public_base_url(request),
    )
    logger.info("[RESEND_VERIFY] Emailed user_id=%s", user.pk)


@require_http_methods(["GET"])
def verify_email(request, token: str):
    """Validate emailed token: verify, expire, or already-verified outcomes."""
    logger.info("[VERIFY_EMAIL] GET token_prefix=%s", (token or "")[:8])
    row = _find_verification_row(token)
    if row is None:
        logger.info("[VERIFY_EMAIL] Unknown/invalid token — showing expired page")
        return render(
            request,
            "accounts/verify_email_result.html",
            {"verify_state": "expired", "resend_email": ""},
        )
    user = row.user
    if row.is_verified:
        messages.info(
            request,
            "Your email is already verified. You can sign in.",
        )
        logger.info("[VERIFY_EMAIL] Already verified user_id=%s", user.pk)
        return redirect(reverse("login"))
    if is_email_verification_token_expired(row):
        logger.info("[VERIFY_EMAIL] Expired user_id=%s", user.pk)
        return render(
            request,
            "accounts/verify_email_result.html",
            {
                "verify_state": "expired",
                "resend_email": user.email,
            },
        )
    mark_email_verified(user)
    messages.success(
        request,
        "Your email has been verified. You can sign in now.",
    )
    logger.info("[VERIFY_EMAIL] Marked verified user_id=%s", user.pk)
    return redirect(reverse("login"))


@require_http_methods(["POST"])
def resend_verification(request):
    """POST-only resend of verification email; response is always non-enumerating."""
    raw_email = request.POST.get("email", "")
    email = (raw_email or "").strip()
    logger.info("[RESEND_VERIFY] POST received email=%s", email or "(empty)")
    user = User.objects.filter(email__iexact=email).first() if email else None
    _resend_verification_if_needed(request, user)
    messages.info(
        request,
        "If an account exists with that email and it still needs verification, "
        "we sent a new verification link.",
    )
    return redirect(f"{reverse('login')}?resent=1")


def _validate_registration_data(
    first_name,
    last_name,
    username,
    email,
    password,
    password_confirm,
    accepted_tos_raw,
):
    """
    Validate registration form data.

    :param accepted_tos_raw: Value of ``accepted_tos`` POST field (``'on'`` or absent).
    :return: dict of field errors; includes ``non_field_errors`` for ToS.
    """
    errors = {}

    if accepted_tos_raw != "on":
        errors.setdefault("non_field_errors", []).append(
            "You must accept the Terms of Service to register."
        )

    fn = (first_name or "").strip()
    ln = (last_name or "").strip()
    if not fn:
        errors["first_name"] = ["This field is required."]
    if not ln:
        errors["last_name"] = ["This field is required."]

    username = (username or "").strip()
    if not username:
        errors["username"] = ["This field is required."]
    elif len(username) < 3 or len(username) > 30:
        errors["username"] = ["Username must be between 3 and 30 characters."]
    elif User.objects.filter(username=username).exists():
        errors["username"] = ["That username is already taken."]

    email = (email or "").strip()
    if not email:
        errors["email"] = ["This field is required."]
    elif "@" not in email or "." not in email.split("@")[-1]:
        errors["email"] = ["Enter a valid email address."]
    elif User.objects.filter(email=email).exists():
        errors["email"] = ["That email is already registered."]

    if not password:
        errors["password"] = ["This field is required."]
    elif len(password) < 8:
        errors["password"] = ["Password must be at least 8 characters long."]

    if not password_confirm:
        errors["password_confirm"] = ["This field is required."]
    elif password and password_confirm and password != password_confirm:
        errors["password_confirm"] = ["Passwords do not match."]

    return errors


@require_http_methods(["GET", "POST"])
def register(request):
    """
    Display registration form and handle user registration.

    Custom implementation without Django Forms per SAO.md architecture.

    On success: user is created, ToS timestamp recorded, verification email sent,
    no auto-login — redirect to login with an info message.
    """
    logger.info("Registration page accessed via %s", request.method)

    redirect_response = _redirect_if_authenticated(request)
    if redirect_response is not None:
        return redirect_response

    empty_ctx = {
        "errors": {},
        "first_name": "",
        "last_name": "",
        "username": "",
        "email": "",
    }

    if request.method == "GET":
        logger.info("Displaying registration form")
        return render(request, "accounts/register.html", empty_ctx)

    first_name = request.POST.get("first_name", "")
    last_name = request.POST.get("last_name", "")
    username = request.POST.get("username", "").strip()
    email = request.POST.get("email", "").strip()
    password = request.POST.get("password", "")
    password_confirm = request.POST.get("password_confirm", "")
    accepted_tos = request.POST.get("accepted_tos")

    logger.info("Registration attempt for username=%s email=%s", username, email)

    errors = _validate_registration_data(
        first_name,
        last_name,
        username,
        email,
        password,
        password_confirm,
        accepted_tos,
    )
    if errors:
        logger.warning(
            "Registration validation failed username=%s keys=%s",
            username,
            list(errors.keys()),
        )
        return render(
            request,
            "accounts/register.html",
            {
                "errors": errors,
                "first_name": first_name,
                "last_name": last_name,
                "username": username,
                "email": email,
            },
        )

    try:
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            first_name=(first_name or "").strip(),
            last_name=(last_name or "").strip(),
        )
        logger.info("User %s created successfully id=%s", username, user.pk)

        ob = get_or_create_onboarding_state(user)
        ob.accepted_tos_at = timezone.now()
        ob.save(update_fields=["accepted_tos_at"])

        token = generate_verification_token(user)
        EmailService.send_verification_email(
            user,
            token,
            base_url=_registration_public_base_url(request),
        )

        messages.info(
            request,
            "Account created. Please check your inbox and verify your email before logging in.",
        )
        return redirect(reverse("login"))
    except Exception as e:
        logger.exception("Error creating user %s: %s", username, e)
        return render(
            request,
            "accounts/register.html",
            {
                "errors": {
                    "non_field_errors": [
                        "An error occurred during registration. Please try again."
                    ]
                },
                "first_name": first_name,
                "last_name": last_name,
                "username": username,
                "email": email,
            },
        )


@require_http_methods(["GET", "POST"])
def password_reset_request(request):
    """
    Display password reset request form and send reset email.

    Uses Django ``EMAIL_BACKEND`` (SES in dev/prod; locmem in tests).
    
    Template: accounts/password_reset.html
    Context:
        errors: dict - Field-specific errors
        email: str - Preserved email on error
        success: bool - Email sent successfully
    
    :param request: Django request object
    :return: Rendered password reset template
    """
    logger.info(f"Password reset page accessed via {request.method}")
    
    if request.method == 'GET':
        logger.info("Displaying password reset form")
        return render(request, 'accounts/password_reset.html', {
            'errors': {},
            'email': '',
            'success': False
        })
    
    # POST request - send reset email
    email = request.POST.get('email', '').strip()
    
    logger.info(f"Password reset request for email: {email}")
    
    # Validate email
    if not email:
        logger.warning("Password reset: empty email")
        return render(request, 'accounts/password_reset.html', {
            'errors': {'email': ['This field is required.']},
            'email': email,
            'success': False
        })
    
    # Check if user exists (security: always show success to prevent enumeration)
    try:
        user = User.objects.get(email=email)
        logger.info(f"Password reset: user found for email {email}")
        
        # Generate reset token (simplified - in production use django.contrib.auth.tokens)
        from django.utils.http import urlsafe_base64_encode
        from django.utils.encoding import force_bytes
        import secrets
        
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = secrets.token_urlsafe(32)
        
        # Store token in session (simplified - production should use proper token generator)
        request.session[f'password_reset_{uid}'] = {
            'token': token,
            'user_id': user.pk,
            'timestamp': str(__import__('datetime').datetime.now())
        }
        
        # Send email (console backend - will print to console)
        from django.core.mail import send_mail
        from django.urls import reverse
        
        reset_url = request.build_absolute_uri(
            reverse('password_reset_confirm', kwargs={'uidb64': uid, 'token': token})
        )
        
        send_mail(
            subject='Password Reset - Mimir',
            message=f'Click the link to reset your password:\n\n{reset_url}\n\nIf you did not request this, please ignore this email.',
            from_email='noreply@mimir.local',
            recipient_list=[email],
            fail_silently=False,
        )
        
        logger.info(f"Password reset email sent to {email}")
    except User.DoesNotExist:
        # Security: Don't reveal if email exists
        logger.warning(f"Password reset requested for non-existent email: {email}")
    
    # Always show success message (security best practice)
    return render(request, 'accounts/password_reset.html', {
        'errors': {},
        'email': email,
        'success': True
    })


@require_http_methods(["GET", "POST"])
def password_reset_confirm(request, uidb64, token):
    """
    Confirm password reset and set new password.
    
    Template: accounts/password_reset_confirm.html
    Context:
        errors: dict - Field-specific errors
        valid_link: bool - Token is valid
        success: bool - Password reset successfully
    
    :param request: Django request object
    :param uidb64: str - Base64 encoded user ID
    :param token: str - Reset token
    :return: Rendered password reset confirm template
    """
    from django.utils.http import urlsafe_base64_decode
    
    logger.info(f"Password reset confirm accessed via {request.method}")
    
    # Validate token
    try:
        uid = urlsafe_base64_decode(uidb64).decode()
        session_data = request.session.get(f'password_reset_{uidb64}')
        
        if not session_data or session_data['token'] != token:
            logger.warning(f"Invalid password reset token for uid {uid}")
            return render(request, 'accounts/password_reset_confirm.html', {
                'valid_link': False,
                'errors': {},
                'success': False
            })
        
        user = User.objects.get(pk=session_data['user_id'])
        logger.info(f"Valid password reset token for user {user.username}")
        
    except (TypeError, ValueError, OverflowError, User.DoesNotExist, KeyError):
        logger.error("Invalid password reset link")
        return render(request, 'accounts/password_reset_confirm.html', {
            'valid_link': False,
            'errors': {},
            'success': False
        })
    
    if request.method == 'GET':
        return render(request, 'accounts/password_reset_confirm.html', {
            'valid_link': True,
            'errors': {},
            'success': False
        })
    
    # POST - set new password
    password = request.POST.get('password', '')
    password_confirm = request.POST.get('password_confirm', '')
    
    # Validate passwords
    errors = {}
    if not password:
        errors['password'] = ['This field is required.']
    elif len(password) < 8:
        errors['password'] = ['Password must be at least 8 characters long.']
    
    if not password_confirm:
        errors['password_confirm'] = ['This field is required.']
    elif password and password_confirm and password != password_confirm:
        errors['password_confirm'] = ['Passwords do not match.']
    
    if errors:
        logger.warning(f"Password reset validation failed for user {user.username}")
        return render(request, 'accounts/password_reset_confirm.html', {
            'valid_link': True,
            'errors': errors,
            'success': False
        })
    
    # Set new password
    user.set_password(password)
    user.save()

    mark_email_verified(user)
    logger.info("[PASSWORD_RESET] Marked email verified user_id=%s", user.pk)
    
    # Clear session token
    del request.session[f'password_reset_{uidb64}']
    
    logger.info(f"Password reset successful for user {user.username}")
    
    return render(request, 'accounts/password_reset_confirm.html', {
        'valid_link': True,
        'errors': {},
        'success': True
    })
