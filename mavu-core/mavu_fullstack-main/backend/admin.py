"""SQLAdmin interface for MavuAI."""
from sqladmin import Admin, ModelView
from sqladmin.authentication import AuthenticationBackend
from sqlalchemy import select
from starlette.requests import Request
from markupsafe import Markup
import html as html_lib
import json
import structlog

from utils.password import verify_password
from config import settings
from dependencies.database import engine
from models import Chat, FCMDevice, PromoCode, Threat, User, Session, EmailVerification, PaymeTransaction

logger = structlog.get_logger()


class UserAdmin(ModelView, model=User):
    """Admin interface for User model"""
    name = "User"
    name_plural = "Users"
    icon = "fa-solid fa-users"

    column_list = [
        User.id,
        User.telegram_id,
        User.email,
        User.username,
        User.name,
        User.is_active,
        User.is_verified,
        User.is_admin,
        User.created_at,
    ]

    column_searchable_list = [User.email, User.username, User.name]
    column_sortable_list = [User.id, User.email, User.username, User.created_at]
    column_default_sort = ("created_at", True)

    form_excluded_columns = ["password_hash", "created_at", "updated_at", "chats", "threats", "promo_codes", "sessions", "fcm_devices", "email_verifications"]

    page_size = 20
    can_create = True
    can_edit = True
    can_delete = True
    can_view_details = True


class SessionAdmin(ModelView, model=Session):
    """Admin interface for Session model"""
    name = "Session"
    name_plural = "Sessions"
    icon = "fa-solid fa-clock"

    column_list = [
        Session.id,
        Session.user_id,
        Session.session_token,
        Session.is_active,
        Session.expires_at,
        Session.ip_address,
        Session.created_at,
    ]

    column_searchable_list = [
        Session.session_token,
        Session.ip_address,
        Session.user_agent
    ]
    column_sortable_list = [
        Session.id,
        Session.user_id,
        Session.is_active,
        Session.expires_at,
        Session.created_at
    ]
    column_default_sort = ("created_at", True)

    form_excluded_columns = ["created_at", "updated_at", "user"]

    page_size = 20
    can_create = True
    can_edit = True
    can_delete = True
    can_view_details = True


class ChatAdmin(ModelView, model=Chat):
    """Admin interface for Chat model"""
    name = "Chat"
    name_plural = "Chats"
    icon = "fa-solid fa-comments"

    column_list = [
        Chat.id,
        Chat.user_id,
        Chat.message,
        Chat.processed,
        Chat.created_at,
    ]

    column_details_list = [
        Chat.id,
        Chat.user_id,
        Chat.message,
        Chat.response,
        Chat.context,
        Chat.processed,
        Chat.created_at,
        Chat.updated_at,
    ]

    column_searchable_list = [Chat.message, Chat.response]
    column_sortable_list = [Chat.id, Chat.user_id, Chat.created_at]
    column_default_sort = ("created_at", True)

    form_excluded_columns = ["created_at", "updated_at", "user"]

    # Custom formatters for detail view to display with proper height and line breaks
    column_formatters_detail = {
        "context": lambda model, attr: ChatAdmin._format_context_detail(model.context if hasattr(model, 'context') else None),
        "response": lambda model, attr: ChatAdmin._format_text_detail(model.response if hasattr(model, 'response') else None),
        "message": lambda model, attr: ChatAdmin._format_text_detail(model.message if hasattr(model, 'message') else None),
    }

    page_size = 20
    can_create = True
    can_edit = True
    can_delete = True
    can_view_details = True

    @staticmethod
    def _format_context_detail(context):
        """Format context JSON to display prompt with proper height and line breaks"""
        if not context:
            return Markup('<span style="color: #666;">No context</span>')

        # If context has a 'prompt' key, extract and format it
        if isinstance(context, dict) and 'prompt' in context:
            prompt_text = context['prompt']
            # Escape HTML characters then replace newlines with <br>
            escaped = html_lib.escape(prompt_text)
            # Replace \n with actual <br> tags
            formatted = escaped.replace('\\n', '<br>').replace('\n', '<br>')
            return Markup(
                f'<div style="background: #2b2b2b; color: #f8f8f2; padding: 15px; '
                f'border-radius: 5px; font-family: \'Courier New\', monospace; '
                f'font-size: 13px; line-height: 1.8; min-height: 300px; max-height: 800px; '
                f'overflow-y: auto; overflow-x: auto; white-space: normal; word-wrap: break-word;">'
                f'{formatted}</div>'
            )

        # Otherwise, just display the raw JSON
        json_str = json.dumps(context, indent=2, ensure_ascii=False)
        escaped = html_lib.escape(json_str)
        formatted_json = escaped.replace('\\n', '<br>').replace('\n', '<br>')
        return Markup(
            f'<div style="background: #f5f5f5; color: #333; padding: 15px; '
            f'border-radius: 5px; font-family: monospace; font-size: 12px; '
            f'min-height: 200px; max-height: 600px; overflow-y: auto; overflow-x: auto; '
            f'white-space: normal;">{formatted_json}</div>'
        )

    @staticmethod
    def _format_text_detail(text):
        """Format text fields with proper height and line breaks"""
        if not text:
            return Markup('<span style="color: #666;">No text</span>')
        # Escape HTML and replace newlines with <br>
        escaped = html_lib.escape(text)
        # Replace both \n and literal newlines
        formatted = escaped.replace('\\n', '<br>').replace('\n', '<br>')
        return Markup(
            f'<div style="background: #f9f9f9; color: #333; padding: 12px; '
            f'border-radius: 4px; border: 1px solid #ddd; min-height: 100px; '
            f'max-height: 400px; overflow-y: auto; white-space: normal; '
            f'word-wrap: break-word; font-family: Arial, sans-serif; '
            f'font-size: 14px; line-height: 1.6;">{formatted}</div>'
        )


class EmailVerificationAdmin(ModelView, model=EmailVerification):
    """Admin interface for EmailVerification model"""
    name = "Email Verification"
    name_plural = "Email Verifications"
    icon = "fa-solid fa-envelope-circle-check"

    column_list = [
        EmailVerification.id,
        EmailVerification.user_id,
        EmailVerification.email,
        EmailVerification.is_verified,
        EmailVerification.expires_at,
        EmailVerification.verified_at,
        EmailVerification.created_at,
    ]

    column_searchable_list = [EmailVerification.email, EmailVerification.token]
    column_sortable_list = [EmailVerification.id, EmailVerification.user_id, EmailVerification.created_at]
    column_default_sort = ("created_at", True)

    form_excluded_columns = ["created_at", "updated_at", "user"]

    page_size = 20
    can_create = True
    can_edit = True
    can_delete = True
    can_view_details = True


class FCMDeviceAdmin(ModelView, model=FCMDevice):
    """Admin interface for FCM Device model"""
    name = "FCM Device"
    name_plural = "FCM Devices"
    icon = "fa-solid fa-mobile"

    column_list = [
        FCMDevice.id,
        FCMDevice.user_id,
        FCMDevice.device_id,
        FCMDevice.device_type,
        FCMDevice.language,
        FCMDevice.created_at,
    ]

    column_searchable_list = [FCMDevice.device_id, FCMDevice.registration_id]
    column_sortable_list = [FCMDevice.id, FCMDevice.user_id, FCMDevice.device_type, FCMDevice.created_at]
    column_default_sort = ("created_at", True)

    form_excluded_columns = ["created_at", "updated_at", "user"]

    page_size = 20
    can_create = True
    can_edit = True
    can_delete = True
    can_view_details = True


class ThreatAdmin(ModelView, model=Threat):
    """Admin interface for Threat model"""
    name = "Threat"
    name_plural = "Threats"
    icon = "fa-solid fa-bug"

    column_list = [
        Threat.id,
        Threat.user_id,
        Threat.threat_type,
        Threat.severity,
        Threat.description,
        Threat.detected_at,
        Threat.resolved,
    ]

    column_details_list = [
        Threat.id,
        Threat.user_id,
        Threat.threat_type,
        Threat.severity,
        Threat.description,
        Threat.evidence,
        Threat.detected_at,
        Threat.resolved,
        Threat.resolved_at,
        Threat.resolved_by,
        Threat.notes,
        Threat.created_at,
        Threat.updated_at,
    ]

    column_searchable_list = [Threat.threat_type, Threat.description]
    column_sortable_list = [Threat.id, Threat.user_id, Threat.detected_at, Threat.severity]
    column_default_sort = ("created_at", True)

    form_excluded_columns = ["created_at", "updated_at", "user"]

    # Custom formatters for detail view to display with proper height and line breaks
    column_formatters_detail = {
        "description": lambda model, attr: ThreatAdmin._format_threat_text(model.description if hasattr(model, 'description') else None),
    }

    page_size = 20
    can_create = True
    can_edit = True
    can_delete = True
    can_view_details = True

    @staticmethod
    def _format_threat_text(text):
        """Format threat text fields with proper height and line breaks"""
        if not text:
            return Markup('<span style="color: #666;">No text</span>')
        # Escape HTML and replace newlines with <br>
        escaped = html_lib.escape(text)
        # Replace both \n and literal newlines
        formatted = escaped.replace('\\n', '<br>').replace('\n', '<br>')
        return Markup(
            f'<div style="background: #fff3cd; color: #856404; padding: 12px; '
            f'border-radius: 4px; border: 1px solid #ffc107; min-height: 100px; '
            f'max-height: 400px; overflow-y: auto; white-space: normal; '
            f'word-wrap: break-word; font-family: Arial, sans-serif; '
            f'font-size: 14px; line-height: 1.6;">{formatted}</div>'
        )


class PromoCodeAdmin(ModelView, model=PromoCode):
    """Admin interface for PromoCode model"""
    name = "Promo Code"
    name_plural = "Promo Codes"
    icon = "fa-solid fa-ticket"

    column_list = [
        PromoCode.id,
        PromoCode.code,
        PromoCode.is_active,
        PromoCode.user_id,
        PromoCode.activated_at,
        PromoCode.created_at,
    ]

    column_searchable_list = [PromoCode.code]
    column_sortable_list = [PromoCode.id, PromoCode.code, PromoCode.created_at]
    column_default_sort = ("created_at", True)

    form_excluded_columns = ["created_at", "updated_at", "user"]

    page_size = 20
    can_create = True
    can_edit = True
    can_delete = True
    can_view_details = True


class PaymeTransactionAdmin(ModelView, model=PaymeTransaction):
    """Admin interface for PaymeTransaction model"""
    name = "Payme Transaction"
    name_plural = "Payme Transactions"
    icon = "fa-solid fa-credit-card"

    column_list = [
        PaymeTransaction.id,
        PaymeTransaction.transaction_id,
        PaymeTransaction.user_id,
        PaymeTransaction.promo_code_id,
        PaymeTransaction.amount,
        PaymeTransaction.status,
        PaymeTransaction.perform_time,
        PaymeTransaction.created_at,
    ]

    column_searchable_list = [PaymeTransaction.transaction_id]
    column_sortable_list = [PaymeTransaction.id, PaymeTransaction.transaction_id, PaymeTransaction.created_at]
    column_default_sort = ("created_at", True)

    form_excluded_columns = ["created_at", "updated_at", "user", "promo_code"]

    page_size = 20
    can_create = True
    can_edit = True
    can_delete = True
    can_view_details = True


class MyAuthBackend(AuthenticationBackend):
    """
    Custom authentication backend for SQLAdmin using session-based authentication.
    """

    async def login(self, request: Request) -> bool:
        """Perform login"""
        form = await request.form()
        username = form.get("username")
        password = form.get("password")

        if not username or not password:
            return False

        from dependencies.database import SessionLocal

        db = SessionLocal()
        try:
            # Query for user by email or username
            user = db.query(User).filter(
                (User.email == username) | (User.username == username)
            ).first()

            if not user:
                logger.warning("Login attempt with unknown username", username=username)
                return False

            # Check if user is active and is admin
            if not user.is_active or not user.is_admin:
                logger.warning("Login attempt by non-admin user", username=username)
                return False

            # Check if user has a password
            if not user.password_hash:
                logger.warning("Login attempt for user without password", username=username)
                return False

            # Verify password
            if verify_password(password, user.password_hash):
                # Store user ID in session
                request.session.update({
                    "user_id": str(user.id),
                    "user_email": user.email,
                    "is_admin": True
                })
                logger.info("Admin login successful", username=username, user_id=user.id)
                return True

            logger.warning("Login attempt with invalid password", username=username)
            return False

        except Exception as e:
            logger.error("Login error", error=str(e))
            return False
        finally:
            db.close()

    async def logout(self, request: Request) -> bool:
        """Perform logout"""
        request.session.clear()
        logger.info("Admin logout")
        return True

    async def authenticate(self, request: Request) -> bool:
        """Check if authenticated"""
        user_id = request.session.get("user_id")
        is_admin = request.session.get("is_admin", False)
        return bool(user_id and is_admin)


def create_admin(app):
    """
    Create and configure admin instance.
    Must be called BEFORE middleware is added to the app.
    """
    # Create admin with authentication
    authentication_backend = MyAuthBackend(secret_key=settings.secret_key)

    admin = Admin(
        app,
        engine,
        title="MavuAI Admin",
        base_url="/admin",
        authentication_backend=authentication_backend
    )

    # Add all model views
    admin.add_view(UserAdmin)
    admin.add_view(SessionAdmin)
    admin.add_view(ChatAdmin)
    admin.add_view(EmailVerificationAdmin)
    admin.add_view(FCMDeviceAdmin)
    admin.add_view(ThreatAdmin)
    admin.add_view(PromoCodeAdmin)
    admin.add_view(PaymeTransactionAdmin)

    logger.info("SQLAdmin interface configured", base_url="/admin")

    return admin
