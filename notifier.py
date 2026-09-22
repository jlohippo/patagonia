import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os

def send_alert(to_email, product):
    """
    Sends an email alert when a product meets the discount target.
    Expects product to be a ProductMonitor model instance or a dict with similar properties.
    """
    smtp_server = os.environ.get('SMTP_SERVER')
    smtp_port = os.environ.get('SMTP_PORT')
    smtp_user = os.environ.get('SMTP_USER')
    smtp_password = os.environ.get('SMTP_PASSWORD')

    # Do not attempt to send if SMTP config is missing (avoids crashing)
    if not all([smtp_server, smtp_port, smtp_user, smtp_password]):
        print(f"SMTP configuration missing. Would have sent email to {to_email} for {product.name}")
        return False

    try:
        smtp_port = int(smtp_port)
    except ValueError:
        print("SMTP_PORT must be an integer.")
        return False

    sender_email = smtp_user
    subject = f"Patagonia Web Specials Alert: {product.name} is on sale!"

    body = f"""
    Great news!

    The Patagonia product you are monitoring is currently on sale.

    Product: {product.name}
    URL: {product.url}
    Size: {product.size or 'Any'}
    Color: {product.color or 'Any'}

    Original Price: ${product.original_price:.2f}
    Current Price: ${product.current_price:.2f}
    """

    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = to_email
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))

    try:
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(smtp_user, smtp_password)
        server.send_message(msg)
        server.quit()
        print(f"Email sent successfully to {to_email} for {product.name}")
        return True
    except Exception as e:
        print(f"Failed to send email: {e}")
        return False
