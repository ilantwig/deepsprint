import smtplib
from utils.utils import clean_emoji
from email.header import Header
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import os 

class Email:
    """Utils for sending emails."""

    @staticmethod
    def send_email(subject: str, body: str) -> str:
        """Send email with given subject and body."""
        return _Email.send_email(subject, body)
    
class _Email:
    """Email handling functionality."""
    
    @staticmethod
    def send_email(subject: str, body: str) -> str:
        """Send email using predefined credentials."""
        return _Email._send_email(os.getenv("EMAIL_FROM"), 
                               os.getenv("EMAIL_KEY"), 
                               os.getenv("EMAIL_TO"), 
                               subject, 
                               body)

    @staticmethod
    def _send_email(sender_email: str, sender_password: str, 
                   recipient_email: str, subject: str, body: str) -> str:
        """
        Internal method to send email using SMTP.
        
        Args:
            sender_email: Sender's email address
            sender_password: Sender's email password
            recipient_email: Recipient's email address
            subject: Email subject
            body: Email body
            
        Returns:
            Status message
        """
        try:
            message = MIMEMultipart()
            message['From'] = sender_email
            message['To'] = recipient_email
            message['Subject'] = Header(clean_emoji(subject), 'utf-8')
            message.attach(MIMEText(body.encode('utf-8'), 'plain', 'utf-8'))
            
            with smtplib.SMTP_SSL('smtp.mail.yahoo.com', 465) as server:
                server.login(sender_email, sender_password)
                server.send_message(message)
            return "Email sent successfully"
        except Exception as e:
            return f"Error sending email: {str(e)}"