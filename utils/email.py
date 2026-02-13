import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from config import Config


def send_email(to_email, subject, body, is_html=False):
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


def send_reset_email(to_email, reset_link):
    subject = "Password Reset - Kuckoo"
    body = f"""
Hello,

Click the link below to reset your password:

{reset_link}

This link expires in 10 min.
"""
    send_email(to_email, subject, body)
