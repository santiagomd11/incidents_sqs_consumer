import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import logging

logging.basicConfig(level=os.environ.get("LOG_LEVEL", "INFO"))
logger = logging.getLogger(__name__)

def send_email(to_email, subject, body):
    gmail_user = os.environ.get('GMAIL_USER')
    gmail_password = os.environ.get('GMAIL_PASSWORD')
    
    if not gmail_user or not gmail_password:
        logger.error("Environment variables GMAIL_USER and GMAIL_PASSWORD must be set")
        raise Exception("Environment variables GMAIL_USER and GMAIL_PASSWORD must be set")

    try:
        # Set up the MIME
        msg = MIMEMultipart()
        msg['From'] = gmail_user
        msg['To'] = to_email
        msg['Subject'] = subject
        
        # Attach the email body
        msg.attach(MIMEText(body, 'plain'))
        
        logger.info("Connecting to Gmail SMTP server...")
        # Connect to Gmail's SMTP server
        server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
        logger.info("Connected to Gmail SMTP server.")
        
        logger.info("Logging in to Gmail SMTP server...")
        server.login(gmail_user, gmail_password)
        logger.info("Logged in to Gmail SMTP server.")
        
        logger.info(f"Sending email to {to_email} with subject '{subject}'...")
        text = msg.as_string()
        server.sendmail(gmail_user, to_email, text)
        server.quit()
        logger.info("Email sent successfully!")
        
    except smtplib.SMTPException as smtp_error:
        logger.error(f"SMTP error occurred: {smtp_error}")
    except Exception as e:
        logger.error(f"Failed to send email due to: {e}")