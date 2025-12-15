"""
Ray Tasks for Distributed Email Processing
"""

import logging
import ray
from django.conf import settings

logger = logging.getLogger(__name__)

# =====================================================
# Ray Initialization
# =====================================================

def initialize_ray():
    """
    Initialize Ray in local CPU-only mode
    """
    if not ray.is_initialized():
        try:
            ray.init(local_mode=True, include_dashboard=False)
            logger.info("Ray initialized successfully")
        except Exception as e:
            logger.error(f"Ray initialization failed: {e}")


# =====================================================
# OTP & Welcome Emails (Using BrevoEmailService)
# =====================================================

@ray.remote(num_cpus=1)
def send_otp_email_task(recipient_email, otp_code, user_name):
    from stockstarauthversionone.utils import BrevoEmailService

    try:
        email_service = BrevoEmailService()
        success = email_service.send_otp_email(
            recipient_email, otp_code, user_name
        )

        return {
            "success": success,
            "recipient": recipient_email,
            "message": "OTP email sent" if success else "OTP email failed",
        }

    except Exception as e:
        logger.error(f"OTP email Ray task error: {e}")
        return {"success": False, "error": str(e)}


@ray.remote(num_cpus=1)
def send_welcome_email_task(recipient_email, user_name):
    from stockstarauthversionone.utils import BrevoEmailService

    try:
        email_service = BrevoEmailService()
        success = email_service.send_welcome_email(
            recipient_email, user_name
        )

        return {
            "success": success,
            "recipient": recipient_email,
            "message": "Welcome email sent" if success else "Welcome email failed",
        }

    except Exception as e:
        logger.error(f"Welcome email Ray task error: {e}")
        return {"success": False, "error": str(e)}


def send_otp_email_async(recipient_email, otp_code, user_name) -> bool:
    """
    Fire-and-forget OTP email
    """
    try:
        if ray.is_initialized():
            send_otp_email_task.remote(recipient_email, otp_code, user_name)
            return True

        from stockstarauthversionone.utils import BrevoEmailService
        return BrevoEmailService().send_otp_email(
            recipient_email, otp_code, user_name
        )

    except Exception as e:
        logger.error(f"OTP async error: {e}")
        return False


def send_welcome_email_async(recipient_email, user_name) -> bool:
    """
    Fire-and-forget welcome email
    """
    try:
        if ray.is_initialized():
            send_welcome_email_task.remote(recipient_email, user_name)
            return True

        from stockstarauthversionone.utils import BrevoEmailService
        return BrevoEmailService().send_welcome_email(
            recipient_email, user_name
        )

    except Exception as e:
        logger.error(f"Welcome async error: {e}")
        return False


# =====================================================
# Password Reset OTP Email (Brevo SDK)
# =====================================================

def send_password_reset_otp_email(
    recipient_email: str, otp_code: str, user_name: str
) -> bool:
    """
    Send password reset OTP email synchronously
    """
    try:
        import sib_api_v3_sdk
        from sib_api_v3_sdk.rest import ApiException

        configuration = sib_api_v3_sdk.Configuration()
        configuration.api_key["api-key"] = settings.BREVO_API_KEY

        api_client = sib_api_v3_sdk.ApiClient(configuration)
        api_instance = sib_api_v3_sdk.TransactionalEmailsApi(api_client)

        html_content = f"""
        <h2>Password Reset OTP</h2>
        <p>Hi {user_name},</p>
        <p>Your OTP is:</p>
        <h1>{otp_code}</h1>
        <p>This OTP expires in {settings.OTP_EXPIRY_MINUTES} minutes.</p>
        <p>If you did not request this, please ignore this email.</p>
        """

        email = sib_api_v3_sdk.SendSmtpEmail(
            to=[{"email": recipient_email}],
            sender={
                "name": settings.BREVO_SENDER_NAME,
                "email": settings.BREVO_SENDER_EMAIL,
            },
            subject="🔒 Password Reset OTP - StockstarCapital",
            html_content=html_content,
        )

        api_instance.send_transac_email(email)
        logger.info(f"Password reset OTP sent to {recipient_email}")
        return True

    except ApiException as e:
        logger.error(f"Brevo API error: {e}")
        return False

    except Exception as e:
        logger.error(f"Password reset OTP error: {e}")
        return False


# =====================================================
# Ray Wrapper (Async)
# =====================================================

@ray.remote(num_cpus=1)
def send_password_reset_otp_email_ray(
    recipient_email: str, otp_code: str, user_name: str
) -> bool:
    return send_password_reset_otp_email(
        recipient_email, otp_code, user_name
    )


def send_password_reset_otp_email_async(
    recipient_email: str, otp_code: str, user_name: str
) -> bool:
    """
    Async fire-and-forget password reset OTP
    """
    try:
        if ray.is_initialized():
            send_password_reset_otp_email_ray.remote(
                recipient_email, otp_code, user_name
            )
            return True

        return send_password_reset_otp_email(
            recipient_email, otp_code, user_name
        )

    except Exception as e:
        logger.error(f"Password reset OTP async error: {e}")
        return False
