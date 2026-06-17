"""Integration tests for password reset (AUTH-04).

Tests from docs/features/act-0-auth/authentication.feature

NO MOCKING per .windsurf/rules/do-not-mock-in-integration-tests.md
Uses locmem email backend only — never sends via SES.
"""
import pytest
from django.conf import settings
from django.contrib.auth.models import User
from django.test import Client
from django.urls import reverse
from django.core import mail


@pytest.mark.django_db
class TestPasswordReset:
    """Test AUTH-04: Password reset flow."""
    
    def test_password_reset_request_sends_email(self):
        """
        Test password reset request captures email in locmem outbox.
        
        Scenario: AUTH-04 Password reset
        Given: Maria has an account
        When: she requests password reset
        Then: email is captured in locmem outbox (no SES)
        """
        # Arrange
        client = Client()
        user = User.objects.create_user(
            username='maria',
            email='maria@example.com',
            password='OldPass123'
        )
        reset_url = reverse('password_reset')
        
        # Act
        response = client.post(reset_url, {
            'email': 'maria@example.com',
        })
        
        # Assert - Should stay on page with success
        assert response.status_code == 200
        content = response.content.decode('utf-8')
        assert 'sent' in content.lower() or 'email' in content.lower()
        
        # Assert - Email captured in locmem (never SES)
        assert "django_ses" not in settings.EMAIL_BACKEND
        assert len(mail.outbox) == 1
        assert mail.outbox[0].to == ['maria@example.com']
        assert mail.outbox[0].from_email == settings.DEFAULT_FROM_EMAIL
        assert 'Password Reset' in mail.outbox[0].subject
        assert 'password-reset-confirm' in mail.outbox[0].body
    
    def test_password_reset_with_nonexistent_email_shows_success(self):
        """
        Test password reset with non-existent email still shows success.
        
        Security: Don't reveal which emails exist.
        
        Scenario: Password reset for non-existent email
        Given: Email doesn't exist in system
        When: User requests reset
        Then: Success message shown (security best practice)
        """
        # Arrange
        client = Client()
        reset_url = reverse('password_reset')
        
        # Act
        response = client.post(reset_url, {
            'email': 'nonexistent@example.com',
        })
        
        # Assert - Should show success (don't reveal if email exists)
        assert response.status_code == 200
        content = response.content.decode('utf-8')
        assert 'sent' in content.lower() or 'email' in content.lower()
        
        # Assert - No email sent
        assert len(mail.outbox) == 0
    
    def test_password_reset_confirm_with_valid_token_resets_password(self):
        """
        Test password reset confirmation with valid token.
        
        Scenario: Complete password reset
        Given: Maria has valid reset token
        When: she sets new password
        Then: password is updated
        And: she can login with new password
        """
        # Arrange
        client = Client()
        user = User.objects.create_user(
            username='maria',
            email='maria@example.com',
            password='OldPass123'
        )
        
        # Request reset to get token
        reset_url = reverse('password_reset')
        client.post(reset_url, {'email': 'maria@example.com'})
        
        # Extract reset link from email
        email_body = mail.outbox[0].body
        # Parse URL from email (simplified - extract uid and token)
        import re
        match = re.search(r'/auth/user/password-reset-confirm/([^/]+)/([^/\s]+)/', email_body)
        assert match, "Reset link should be in email"
        uidb64, token = match.groups()
        
        confirm_url = reverse('password_reset_confirm', kwargs={'uidb64': uidb64, 'token': token})
        
        # Act - Set new password
        response = client.post(confirm_url, {
            'password': 'NewPass456',
            'password_confirm': 'NewPass456',
        })
        
        # Assert - Should show success
        assert response.status_code == 200
        content = response.content.decode('utf-8')
        assert 'success' in content.lower()
        
        # Assert - Can login with new password
        login_url = reverse('login')
        login_response = client.post(login_url, {
            'username': 'maria',
            'password': 'NewPass456',
        })
        assert login_response.status_code == 302  # Redirect on success
        
        # Assert - Cannot login with old password
        client2 = Client()
        old_login = client2.post(login_url, {
            'username': 'maria',
            'password': 'OldPass123',
        })
        assert old_login.status_code == 200  # Stays on page (error)
    
    def test_password_reset_confirm_with_invalid_token_shows_error(self):
        """
        Test password reset with invalid token shows error.
        
        Scenario: Invalid reset link
        Given: Invalid or expired token
        When: User accesses reset link
        Then: Error message shown
        """
        # Arrange
        client = Client()
        confirm_url = reverse('password_reset_confirm', kwargs={
            'uidb64': 'invalid',
            'token': 'invalid-token'
        })
        
        # Act
        response = client.get(confirm_url)
        
        # Assert
        assert response.status_code == 200
        content = response.content.decode('utf-8')
        assert 'invalid' in content.lower() or 'expired' in content.lower()
    
    def test_password_reset_confirm_with_mismatched_passwords_shows_error(self):
        """
        Test password reset with mismatched passwords shows error.
        
        Scenario: Password mismatch during reset
        Given: Valid reset token
        When: Passwords don't match
        Then: Error message shown
        """
        # Arrange
        client = Client()
        user = User.objects.create_user(
            username='maria',
            email='maria@example.com',
            password='OldPass123'
        )
        
        # Request reset
        reset_url = reverse('password_reset')
        client.post(reset_url, {'email': 'maria@example.com'})
        
        # Get token from email
        email_body = mail.outbox[0].body
        import re
        match = re.search(r'/auth/user/password-reset-confirm/([^/]+)/([^/\s]+)/', email_body)
        uidb64, token = match.groups()
        confirm_url = reverse('password_reset_confirm', kwargs={'uidb64': uidb64, 'token': token})
        
        # Act - Mismatched passwords
        response = client.post(confirm_url, {
            'password': 'NewPass456',
            'password_confirm': 'DifferentPass789',
        })
        
        # Assert
        assert response.status_code == 200
        content = response.content.decode('utf-8')
        assert 'do not match' in content.lower() or 'match' in content.lower()
    
    def test_password_reset_link_visible_on_login_page(self):
        """
        Test that password reset link is visible on login page.
        
        Scenario: User on login page
        Then: "Forgot password?" link is visible
        """
        # Arrange
        client = Client()
        login_url = reverse('login')
        
        # Act
        response = client.get(login_url)
        
        # Assert
        content = response.content.decode('utf-8')
        assert 'forgot' in content.lower() or 'reset' in content.lower()
        assert 'password' in content.lower() and 'reset' in content.lower()
    
    def test_get_password_reset_page_displays_form(self):
        """
        Test GET request to password reset shows form.
        
        Scenario: User visits password reset page
        Then: Email input form is displayed
        """
        # Arrange
        client = Client()
        reset_url = reverse('password_reset')
        
        # Act
        response = client.get(reset_url)
        
        # Assert
        assert response.status_code == 200
        assert response.templates[0].name == 'accounts/password_reset.html'
        content = response.content.decode('utf-8')
        assert 'email' in content.lower()
        assert 'data-testid="password-reset-form"' in content
