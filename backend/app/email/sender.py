import smtplib
import json
import threading
import logging
import urllib.request
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from app.config import (
    SMTP_HOST, SMTP_PORT, SMTP_USE_SSL, SMTP_USER, SMTP_PASSWORD,
    SENDGRID_API_KEY, FROM_EMAIL,
)

logger = logging.getLogger(__name__)


def _build_html(code: str, name: str) -> str:
    return f"""
    <div style="font-family: Arial, sans-serif; max-width: 480px; margin: 0 auto;">
        <h2 style="color: #6366f1;">Mimetic AI</h2>
        <p>Hola <strong>{name}</strong>,</p>
        <p>Tu código de verificación es:</p>
        <div style="text-align: center; margin: 24px 0;">
            <span style="font-size: 32px; font-weight: 700; letter-spacing: 8px;
                background: #1e293b; color: #a5b4fc; padding: 12px 24px;
                border-radius: 8px;">{code}</span>
        </div>
        <p>Este código expira en 10 minutos.</p>
        <p style="color: #64748b; font-size: 12px;">Si no solicitaste este código, ignora este mensaje.</p>
    </div>
    """


def _send_smtp(to_email: str, html: str):
    msg = MIMEMultipart()
    msg["From"] = FROM_EMAIL
    msg["To"] = to_email
    msg["Subject"] = "Código de verificación - Mimetic AI"
    msg.attach(MIMEText(html, "html"))

    if SMTP_USE_SSL:
        with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT, timeout=15) as server:
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.send_message(msg)
    else:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=15) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.send_message(msg)
    logger.info(f"Email sent via SMTP to {to_email}")


def _send_sendgrid(to_email: str, html: str):
    data = json.dumps({
        "personalizations": [{"to": [{"email": to_email}]}],
        "from": {"email": "mimeticvalidated@gmail.com", "name": "Mimetic AI"},
        "subject": "Código de verificación - Mimetic AI",
        "content": [{"type": "text/html", "value": html}],
    }).encode()
    req = urllib.request.Request(
        "https://api.sendgrid.com/v3/mail/send",
        data=data,
        headers={
            "Authorization": f"Bearer {SENDGRID_API_KEY}",
            "Content-Type": "application/json",
        },
    )
    urllib.request.urlopen(req, timeout=15)
    logger.info(f"Email sent via SendGrid to {to_email}")


def _send(to_email: str, code: str, name: str):
    html = _build_html(code, name)

    if SENDGRID_API_KEY:
        try:
            _send_sendgrid(to_email, html)
            return
        except Exception as e:
            logger.error(f"SendGrid failed for {to_email}: {e}")

    if SMTP_USER and SMTP_PASSWORD:
        try:
            _send_smtp(to_email, html)
            return
        except Exception as e:
            logger.error(f"SMTP failed for {to_email}: {e}")

    logger.warning(f"No email provider configured, unable to send to {to_email}")


def send_verification_code(to_email: str, code: str, name: str):
    threading.Thread(target=_send, args=(to_email, code, name), daemon=True).start()
