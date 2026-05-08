"""
Integration tests for user registration API.

Tests registration, token management, and email sending.
"""

import pytest
from unittest.mock import patch, MagicMock
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework.authtoken.models import Token

User = get_user_model()


@pytest.mark.django_db
class TestUserRegistration:
    """Test user registration endpoint."""

    @patch('accounts.services.email_service.EmailService.send_welcome_email')
    def test_register_new_user(self, mock_send_email):
        """Should create user and return token."""
        client = APIClient()
        
        response = client.post('/api/auth/register/', {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password': 'SecurePass123!',
            'first_name': 'New',
            'last_name': 'User'
        }, format='json')
        
        assert response.status_code == 201
        assert 'user' in response.data
        assert 'token' in response.data
        assert response.data['user']['username'] == 'newuser'
        assert response.data['user']['email'] == 'newuser@example.com'
        
        # Verify user created in DB
        user = User.objects.get(username='newuser')
        assert user.email == 'newuser@example.com'
        assert user.first_name == 'New'
        assert user.last_name == 'User'
        
        # Verify token created
        token = Token.objects.get(user=user)
        assert response.data['token'] == token.key
        
        # Verify welcome email was sent
        mock_send_email.assert_called_once_with(user)

    def test_register_missing_username(self):
        """Should reject registration without username."""
        client = APIClient()
        
        response = client.post('/api/auth/register/', {
            'email': 'test@example.com',
            'password': 'SecurePass123!'
        }, format='json')
        
        assert response.status_code == 400
        assert 'error' in response.data
        assert 'username' in response.data['error'].lower()

    def test_register_missing_email(self):
        """Should reject registration without email."""
        client = APIClient()
        
        response = client.post('/api/auth/register/', {
            'username': 'testuser',
            'password': 'SecurePass123!'
        }, format='json')
        
        assert response.status_code == 400
        assert 'error' in response.data
        assert 'email' in response.data['error'].lower()

    def test_register_missing_password(self):
        """Should reject registration without password."""
        client = APIClient()
        
        response = client.post('/api/auth/register/', {
            'username': 'testuser',
            'email': 'test@example.com'
        }, format='json')
        
        assert response.status_code == 400
        assert 'error' in response.data
        assert 'password' in response.data['error'].lower()

    def test_register_duplicate_username(self):
        """Should reject registration with existing username."""
        # Create existing user
        User.objects.create_user(
            username='existing',
            email='existing@example.com',
            password='pass123'
        )
        
        client = APIClient()
        
        response = client.post('/api/auth/register/', {
            'username': 'existing',
            'email': 'different@example.com',
            'password': 'SecurePass123!'
        }, format='json')
        
        assert response.status_code == 400
        assert 'error' in response.data
        assert 'USERNAME_EXISTS' == response.data['code']

    def test_register_duplicate_email(self):
        """Should reject registration with existing email."""
        # Create existing user
        User.objects.create_user(
            username='existing',
            email='existing@example.com',
            password='pass123'
        )
        
        client = APIClient()
        
        response = client.post('/api/auth/register/', {
            'username': 'different',
            'email': 'existing@example.com',
            'password': 'SecurePass123!'
        }, format='json')
        
        assert response.status_code == 400
        assert 'error' in response.data
        assert 'EMAIL_EXISTS' == response.data['code']

    def test_register_weak_password(self):
        """Should reject registration with weak password."""
        client = APIClient()
        
        response = client.post('/api/auth/register/', {
            'username': 'testuser',
            'email': 'test@example.com',
            'password': '123'  # Too short
        }, format='json')
        
        assert response.status_code == 400
        assert 'error' in response.data
        assert 'WEAK_PASSWORD' == response.data['code']

    @patch('accounts.services.email_service.EmailService.send_welcome_email')
    def test_register_email_failure_does_not_block(self, mock_send_email):
        """Registration should succeed even if email fails."""
        # Make email sending fail
        mock_send_email.side_effect = Exception('SES error')
        
        client = APIClient()
        
        response = client.post('/api/auth/register/', {
            'username': 'testuser',
            'email': 'test@example.com',
            'password': 'SecurePass123!'
        }, format='json')
        
        # Should still succeed
        assert response.status_code == 201
        assert 'token' in response.data
        
        # User should be created
        user = User.objects.get(username='testuser')
        assert user is not None


@pytest.mark.django_db
class TestTokenManagement:
    """Test token refresh and revoke endpoints."""

    def test_refresh_token(self):
        """Should create new token and delete old one."""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='pass123'
        )
        old_token = Token.objects.create(user=user)
        old_key = old_token.key
        
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f'Token {old_key}')
        
        response = client.post('/api/auth/token/refresh/')
        
        assert response.status_code == 200
        assert 'token' in response.data
        assert response.data['token'] != old_key
        
        # Old token should be deleted
        assert not Token.objects.filter(key=old_key).exists()
        
        # New token should exist
        assert Token.objects.filter(key=response.data['token']).exists()

    def test_refresh_token_requires_auth(self):
        """Token refresh should require authentication."""
        client = APIClient()
        
        response = client.post('/api/auth/token/refresh/')
        
        assert response.status_code == 401

    def test_revoke_token(self):
        """Should delete user's token."""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='pass123'
        )
        token = Token.objects.create(user=user)
        
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f'Token {token.key}')
        
        response = client.post('/api/auth/token/revoke/')
        
        assert response.status_code == 200
        assert response.data['revoked'] is True
        
        # Token should be deleted
        assert not Token.objects.filter(user=user).exists()

    def test_revoke_token_requires_auth(self):
        """Token revoke should require authentication."""
        client = APIClient()
        
        response = client.post('/api/auth/token/revoke/')
        
        assert response.status_code == 401
