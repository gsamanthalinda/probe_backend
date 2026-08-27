import os
import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from pathlib import Path
from dotenv import load_dotenv
from fastapi import HTTPException, status

logger = logging.getLogger(__name__)

project_root = Path(__file__).resolve().parent.parent.parent
load_dotenv(dotenv_path=project_root / ".env")

SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", 587))
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
EMAIL_FROM = os.getenv("EMAIL_FROM", "probe@example.com")
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")


def _get_smtp_server():
    if not all([SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASSWORD]):
        raise RuntimeError("SMTP is not configured. Set SMTP_HOST, SMTP_PORT, SMTP_USER, and SMTP_PASSWORD in .env")
    server = smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=10)
    server.starttls()
    server.login(SMTP_USER, SMTP_PASSWORD)
    return server


def _send_email(msg):
    try:
        with _get_smtp_server() as server:
            server.sendmail(EMAIL_FROM, msg['To'], msg.as_string())
    except Exception as e:
        logger.error(f"SMTP error: {type(e).__name__}: {e}")
        logger.warning("Falling back to console output for email")
        print("\n" + "="*60)
        print("EMAIL (SMTP FAILED - Console Fallback)")
        print("="*60)
        print(f"From: {msg['From']}")
        print(f"To: {msg['To']}")
        print(f"Subject: {msg['Subject']}")
        print("-"*60)
        for part in msg.walk():
            if part.get_content_type() == "text/plain":
                print(part.get_payload(decode=True).decode('utf-8', errors='replace'))
            elif part.get_content_type() == "text/html":
                print("[HTML content]")
        print("="*60 + "\n")


def send_password_reset_email(to_email: str, reset_token: str):
    if not to_email or "@" not in to_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid email address."
        )

    if not reset_token or len(reset_token) < 32:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid reset token."
        )

    reset_link = f"{FRONTEND_URL}/reset-password?token={reset_token}"

    subject = "HERckers - Password Reset Request"
    html_body = f"""
    <html>
    <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
        <h2 style="color: #2c3e50;">Password Reset Request</h2>
        <p>You requested to reset your password for your HERckers account.</p>
        <p>Click the link below to reset your password:</p>
        <p style="margin: 20px 0;">
            <a href="{reset_link}" style="background-color: #3498db; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; display: inline-block;">
                Reset Password
            </a>
        </p>
        <p>Or copy and paste this link into your browser:</p>
        <p style="word-break: break-all; color: #2c3e50;">{reset_link}</p>
        <p style="color: #e74c3c; font-weight: bold;">This link will expire in 1 hour.</p>
        <p>If you did not request this, please ignore this email.</p>
    </body>
    </html>
    """

    text_body = f"""Password Reset Request

You requested to reset your password for your HERckers account.

Click this link to reset your password:
{reset_link}

This link will expire in 1 hour.

If you did not request this, please ignore this email.
"""

    msg = MIMEMultipart("alternative")
    msg['From'] = EMAIL_FROM
    msg['To'] = to_email
    msg['Subject'] = subject
    msg.attach(MIMEText(text_body, 'plain'))
    msg.attach(MIMEText(html_body, 'html'))

    _send_email(msg)
    return True


def send_welcome_email(to_email: str, first_name: str):
    if not to_email or "@" not in to_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid email address."
        )

    if not first_name or len(first_name.strip()) == 0:
        first_name = "User"

    safe_name = first_name.strip()[:100]

    subject = "Welcome to HERckers"
    body = f"""
    <html>
    <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
        <h2 style="color: #2c3e50;">Welcome {safe_name}!</h2>
        <p>Your account has been successfully created on HERckers.</p>
        <p>You can now log in and start using our platform.</p>
    </body>
    </html>
    """

    msg = MIMEMultipart()
    msg['From'] = EMAIL_FROM
    msg['To'] = to_email
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'html'))

    _send_email(msg)
    return True
