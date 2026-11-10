import pytest


def _contact_payload() -> dict[str, str]:
    return {
        "email": "sender@example.com",
        "subject": "Question",
        "description": "Can you help?",
    }


@pytest.mark.asyncio
async def test_contact_uses_first_admin_native_language(client, admin_user):
    """Contact form forwards the first admin's native language to admin email i18n."""
    from unittest.mock import AsyncMock, patch

    admin, _ = admin_user
    admin.native_language = "es"

    with patch(
        "app.routers.contact.email_service.send_contact_email",
        new_callable=AsyncMock,
    ) as mock_send:
        response = await client.post(
            "/api/contact",
            json=_contact_payload(),
        )

    assert response.status_code == 204
    mock_send.assert_awaited_once()
    assert mock_send.call_args.kwargs["locale"] == "es"


@pytest.mark.asyncio
async def test_contact_returns_502_when_email_send_fails(client, admin_user):
    """Contact router converts email-service failures into a public 502."""
    from unittest.mock import AsyncMock, patch

    with patch(
        "app.routers.contact.email_service.send_contact_email",
        new_callable=AsyncMock,
    ) as mock_send:
        mock_send.side_effect = RuntimeError("SMTP unavailable")
        response = await client.post("/api/contact", json=_contact_payload())

    assert response.status_code == 502
    assert response.json()["detail"] == "Failed to send message. Please try again later."


@pytest.mark.asyncio
async def test_contact_returns_204_when_email_disabled(client, admin_user, monkeypatch):
    """Current behavior: disabled email makes contact submissions a no-op success."""
    from app.core.config import settings

    monkeypatch.setattr(settings, "EMAIL_ENABLED", False)

    response = await client.post("/api/contact", json=_contact_payload())

    assert response.status_code == 204


@pytest.mark.asyncio
async def test_contact_returns_204_when_contact_email_missing(client, admin_user, monkeypatch):
    """Current behavior: missing CONTACT_EMAIL drops the message without failing the request."""
    from unittest.mock import AsyncMock, patch

    from app.core.config import settings

    monkeypatch.setattr(settings, "EMAIL_ENABLED", True)
    monkeypatch.setattr(settings, "CONTACT_EMAIL", "")

    with patch("app.services.email_service.FastMail") as mock_fast_mail:
        mock_fast_mail.return_value.send_message = AsyncMock()
        response = await client.post("/api/contact", json=_contact_payload())

    assert response.status_code == 204
    mock_fast_mail.assert_not_called()
