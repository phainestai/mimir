"""
Health check endpoints for AWS Elastic Beanstalk ALB.

Provides /health/ endpoint for ALB target group health checks.
"""

import logging
from django.http import JsonResponse
from django.db import connection
from django.conf import settings
from django.views.decorators.http import require_GET

logger = logging.getLogger(__name__)


@require_GET
def health_check(request):
    """
    Health check endpoint for ALB target group.
    
    Returns 200 OK if:
    - Django is running
    - Database connection is healthy
    
    Returns 503 Service Unavailable if database check fails.
    
    :param request: HTTP request
    :return: JSON response with health status
    """
    logger.info("Health check requested")
    
    health_status = {
        'status': 'healthy',
        'checks': {}
    }
    status_code = 200
    
    # Check database connection
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
        health_status['checks']['database'] = 'ok'
        logger.info("Database health check passed")
    except Exception as e:
        health_status['status'] = 'unhealthy'
        health_status['checks']['database'] = 'failed'
        health_status['error'] = str(e)
        status_code = 503
        logger.error(f"Database health check failed: {e}", exc_info=True)
    
    # Add environment info (non-sensitive)
    health_status['environment'] = getattr(settings, 'MIMIR_ENV', 'unknown')
    
    return JsonResponse(health_status, status=status_code)
