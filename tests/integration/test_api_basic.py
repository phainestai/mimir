"""
Basic integration tests for DRF API.

Smoke tests to verify API endpoints are accessible and return expected formats.
"""

import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework.authtoken.models import Token
from methodology.models import Playbook

User = get_user_model()


@pytest.mark.django_db
class TestAPIAuthentication:
    """Test API authentication."""

    def test_token_authentication_endpoint(self):
        """Token auth endpoint should return token for valid credentials."""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        client = APIClient()
        response = client.post('/api/auth/token/', {
            'username': 'testuser',
            'password': 'testpass123'
        })
        
        assert response.status_code == 200
        assert 'token' in response.data
        
        # Verify token was created
        token = Token.objects.get(user=user)
        assert response.data['token'] == token.key

    def test_api_requires_authentication(self):
        """API endpoints should require authentication."""
        client = APIClient()
        response = client.get('/api/playbooks/')
        
        assert response.status_code == 401
        assert 'detail' in response.data or 'error' in response.data


@pytest.mark.django_db
class TestPlaybookAPI:
    """Test Playbook API endpoints."""

    def test_list_playbooks_empty(self):
        """List playbooks should return empty list for user with no playbooks."""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        token = Token.objects.create(user=user)
        
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f'Token {token.key}')
        
        response = client.get('/api/playbooks/')
        
        assert response.status_code == 200
        assert response.data['results'] == []

    def test_create_playbook_via_api(self):
        """Create playbook endpoint should create draft playbook."""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        token = Token.objects.create(user=user)
        
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f'Token {token.key}')
        
        response = client.post('/api/playbooks/', {
            'name': 'Test Playbook',
            'description': 'Test description',
            'category': 'development'
        }, format='json')
        
        if response.status_code != 201:
            print(f"Error response: {response.data}")
        assert response.status_code == 201
        assert response.data['name'] == 'Test Playbook'
        assert response.data['status'] == 'draft'
        assert response.data['version'] == '0.1'
        
        # Verify playbook was created in DB
        playbook = Playbook.objects.get(id=response.data['id'])
        assert playbook.name == 'Test Playbook'
        assert playbook.author == user

    def test_get_playbook_detail(self):
        """Get playbook endpoint should return playbook details."""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        token = Token.objects.create(user=user)
        
        playbook = Playbook.objects.create(
            author=user,
            name='Test Playbook',
            description='Test description',
            category='test',
            status='draft',
            version='0.1'
        )
        
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f'Token {token.key}')
        
        response = client.get(f'/api/playbooks/{playbook.id}/')
        
        assert response.status_code == 200
        assert response.data['id'] == playbook.id
        assert response.data['name'] == 'Test Playbook'
        assert 'workflows' in response.data or 'workflow_count' in response.data


@pytest.mark.django_db
class TestAPIErrorHandling:
    """Test API error handling."""

    def test_not_found_error_format(self):
        """API should return consistent error format for 404."""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        token = Token.objects.create(user=user)
        
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f'Token {token.key}')
        
        response = client.get('/api/playbooks/99999/')
        
        assert response.status_code == 404
        # Should have error field
        assert 'error' in response.data or 'detail' in response.data

    def test_validation_error_format(self):
        """API should return consistent error format for validation errors."""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        token = Token.objects.create(user=user)
        
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f'Token {token.key}')
        
        # Missing required fields
        response = client.post('/api/playbooks/', {}, format='json')
        
        assert response.status_code == 400
        # Should have error or validation details
        assert 'error' in response.data or 'name' in response.data
