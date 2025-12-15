"""
Utility Functions for StockstarAuthVersionOne (Authentication & Email Services)
"""

import sib_api_v3_sdk
from sib_api_v3_sdk.rest import ApiException
from django.conf import settings
import logging

logger = logging.getLogger(__name__)


class BrevoEmailService:
    """
    Service class for sending emails using Brevo (formerly Sendinblue)
    for StockstarAuthVersionOne module
    """
    
    def __init__(self):
        """Initialize Brevo API configuration"""
        configuration = sib_api_v3_sdk.Configuration()
        configuration.api_key['api-key'] = settings.BREVO_API_KEY
        self.api_instance = sib_api_v3_sdk.TransactionalEmailsApi(
            sib_api_v3_sdk.ApiClient(configuration)
        )
    
    def send_otp_email(self, recipient_email, otp_code, user_name):
        """
        Send OTP verification email to user
        
        Args:
            recipient_email (str): Recipient's email address
            otp_code (str): OTP code to send
            user_name (str): User's first name
        
        Returns:
            bool: True if email sent successfully, False otherwise
        """
        
        subject = "Verify Your StockstarCapital Account"
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    line-height: 1.6;
                    color: #333;
                }}
                .container {{
                    max-width: 600px;
                    margin: 0 auto;
                    padding: 20px;
                    background-color: #f9f9f9;
                }}
                .header {{
                    background-color: #2c3e50;
                    color: white;
                    padding: 20px;
                    text-align: center;
                    border-radius: 5px 5px 0 0;
                }}
                .content {{
                    background-color: white;
                    padding: 30px;
                    border-radius: 0 0 5px 5px;
                }}
                .otp-box {{
                    background-color: #ecf0f1;
                    border: 2px dashed #3498db;
                    padding: 20px;
                    text-align: center;
                    font-size: 32px;
                    font-weight: bold;
                    letter-spacing: 8px;
                    color: #2c3e50;
                    margin: 20px 0;
                    border-radius: 5px;
                }}
                .warning {{
                    background-color: #fff3cd;
                    border-left: 4px solid #ffc107;
                    padding: 12px;
                    margin: 20px 0;
                }}
                .footer {{
                    text-align: center;
                    color: #7f8c8d;
                    font-size: 12px;
                    margin-top: 20px;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>StockstarCapital</h1>
                </div>
                <div class="content">
                    <h2>Hello {user_name},</h2>
                    <p>Thank you for registering with StockstarCapital!</p>
                    <p>To complete your registration, please verify your email address using the OTP code below:</p>
                    
                    <div class="otp-box">
                        {otp_code}
                    </div>
                    
                    <div class="warning">
                        <strong>⚠️ Important:</strong>
                        <ul style="margin: 5px 0;">
                            <li>This OTP is valid for {settings.OTP_EXPIRY_MINUTES} minutes</li>
                            <li>Do not share this code with anyone</li>
                            <li>If you didn't request this code, please ignore this email</li>
                        </ul>
                    </div>
                    
                    <p>If you have any questions, please contact our support team.</p>
                    
                    <p>Best regards,<br>
                    <strong>The StockstarCapital Team</strong></p>
                </div>
                <div class="footer">
                    <p>This is an automated email. Please do not reply to this message.</p>
                    <p>&copy; 2024 StockstarCapital. All rights reserved.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        send_smtp_email = sib_api_v3_sdk.SendSmtpEmail(
            to=[{"email": recipient_email, "name": user_name}],
            sender={
                "email": settings.BREVO_SENDER_EMAIL,
                "name": settings.BREVO_SENDER_NAME
            },
            subject=subject,
            html_content=html_content
        )
        
        try:
            api_response = self.api_instance.send_transac_email(send_smtp_email)
            logger.info(
                f"[StockstarAuthVersionOne] OTP email sent successfully to {recipient_email}. "
                f"Message ID: {api_response.message_id}"
            )
            return True
            
        except ApiException as e:
            logger.error(f"[StockstarAuthVersionOne] Failed to send OTP email to {recipient_email}: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"[StockstarAuthVersionOne] Unexpected error sending OTP email to {recipient_email}: {str(e)}")
            return False
    
    def send_welcome_email(self, recipient_email, user_name):
        """
        Send welcome email after successful verification
        
        Args:
            recipient_email (str): Recipient's email address
            user_name (str): User's first name
        
        Returns:
            bool: True if email sent successfully, False otherwise
        """
        
        subject = "Welcome to StockstarCapital!"
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    line-height: 1.6;
                    color: #333;
                }}
                .container {{
                    max-width: 600px;
                    margin: 0 auto;
                    padding: 20px;
                    background-color: #f9f9f9;
                }}
                .header {{
                    background-color: #27ae60;
                    color: white;
                    padding: 20px;
                    text-align: center;
                    border-radius: 5px 5px 0 0;
                }}
                .content {{
                    background-color: white;
                    padding: 30px;
                    border-radius: 0 0 5px 5px;
                }}
                .success-icon {{
                    text-align: center;
                    font-size: 60px;
                    margin: 20px 0;
                }}
                .footer {{
                    text-align: center;
                    color: #7f8c8d;
                    font-size: 12px;
                    margin-top: 20px;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>Welcome to StockstarCapital!</h1>
                </div>
                <div class="content">
                    <div class="success-icon">✓</div>
                    <h2>Congratulations, {user_name}!</h2>
                    <p>Your email has been successfully verified and your account is now active.</p>
                    <p>You can now access all features of StockstarCapital platform.</p>
                    <p>We're excited to have you on board!</p>
                    <p>Best regards,<br>
                    <strong>The StockstarCapital Team</strong></p>
                </div>
                <div class="footer">
                    <p>&copy; 2024 StockstarCapital. All rights reserved.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        send_smtp_email = sib_api_v3_sdk.SendSmtpEmail(
            to=[{"email": recipient_email, "name": user_name}],
            sender={
                "email": settings.BREVO_SENDER_EMAIL,
                "name": settings.BREVO_SENDER_NAME
            },
            subject=subject,
            html_content=html_content
        )
        
        try:
            api_response = self.api_instance.send_transac_email(send_smtp_email)
            logger.info(f"[StockstarAuthVersionOne] Welcome email sent to {recipient_email}. Message ID: {api_response.message_id}")
            return True
        except Exception as e:
            logger.error(f"[StockstarAuthVersionOne] Failed to send welcome email to {recipient_email}: {str(e)}")
            return False


def get_client_ip(request):
    """
    Get client IP address from request
    
    Args:
        request: Django request object
    
    Returns:
        str: Client IP address
    """
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def get_user_agent(request):
    """
    Get user agent from request
    
    Args:
        request: Django request object
    
    Returns:
        str: User agent string
    """
    return request.META.get('HTTP_USER_AGENT', '')
