import os
import smtplib
import logging
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from config import Config


logger = logging.getLogger("email_logger")


def send_email(to_email, subject, body, is_html=False):
    """
    Production-safe email sender.
    Will not crash app if SMTP fails.
    """

    # Disable email in Railway free environment (optional safety)
    if os.environ.get("RAILWAY_ENVIRONMENT"):
        logger.info("Email sending skipped (Railway environment).")
        return

    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = Config.MAIL_USERNAME
        msg["To"] = to_email

        if is_html:
            msg.attach(MIMEText(body, "html"))
        else:
            msg.attach(MIMEText(body, "plain"))

        with smtplib.SMTP_SSL(Config.MAIL_SERVER, Config.MAIL_PORT) as server:
            server.login(Config.MAIL_USERNAME, Config.MAIL_PASSWORD)
            server.send_message(msg)

        logger.info(f"Email sent successfully to {to_email}")

    except Exception as e:
        logger.error(f"Email sending failed: {str(e)}")
        # Do NOT raise error → prevents payment webhook crash
        return


def send_reset_email(to_email, reset_link):
    subject = "Password Reset - Kuckoo"
    body = f"""
Hello,

Click the link below to reset your password:

{reset_link}

This link expires in 10 minutes.
"""
    send_email(to_email, subject, body)
