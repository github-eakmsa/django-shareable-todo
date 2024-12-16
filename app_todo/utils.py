from background_task import background
from django.core.mail import EmailMessage
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

@background(schedule=1)
def send_email(subject, message, recipient_list, from_email=None, html_message=None, attachments=None):
    """
    Utility function to send emails.
    
    Args:
        subject (str): Subject of the email.
        message (str): Plain text message.
        recipient_list (list): List of recipients.
        from_email (str): Sender's email address. Defaults to settings.DEFAULT_FROM_EMAIL.
        html_message (str): HTML message. Defaults to None.
        attachments (list): List of file paths to attach. Defaults to None.
    
    Returns:
        bool: True if email sent successfully, False otherwise.
    """
    try:
        from_email = from_email or settings.DEFAULT_FROM_EMAIL
        email = EmailMessage(subject, message, from_email, recipient_list)

        # Attach HTML content if provided
        if html_message:
            email.content_subtype = 'html'
            email.body = html_message

        # Attach files if provided
        if attachments:
            for attachment in attachments:
                email.attach_file(attachment)
        
        # Send email
        email.send()
        return True
    except Exception as e:
        # Log the error
        logger.error(f"Error sending email: {e}")
        return False
        
        # # Send reminder email
        # mail_subject = 'Todo Reminder'
        # text_content = f'Your todo "{todo.title}" is due in less than 6 hours!'

        # email_sent = send_email(mail_subject, text_content, [todo.user.email], html_message=text_content)
            
        # if email_sent:
        #     # If email sent successfully, proceed to next step
        #     # Mark the reminder as sent
        #     todo.reminder_sent = True
        #     todo.save()
        #     return True
        # else:
        #     # Handle email failure case
        #     return False
