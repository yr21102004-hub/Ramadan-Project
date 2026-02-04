import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv

load_dotenv()

def send_email(to_email, subject, body):
    """
    Sends an email using SMTP credentials from .env
    Falls back to console log if no credentials provided.
    """
    smtp_server = os.getenv('MAIL_SERVER')
    smtp_port = os.getenv('MAIL_PORT')
    smtp_user = os.getenv('MAIL_USERNAME')
    smtp_password = os.getenv('MAIL_PASSWORD')
    
    if not all([smtp_server, smtp_port, smtp_user, smtp_password]):
        print("---------------------------------------------------------")
        print(f"[EMAIL SIMULATION] To: {to_email}")
        print(f"Subject: {subject}")
        print(f"Body: {body}")
        print("---------------------------------------------------------")
        return False
        
    try:
        msg = MIMEMultipart()
        msg['From'] = smtp_user
        msg['To'] = to_email
        msg['Subject'] = subject
        
        msg.attach(MIMEText(body, 'html'))
        
        server = smtplib.SMTP(smtp_server, int(smtp_port))
        server.starttls()
        server.login(smtp_user, smtp_password)
        text = msg.as_string()
        server.sendmail(smtp_user, to_email, text)
        server.quit()
        return True
    except Exception as e:
        print(f"Failed to send email: {e}")
        return False
