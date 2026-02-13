import threading
from utils.email import send_email


def send_email_async(to_email, subject, body, is_html=False,):
    thread = threading.Thread(
        target=send_email,
        args=(to_email, subject, body, is_html, )
    )
    thread.start()
