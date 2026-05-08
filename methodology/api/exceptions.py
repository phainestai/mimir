"""
Custom exception handler for DRF API.

Provides consistent error response format across all endpoints.
"""

from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status
from django.core.exceptions import ValidationError, PermissionDenied, ObjectDoesNotExist


def custom_exception_handler(exc, context):
    """
    Custom exception handler for consistent error responses.
    
    Returns error responses in format:
    {
        "error": "Human-readable error message",
        "code": "ERROR_CODE",
        "details": {}
    }
    
    :param exc: Exception instance
    :param context: Context dict with view and request
    :return: Response with error details
    """
    # Call DRF's default exception handler first
    response = exception_handler(exc, context)
    
    # If DRF handled it, format the response
    if response is not None:
        error_data = {
            'error': str(exc),
            'code': get_error_code(exc),
        }
        
        # Add details if available
        if hasattr(exc, 'detail'):
            if isinstance(exc.detail, dict):
                error_data['details'] = exc.detail
            elif isinstance(exc.detail, list):
                error_data['details'] = {'messages': exc.detail}
        
        response.data = error_data
        return response
    
    # Handle Django exceptions not caught by DRF
    if isinstance(exc, ValidationError):
        return Response(
            {
                'error': '; '.join(exc.messages) if hasattr(exc, 'messages') else str(exc),
                'code': 'VALIDATION_ERROR',
            },
            status=status.HTTP_400_BAD_REQUEST
        )
    
    if isinstance(exc, PermissionDenied):
        return Response(
            {
                'error': str(exc) or 'Permission denied',
                'code': 'PERMISSION_DENIED',
            },
            status=status.HTTP_403_FORBIDDEN
        )
    
    if isinstance(exc, ObjectDoesNotExist):
        return Response(
            {
                'error': str(exc) or 'Resource not found',
                'code': 'NOT_FOUND',
            },
            status=status.HTTP_404_NOT_FOUND
        )
    
    # Handle ValueError (from MCP tools)
    if isinstance(exc, ValueError):
        return Response(
            {
                'error': str(exc),
                'code': 'VALIDATION_ERROR',
            },
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Default: let Django handle it (500 error)
    return None


def get_error_code(exc):
    """
    Map exception type to error code.
    
    :param exc: Exception instance
    :return: Error code string
    """
    exc_class = exc.__class__.__name__
    
    # Map common DRF exceptions
    error_code_map = {
        'ValidationError': 'VALIDATION_ERROR',
        'PermissionDenied': 'PERMISSION_DENIED',
        'NotAuthenticated': 'UNAUTHORIZED',
        'AuthenticationFailed': 'UNAUTHORIZED',
        'NotFound': 'NOT_FOUND',
        'MethodNotAllowed': 'METHOD_NOT_ALLOWED',
        'Throttled': 'RATE_LIMIT_EXCEEDED',
    }
    
    return error_code_map.get(exc_class, 'UNKNOWN_ERROR')
