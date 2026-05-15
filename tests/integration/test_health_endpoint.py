"""
Integration tests for /health/ endpoint.

Tests health check endpoint behavior for ALB target group health checks.
"""

import pytest
from django.test import Client
from django.urls import reverse
from unittest.mock import patch


@pytest.mark.django_db
class TestHealthEndpoint:
    """Test /health/ endpoint for ALB health checks."""

    def test_health_endpoint_returns_200_when_healthy(self):
        """Health endpoint should return 200 OK when all checks pass."""
        client = Client()
        response = client.get('/health/')
        
        assert response.status_code == 200
        data = response.json()
        assert data['status'] == 'healthy'
        assert 'checks' in data
        assert data['checks']['database'] == 'ok'

    def test_health_endpoint_includes_environment(self):
        """Health endpoint should include environment info."""
        client = Client()
        response = client.get('/health/')
        
        data = response.json()
        assert 'environment' in data
        # In test env, should be 'test'
        assert data['environment'] in ('test', 'dev', 'prod', 'unknown')

    def test_health_endpoint_returns_503_on_db_failure(self):
        """Health endpoint should return 503 when database check fails."""
        client = Client()
        
        # Mock database connection to raise exception
        with patch('mimir.health_views.connection') as mock_conn:
            mock_cursor = mock_conn.cursor.return_value.__enter__.return_value
            mock_cursor.execute.side_effect = Exception("Database connection failed")
            
            response = client.get('/health/')
            
            assert response.status_code == 503
            data = response.json()
            assert data['status'] == 'unhealthy'
            assert data['checks']['database'] == 'failed'
            assert 'error' in data

    def test_health_endpoint_accessible_without_auth(self):
        """Health endpoint should be accessible without authentication."""
        # ALB health checks don't authenticate
        client = Client()
        response = client.get('/health/')
        
        # Should not redirect to login
        assert response.status_code in (200, 503)
        assert 'login' not in response.url if hasattr(response, 'url') else True

    def test_health_endpoint_logs_check(self, caplog):
        """Health endpoint should log health check requests."""
        import logging
        caplog.set_level(logging.INFO)
        
        client = Client()
        client.get('/health/')
        
        # Should have logged the health check
        assert any('Health check requested' in record.message for record in caplog.records)


@pytest.mark.django_db
class TestHealthEndpointURL:
    """Test health endpoint URL resolution."""

    def test_health_url_resolves(self):
        """Health check URL should resolve correctly."""
        url = reverse('health_check')
        assert url == '/health/'

    def test_health_endpoint_accepts_get_only(self):
        """Health endpoint should only accept GET requests."""
        client = Client()
        
        # GET should work
        response = client.get('/health/')
        assert response.status_code == 200
        
        # POST should return 405 Method Not Allowed
        response = client.post('/health/')
        assert response.status_code == 405
        
        # PUT should return 405
        response = client.put('/health/')
        assert response.status_code == 405
        
        # DELETE should return 405
        response = client.delete('/health/')
        assert response.status_code == 405
