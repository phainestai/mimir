"""Authentication views for user login and logout."""
import logging
from django.contrib.auth import authenticate, login as auth_login, logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import render, redirect
from django.urls import reverse
from django.views.decorators.http import require_http_methods

from accounts.models import mark_onboarding_completed
from django.contrib.auth.decorators import login_required


def settings_view(request):
    """
    Display user settings page.
    
    Scenario: NAV-05 Access settings
    
    Template: accounts/settings.html
    Context: None
    
    :param request: Django request object
    :return: Rendered settings template
    """
    logger.info("[NAV-05] User %s accessed settings page", request.user.username)
    return render(request, 'accounts/settings.html')


logger = logging.getLogger(__name__)


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
    
    # GET request - display form
    if request.method == 'GET':
        logger.info("Displaying login form")
        return render(request, 'accounts/login.html', {
            'errors': {},
            'username': ''
        })
    
    # POST request - handle login
    username = request.POST.get('username', '').strip()
    password = request.POST.get('password', '')
    remember_me = request.POST.get('remember_me') == 'on'
    
    logger.info(f"Login attempt for username: {username}, remember_me: {remember_me}")
    
    # Validate input
    errors = _validate_login_data(username, password)
    if errors:
        logger.warning(f"Login validation failed for username: {username}, errors: {list(errors.keys())}")
        return render(request, 'accounts/login.html', {
            'errors': errors,
            'username': username
        })
    
    # Authenticate
    user = authenticate(request, username=username, password=password)
    
    if user is not None:
        # Successful authentication
        auth_login(request, user)
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
        return render(request, 'accounts/login.html', {
            'errors': errors,
            'username': username
        })


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


def _validate_registration_data(username, email, password, password_confirm):
    """
    Validate registration form data.
    
    Internal helper for register view.
    
    :param username: str - Username from form. Example: "maria"
    :param email: str - Email from form. Example: "maria@example.com"
    :param password: str - Password from form. Example: "SecurePass123"
    :param password_confirm: str - Password confirmation. Example: "SecurePass123"
    :return: dict - Validation errors. Example: {"password": ["Passwords do not match."]}
    
    Validation Rules:
        - Username: Required, non-empty, 3-30 chars, unique
        - Email: Required, valid format, unique
        - Password: Required, min 8 chars
        - Password confirmation: Must match password
    """
    errors = {}
    
    # Username validation
    if not username:
        errors['username'] = ['This field is required.']
    elif len(username) < 3 or len(username) > 30:
        errors['username'] = ['Username must be between 3 and 30 characters.']
    elif User.objects.filter(username=username).exists():
        errors['username'] = ['This username is already taken.']
    
    # Email validation
    if not email:
        errors['email'] = ['This field is required.']
    elif '@' not in email or '.' not in email.split('@')[-1]:
        errors['email'] = ['Enter a valid email address.']
    elif User.objects.filter(email=email).exists():
        errors['email'] = ['This email is already registered.']
    
    # Password validation
    if not password:
        errors['password'] = ['This field is required.']
    elif len(password) < 8:
        errors['password'] = ['Password must be at least 8 characters long.']
    
    # Password confirmation
    if not password_confirm:
        errors['password_confirm'] = ['This field is required.']
    elif password and password_confirm and password != password_confirm:
        errors['password_confirm'] = ['Passwords do not match.']
    
    return errors


@require_http_methods(["GET", "POST"])
def register(request):
    """
    Display registration form and handle user registration.
    
    Custom implementation without Django Forms per SAO.md architecture.
    
    Template: accounts/register.html
    Context:
        errors: dict - Field-specific and non-field errors
        username: str - Preserved username on error
        email: str - Preserved email on error
    
    :param request: Django request object
    :return: Rendered registration template or redirect to onboarding
    """
    logger.info(f"Registration page accessed via {request.method}")
    
    # GET request - display form
    if request.method == 'GET':
        logger.info("Displaying registration form")
        return render(request, 'accounts/register.html', {
            'errors': {},
            'username': '',
            'email': ''
        })
    
    # POST request - handle registration
    username = request.POST.get('username', '').strip()
    email = request.POST.get('email', '').strip()
    password = request.POST.get('password', '')
    password_confirm = request.POST.get('password_confirm', '')
    
    logger.info(f"Registration attempt for username: {username}, email: {email}")
    
    # Validate input
    errors = _validate_registration_data(username, email, password, password_confirm)
    if errors:
        logger.warning(f"Registration validation failed for username: {username}, errors: {list(errors.keys())}")
        return render(request, 'accounts/register.html', {
            'errors': errors,
            'username': username,
            'email': email
        })
    
    # Create user
    try:
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password
        )
        logger.info(f"User {username} created successfully")
        
        # Auto-login
        auth_login(request, user)
        logger.info(f"User {username} auto-logged in after registration")
        
        # Redirect to onboarding
        logger.info(f"Redirecting user {username} to onboarding")
        return redirect('/auth/user/onboarding/')
    except Exception as e:
        logger.error(f"Error creating user {username}: {str(e)}")
        errors = {
            'non_field_errors': ['An error occurred during registration. Please try again.']
        }
        return render(request, 'accounts/register.html', {
            'errors': errors,
            'username': username,
            'email': email
        })


@require_http_methods(["GET", "POST"])
def password_reset_request(request):
    """
    Display password reset request form and send reset email.
    
    Uses console email backend per AUTH_IMPLEMENTATION_PLAN.md.
    
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
    
    # Clear session token
    del request.session[f'password_reset_{uidb64}']
    
    logger.info(f"Password reset successful for user {user.username}")
    
    return render(request, 'accounts/password_reset_confirm.html', {
        'valid_link': True,
        'errors': {},
        'success': True
    })
