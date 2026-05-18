import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from app.config import SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASSWORD, FROM_EMAIL


def send_verification_code(to_email: str, code: str, name: str):
    msg = MIMEMultipart()
    msg["From"] = FROM_EMAIL
    msg["To"] = to_email
    msg["Subject"] = "Código de verificación - Mimetic AI"

    html = f"""
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
    msg.attach(MIMEText(html, "html"))

    with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
        server.starttls()
        server.login(SMTP_USER, SMTP_PASSWORD)
        server.send_message(msg)
