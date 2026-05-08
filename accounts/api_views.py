"""
API views for user registration and authentication.

Provides REST endpoints for user onboarding and token management.
"""

import logging
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.authtoken.models import Token

logger = logging.getLogger(__name__)

User = get_user_model()


@api_view(['POST'])
@permission_classes([AllowAny])
def register_user(request):
    """
    Register a new user account.
    
    Creates user, sends verification email via SES, and returns auth token.
    
    Request body:
    {
        "username": "string",
        "email": "string",
        "password": "string",
        "first_name": "string" (optional),
        "last_name": "string" (optional)
    }
    
    Response:
    {
        "user": {
            "id": int,
            "username": "string",
            "email": "string",
            "first_name": "string",
            "last_name": "string"
        },
        "token": "string"
    }
    """
    logger.info('API: register_user called')
    
    # Extract data
    username = request.data.get('username', '').strip()
    email = request.data.get('email', '').strip()
    password = request.data.get('password', '')
    first_name = request.data.get('first_name', '').strip()
    last_name = request.data.get('last_name', '').strip()
    
    # Validate required fields
    if not username:
        return Response(
            {'error': 'username is required', 'code': 'VALIDATION_ERROR'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    if not email:
        return Response(
            {'error': 'email is required', 'code': 'VALIDATION_ERROR'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    if not password:
        return Response(
            {'error': 'password is required', 'code': 'VALIDATION_ERROR'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Check if username already exists
    if User.objects.filter(username=username).exists():
        return Response(
            {'error': f'Username "{username}" is already taken', 'code': 'USERNAME_EXISTS'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Check if email already exists
    if User.objects.filter(email=email).exists():
        return Response(
            {'error': f'Email "{email}" is already registered', 'code': 'EMAIL_EXISTS'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Validate password strength
    try:
        validate_password(password)
    except ValidationError as e:
        return Response(
            {'error': '; '.join(e.messages), 'code': 'WEAK_PASSWORD'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Create user
    try:
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name
        )
        
        logger.info(f'API: Created user id={user.id}, username={username}')
        
        # Create auth token
        token, created = Token.objects.get_or_create(user=user)
        
        # Send welcome email via SES
        from accounts.services.email_service import EmailService
        try:
            EmailService.send_welcome_email(user)
            logger.info(f'API: Sent welcome email to {email}')
        except Exception as e:
            # Log but don't fail registration if email fails
            logger.error(f'API: Failed to send welcome email to {email}: {e}')
        
        return Response({
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name
            },
            'token': token.key
        }, status=status.HTTP_201_CREATED)
        
    except Exception as e:
        logger.error(f'API: Failed to create user: {e}')
        return Response(
            {'error': 'Failed to create user account', 'code': 'INTERNAL_ERROR'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
def refresh_token(request):
    """
    Refresh user's auth token.
    
    Deletes old token and creates new one.
    Requires authentication.
    
    Response:
    {
        "token": "string"
    }
    """
    logger.info(f'API: refresh_token called by user={request.user.id}')
    
    # Delete old token
    Token.objects.filter(user=request.user).delete()
    
    # Create new token
    token = Token.objects.create(user=request.user)
    
    logger.info(f'API: Refreshed token for user={request.user.id}')
    
    return Response({
        'token': token.key
    })


@api_view(['POST'])
def revoke_token(request):
    """
    Revoke user's auth token (logout).
    
    Deletes the auth token.
    Requires authentication.
    
    Response:
    {
        "revoked": true
    }
    """
    logger.info(f'API: revoke_token called by user={request.user.id}')
    
    # Delete token
    Token.objects.filter(user=request.user).delete()
    
    logger.info(f'API: Revoked token for user={request.user.id}')
    
    return Response({
        'revoked': True
    })
