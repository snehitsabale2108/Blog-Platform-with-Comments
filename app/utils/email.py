from flask_mail import Message
from flask import render_template_string, current_app
from ..extensions import mail


VERIFY_TEMPLATE = """
<p>Hello {{ name }},</p>
<p>Please verify your email by clicking the link below:</p>
<p><a href="{{ url }}">Verify Email</a></p>
<p>This link expires in 1 hour.</p>
<p>— The Inkwell Team</p>
"""

RESET_TEMPLATE = """
<p>Hello {{ name }},</p>
<p>Click below to reset your password:</p>
<p><a href="{{ url }}">Reset Password</a></p>
<p>This link expires in 1 hour. If you didn't request this, ignore this email.</p>
<p>— The Inkwell Team</p>
"""


def send_verification_email(user):
    token = user.generate_verification_token()
    url = f"{current_app.config['APP_URL']}/auth/verify/{token}"
    html = render_template_string(VERIFY_TEMPLATE, name=user.display_name or user.username, url=url)
    msg = Message(
        subject="Verify your Inkwell account",
        recipients=[user.email],
        html=html,
    )
    try:
        mail.send(msg)
    except Exception as e:
        current_app.logger.warning(f"Could not send verification email: {e}")


def send_password_reset_email(user):
    token = user.generate_password_reset_token()
    url = f"{current_app.config['APP_URL']}/auth/reset-password/{token}"
    html = render_template_string(RESET_TEMPLATE, name=user.display_name or user.username, url=url)
    msg = Message(
        subject="Reset your Inkwell password",
        recipients=[user.email],
        html=html,
    )
    try:
        mail.send(msg)
    except Exception as e:
        current_app.logger.warning(f"Could not send password reset email: {e}")
