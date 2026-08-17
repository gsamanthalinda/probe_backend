import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from pathlib import Path
from dotenv import load_dotenv

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
    server = smtplib.SMTP(SMTP_HOST, SMTP_PORT)
    server.starttls()
    server.login(SMTP_USER, SMTP_PASSWORD)
    return server


def send_password_reset_email(to_email: str, reset_token: str):
    reset_link = f"{FRONTEND_URL}/reset-password?token={reset_token}"
    
    subject = "HERckers - Password Reset Request"
    body = f"""
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
        <p style="color: #e74c3c; font-weight: bold;">This link will expire in 1 hour.</p>
        <p>If you did not request this, please ignore this email.</p>
    </body>
    </html>
    """
    
    msg = MIMEMultipart()
    msg['From'] = EMAIL_FROM
    msg['To'] = to_email
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'html'))
    
    try:
        with _get_smtp_server() as server:
            server.sendmail(EMAIL_FROM, to_email, msg.as_string())
        print(f"[EMAIL] Password reset email sent to {to_email}")
        return True
    except Exception as e:
        print(f"[EMAIL] Failed to send password reset email to {to_email}: {e}")
        return False


def send_welcome_email(to_email: str, first_name: str):
    subject = "Welcome to HERckers"
    body = f"""
    <html>
    <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
        <h2 style="color: #2c3e50;">Welcome {first_name}!</h2>
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
    
    try:
        with _get_smtp_server() as server:
            server.sendmail(EMAIL_FROM, to_email, msg.as_string())
        print(f"[EMAIL] Welcome email sent to {to_email}")
        return True
    except Exception as e:
        print(f"[EMAIL] Failed to send welcome email to {to_email}: {e}")
        return False
