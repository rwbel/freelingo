"""Email service — wraps fastapi-mail for transactional emails.

Reads configuration from settings. If EMAIL_ENABLED=false, all send_*
functions are no-ops so the app works without SMTP configured.
"""

from __future__ import annotations

from html import escape
from pathlib import Path

from fastapi_mail import ConnectionConfig, FastMail, MessageSchema, MessageType

from app.core.app_logger import get_logger
from app.core.config import settings

logger = get_logger(__name__)

_TEMPLATES_DIR = Path(__file__).parent.parent / "templates" / "email"


class _SafeHtml(str):
    """Trusted HTML controlled by the application, never by user input."""


def _safe_html(value: str) -> _SafeHtml:
    return _SafeHtml(value)


def _get_mail_config() -> ConnectionConfig:
    return ConnectionConfig(
        MAIL_USERNAME=settings.SMTP_USER,
        MAIL_PASSWORD=settings.SMTP_PASSWORD,
        MAIL_FROM=settings.SMTP_FROM,
        MAIL_PORT=settings.SMTP_PORT,
        MAIL_SERVER=settings.SMTP_HOST,
        MAIL_STARTTLS=settings.SMTP_TLS,
        MAIL_SSL_TLS=settings.SMTP_SSL,
        USE_CREDENTIALS=bool(settings.SMTP_USER),
        VALIDATE_CERTS=True,
    )


_VERIFY_I18N: dict[str, dict[str, str]] = {
    "es": {
        "greeting": "Hola {name},",
        "subject": "Verifica tu cuenta de FreeLingo",
        "body": "Gracias por crear tu cuenta de FreeLingo.<br />Por favor, verifica tu dirección de correo haciendo clic en el botón. Este enlace es válido durante <strong>24 horas</strong>.",
        "button": "Verificar mi cuenta",
        "link_fallback": "Si el botón no funciona, copia y pega este enlace en tu navegador:",
        "footer": "Si no creaste esta cuenta, puedes ignorar este correo.",
    },
    "ast": {
        "greeting": "Hola {name},",
        "subject": "Verifica la to cuenta de FreeLingo",
        "body": "Gracies por crear la to cuenta de FreeLingo.<br />Por favor, verifica la to direición de corréu faciendo clic en el botón. Esti enllaz ye válidu mientres <strong>24 hores</strong>.",
        "button": "Verificar la mio cuenta",
        "link_fallback": "Si el botón nun funciona, copia y pega esti enllaz nel to navegador:",
        "footer": "Si nun creesites esta cuenta, podes ignorar este corréu.",
    },
}

_RESET_I18N: dict[str, dict[str, str]] = {
    "es": {
        "greeting": "Hola {name},",
        "subject": "Restablece tu contraseña de FreeLingo",
        "body": "Hemos recibido una solicitud para restablecer la contraseña de tu cuenta FreeLingo.<br />Haz clic en el botón para crear una nueva. Este enlace es válido durante <strong>1 hora</strong>.",
        "button": "Restablecer contraseña",
        "link_fallback": "Si el botón no funciona, copia y pega este enlace en tu navegador:",
        "footer": "Si no solicitaste restablecer tu contraseña, puedes ignorar este correo.",
    },
    "ast": {
        "greeting": "Hola {name},",
        "subject": "Restablez la to contrasena de FreeLingo",
        "body": "Rebimos una soliciú pa restablecer la contrasena de la to cuenta FreeLingo.<br />Fai clic nel botón pa crear una nueva. Esti enllaz ye válidu mientres <strong>1 hora</strong>.",
        "button": "Restablecer contrasena",
        "link_fallback": "Si el botón nun funciona, copia y pega esti enllaz nel to navegador:",
        "footer": "Si nun solicitaches restablecer la to contrasena, podes ignorar este corréu.",
    },
}

_WELCOME_I18N: dict[str, dict[str, str]] = {
    "es": {
        "subject": "¡Bienvenido a FreeLingo!",
        "greeting": "Hola {name},",
        "body": "Tu cuenta está lista. Así puedes empezar:",
        "step1": "Haz la <strong>Evaluación</strong> — detecta tu nivel actual (A1–C2) y tus puntos fuertes y débiles.",
        "step2": "Genera tu <strong>Plan de estudio</strong> — un calendario semanal adaptado a tu nivel y objetivos.",
        "step3": "Completa tu primera lección diaria y empieza a construir tu racha.",
        "button": "Ir a mi panel",
        "footer": "¡Buena suerte con el aprendizaje!",
    },
    "ast": {
        "subject": "¡Bienveníu a FreeLingo!",
        "greeting": "Hola {name},",
        "body": "La to cuenta ta llista. Asina podes empezar:",
        "step1": "Fai la <strong>Evaluación</strong> — detecta to nivel actual (A1–C2) y los tos puntos fuertes y febles.",
        "step2": "Xenera to <strong>Plan d'estudiu</strong> — un calendariu selmanal adaptáu al to nivel y oxetivos.",
        "step3": "Completa to primer leición diaria y empieza a construyir to racha.",
        "button": "Ir al mio panél",
        "footer": "¡Bon aprendiza!",
    },
}

_ACCOUNT_DELETED_I18N: dict[str, dict[str, str]] = {
    "es": {
        "greeting": "Hola {name},",
        "subject": "Tu cuenta de FreeLingo ha sido eliminada",
        "body": "Tu cuenta de FreeLingo y todos tus datos asociados han sido eliminados permanentemente.",
        "footer": "Si no solicitaste esto, contacta con soporte inmediatamente.",
    },
    "ast": {
        "greeting": "Hola {name},",
        "subject": "La to cuenta de FreeLingo foi eliminada",
        "body": "La to cuenta de FreeLingo y tolos sos datos asociaos foron eliminaos permanentemente.",
        "footer": "Si nun solicitastes esto, contacta col sofitu inmediatamiente.",
    },
}

_CONTACT_I18N: dict[str, dict[str, str]] = {
    "es": {
        "greeting": "Hola {name},",
        "subject": "Nuevo mensaje de contacto - FreeLingo",
        "body": "Has recibido un nuevo mensaje de contacto:",
        "footer": "FreeLingo",
    },
    "ast": {
        "greeting": "Hola {name},",
        "subject": "Nuevu mensaxe de contactu - FreeLingo",
        "body": "Rebistes un nuevu mensaxe de contactu:",
        "footer": "FreeLingo",
    },
}

_FEEDBACK_I18N: dict[str, dict[str, str]] = {
    "es": {
        "greeting": "Hola {name},",
        "subject": "Nuevo feedback recibido - FreeLingo",
        "body": "Se ha recibido nuevo feedback:",
        "footer": "FreeLingo",
    },
    "ast": {
        "greeting": "Hola {name},",
        "subject": "Nuevu feedback rebíu - FreeLingo",
        "body": "Rebiose nuevu feedback:",
        "footer": "FreeLingo",
    },
}

_REVIEW_I18N: dict[str, dict[str, str]] = {
    "es": {
        "greeting": "Hola {name},",
        "subject": "Nueva reseña recibida - FreeLingo",
        "body": "Se ha recibido una nueva reseña:",
        "footer": "FreeLingo",
    },
    "ast": {
        "greeting": "Hola {name},",
        "subject": "Nova reseña rebidá - FreeLingo",
        "body": "Rebiose una nova reseña:",
        "footer": "FreeLingo",
    },
}


async def _send_email(
    to: str,
    subject: str,
    template_name: str,
    context: dict[str, str],
) -> None:
    """Render template and send email. No-op if EMAIL_ENABLED=false."""
    if not settings.EMAIL_ENABLED:
        return

    template_path = _TEMPLATES_DIR / template_name
    if not template_path.exists():
        logger.error("Email template not found", template=template_name)
        return

    template = template_path.read_text(encoding="utf-8")
    for key, value in context.items():
        template = template.replace(f"{{{{ {key} }}}}", value)

    message = MessageSchema(
        recipients=[to],
        subject=subject,
        body=template,
        subtype=MessageType.html,
    )

    fm = FastMail(_get_mail_config())
    await fm.send_message(message)


async def send_verification_email(
    email: str,
    name: str,
    token: str,
    locale: str = "es",
) -> None:
    catalog = _VERIFY_I18N.get(locale, _VERIFY_I18N["es"])
    verify_url = f"{settings.FRONTEND_URL}/verify-email?token={token}"
    await _send_email(
        to=email,
        subject=catalog["subject"],
        template_name="verify_email.html",
        context={
            "greeting": catalog["greeting"].format(name=name),
            "body": catalog["body"],
            "button": catalog["button"],
            "link_fallback": catalog["link_fallback"],
            "url": verify_url,
            "base_url": settings.FRONTEND_URL,
            "footer": catalog["footer"],
        },
    )


async def send_reset_password_email(
    email: str,
    name: str,
    token: str,
    locale: str = "es",
) -> None:
    catalog = _RESET_I18N.get(locale, _RESET_I18N["es"])
    reset_url = f"{settings.FRONTEND_URL}/reset-password?token={token}"
    await _send_email(
        to=email,
        subject=catalog["subject"],
        template_name="reset_password.html",
        context={
            "greeting": catalog["greeting"].format(name=name),
            "body": catalog["body"],
            "button": catalog["button"],
            "link_fallback": catalog["link_fallback"],
            "url": reset_url,
            "base_url": settings.FRONTEND_URL,
            "footer": catalog["footer"],
        },
    )


async def send_welcome_email(
    email: str,
    name: str,
    locale: str = "es",
) -> None:
    catalog = _WELCOME_I18N.get(locale, _WELCOME_I18N["es"])
    await _send_email(
        to=email,
        subject=catalog["subject"],
        template_name="welcome.html",
        context={
            "greeting": catalog["greeting"].format(name=name),
            "body": catalog["body"],
            "step1": catalog["step1"],
            "step2": catalog["step2"],
            "step3": catalog["step3"],
            "button": catalog["button"],
            "url": f"{settings.FRONTEND_URL}/dashboard",
            "base_url": settings.FRONTEND_URL,
            "footer": catalog["footer"],
        },
    )


async def send_account_deleted_email(
    email: str,
    name: str,
    locale: str = "es",
) -> None:
    catalog = _ACCOUNT_DELETED_I18N.get(locale, _ACCOUNT_DELETED_I18N["es"])
    await _send_email(
        to=email,
        subject=catalog["subject"],
        template_name="account_deleted.html",
        context={
            "greeting": catalog["greeting"].format(name=name),
            "body": catalog["body"],
            "base_url": settings.FRONTEND_URL,
            "footer": catalog["footer"],
        },
    )


async def send_contact_email(
    admin_email: str,
    admin_name: str,
    user_email: str,
    user_name: str,
    subject: str,
    description: str,
    locale: str = "es",
) -> None:
    catalog = _CONTACT_I18N.get(locale, _CONTACT_I18N["es"])
    await _send_email(
        to=admin_email,
        subject=catalog["subject"],
        template_name="contact_admin.html",
        context={
            "greeting": catalog["greeting"].format(name=admin_name),
            "body": catalog["body"],
            "user_email": user_email,
            "user_name": user_name,
            "subject": subject,
            "description": description,
            "base_url": settings.FRONTEND_URL,
            "footer": catalog["footer"],
        },
    )


async def send_feedback_notification(
    admin_email: str,
    admin_name: str,
    category: str,
    title: str,
    description: str,
    user_display_name: str,
    user_id: int,
    locale: str = "es",
) -> None:
    catalog = _FEEDBACK_I18N.get(locale, _FEEDBACK_I18N["es"])
    await _send_email(
        to=admin_email,
        subject=catalog["subject"],
        template_name="feedback_notification.html",
        context={
            "greeting": catalog["greeting"].format(name=admin_name),
            "body": catalog["body"],
            "category": category,
            "title": title,
            "description": description,
            "user_display_name": user_display_name,
            "user_id": user_id,
            "base_url": settings.FRONTEND_URL,
            "footer": catalog["footer"],
        },
    )


async def send_review_notification(
    admin_email: str,
    admin_name: str,
    user_display_name: str,
    rating: int,
    target_language: str,
    review_id: int,
    locale: str = "es",
) -> None:
    catalog = _REVIEW_I18N.get(locale, _REVIEW_I18N["es"])
    await _send_email(
        to=admin_email,
        subject=catalog["subject"],
        template_name="review_notification.html",
        context={
            "greeting": catalog["greeting"].format(name=admin_name),
            "body": catalog["body"],
            "user_display_name": user_display_name,
            "rating": str(rating),
            "target_language": target_language,
            "review_id": str(review_id),
            "base_url": settings.FRONTEND_URL,
            "footer": catalog["footer"],
        },
    )
