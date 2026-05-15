"""
Email service using AWS SES.

Sends transactional emails for user registration, password reset, etc.
"""

import logging
import os
from django.conf import settings

logger = logging.getLogger(__name__)


class EmailService:
    """
    Service for sending emails via AWS SES.
    
    Uses boto3 to send emails through Amazon Simple Email Service.
    Requires AWS credentials and verified domain in SES.
    """
    
    @staticmethod
    def _get_ses_client():
        """
        Get boto3 SES client.
        
        :return: boto3 SES client or None if not configured
        """
        try:
            import boto3
            
            # Use environment variables for AWS credentials
            # AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_DEFAULT_REGION
            return boto3.client('ses')
        except Exception as e:
            logger.warning(f'Failed to create SES client: {e}')
            return None
    
    @staticmethod
    def send_welcome_email(user):
        """
        Send welcome email to new user.
        
        :param user: User instance
        :raises Exception: If email fails to send
        """
        ses_client = EmailService._get_ses_client()
        
        if not ses_client:
            logger.warning('SES not configured, skipping welcome email')
            return
        
        # Get sender email from settings
        sender = getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@featurefactory.io')
        
        # Email content
        subject = 'Welcome to Mimir!'
        body_text = f"""
Hello {user.first_name or user.username},

Welcome to Mimir! Your account has been successfully created.

You can now start creating playbooks and workflows to organize your development processes.

Username: {user.username}
Email: {user.email}

If you have any questions, please don't hesitate to reach out.

Best regards,
The Mimir Team
"""
        
        body_html = f"""
<html>
<head></head>
<body>
  <h1>Welcome to Mimir!</h1>
  <p>Hello {user.first_name or user.username},</p>
  <p>Your account has been successfully created.</p>
  <p>You can now start creating playbooks and workflows to organize your development processes.</p>
  <p><strong>Account Details:</strong></p>
  <ul>
    <li>Username: {user.username}</li>
    <li>Email: {user.email}</li>
  </ul>
  <p>If you have any questions, please don't hesitate to reach out.</p>
  <p>Best regards,<br>The Mimir Team</p>
</body>
</html>
"""
        
        try:
            response = ses_client.send_email(
                Source=sender,
                Destination={'ToAddresses': [user.email]},
                Message={
                    'Subject': {'Data': subject, 'Charset': 'UTF-8'},
                    'Body': {
                        'Text': {'Data': body_text, 'Charset': 'UTF-8'},
                        'Html': {'Data': body_html, 'Charset': 'UTF-8'}
                    }
                }
            )
            
            logger.info(f'Sent welcome email to {user.email}, MessageId: {response["MessageId"]}')
            
        except Exception as e:
            logger.error(f'Failed to send welcome email to {user.email}: {e}')
            raise
    
    @staticmethod
    def send_password_reset_email(user, reset_token):
        """
        Send password reset email.
        
        :param user: User instance
        :param reset_token: Password reset token
        :raises Exception: If email fails to send
        """
        ses_client = EmailService._get_ses_client()
        
        if not ses_client:
            logger.warning('SES not configured, skipping password reset email')
            return
        
        sender = getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@featurefactory.io')
        
        # Get base URL from settings
        base_url = getattr(settings, 'FRONTEND_URL', 'https://mimir.featurefactory.io')
        reset_url = f'{base_url}/reset-password?token={reset_token}'
        
        subject = 'Password Reset Request'
        body_text = f"""
Hello {user.first_name or user.username},

You requested a password reset for your Mimir account.

Click the link below to reset your password:
{reset_url}

This link will expire in 24 hours.

If you didn't request this, please ignore this email.

Best regards,
The Mimir Team
"""
        
        body_html = f"""
<html>
<head></head>
<body>
  <h1>Password Reset Request</h1>
  <p>Hello {user.first_name or user.username},</p>
  <p>You requested a password reset for your Mimir account.</p>
  <p><a href="{reset_url}">Click here to reset your password</a></p>
  <p>This link will expire in 24 hours.</p>
  <p>If you didn't request this, please ignore this email.</p>
  <p>Best regards,<br>The Mimir Team</p>
</body>
</html>
"""
        
        try:
            response = ses_client.send_email(
                Source=sender,
                Destination={'ToAddresses': [user.email]},
                Message={
                    'Subject': {'Data': subject, 'Charset': 'UTF-8'},
                    'Body': {
                        'Text': {'Data': body_text, 'Charset': 'UTF-8'},
                        'Html': {'Data': body_html, 'Charset': 'UTF-8'}
                    }
                }
            )
            
            logger.info(f'Sent password reset email to {user.email}, MessageId: {response["MessageId"]}')
            
        except Exception as e:
            logger.error(f'Failed to send password reset email to {user.email}: {e}')
            raise
