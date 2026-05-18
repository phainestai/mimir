"""Integration tests for navbar navigation links.

Tests that navbar links use correct URLs per URL convention.
This test would have caught the /accounts/ vs /auth/user/ discrepancy.
"""
import pytest
from django.contrib.auth.models import User
from django.test import Client
from django.urls import reverse


@pytest.mark.django_db
class TestNavbarLinks:
    """Test navbar links use correct URL convention."""
    
    def test_navbar_login_link_when_not_authenticated(self):
        """
        Test navbar login link uses correct URL.
        
        When: User is not authenticated
        Then: Navbar shows login link with /auth/user/login/
        """
        client = Client()
        response = client.get('/')
        
        assert response.status_code == 200
        html = response.content.decode('utf-8')
        
        # Should have login link
        assert 'data-testid="login-link"' in html
        
        # Should NOT have old /accounts/ URL
        assert '/accounts/login/' not in html, \
            "Navbar still uses old /accounts/login/ URL"
        
        # Should have new /auth/user/ URL
        assert '/auth/user/login/' in html, \
            "Navbar should use /auth/user/login/ URL"
    
    def test_navbar_logout_link_when_authenticated(self):
        """
        Test navbar logout link uses correct URL.
        
        When: User is authenticated
        Then: Navbar shows logout link with /auth/user/logout/
        """
        client = Client()
        user = User.objects.create_user(username='testuser', password='testpass')
        client.login(username='testuser', password='testpass')
        
        response = client.get('/')
        
        assert response.status_code == 200
        html = response.content.decode('utf-8')
        
        # Should have logout link
        assert 'data-testid="logout-link"' in html
        
        # Should have username display
        assert user.username in html
        
        # Should NOT have old /accounts/ URL
        assert '/accounts/logout/' not in html, \
            "Navbar still uses old /accounts/logout/ URL"
        
        # Should have new /auth/user/ URL (logout is POST, but href still there)
        assert '/auth/user/logout/' in html, \
            "Navbar should use /auth/user/logout/ URL"
    
    def test_navbar_shows_user_info_when_authenticated(self):
        """Test navbar displays user information correctly."""
        client = Client()
        user = User.objects.create_user(username='maria', password='testpass')
        client.login(username='maria', password='testpass')
        
        response = client.get('/')
        html = response.content.decode('utf-8')
        
        # Should show username
        assert 'maria' in html
        assert 'data-testid="user-display"' in html
        
        # Should have profile entry point
        assert 'data-testid="nav-view-profile"' in html
        assert reverse("profile") in html
