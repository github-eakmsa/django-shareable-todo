# notifications/service.py
from .template_manager import TemplateManager
from .factory import NotificationChannelFactory
from app_todo.models import Notification

class NotificationService:
    def send_notification(self, user, template_name, context, channels):
        # Fetch and render the template with context
        subject, message = TemplateManager.render(template_name, context)

        # Create a notification instance to pass to channels
        notification = Notification(user=user, message=message, type=template_name)
        
        # Loop through channels and send
        for channel_type in channels:
            channel = NotificationChannelFactory.get_channel(channel_type)
            if channel_type in ("email", "push"):
                channel.send(notification, subject=subject)  # Pass subject for email
            else:
                channel.send(notification)
        
        # Save the notification if it's an in-app notification
        # if "in_app" in channels:
        #     notification.save()
