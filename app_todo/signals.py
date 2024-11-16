from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils.timezone import timedelta

from app_todo.notifications.service import NotificationService

from .models import Todo
from .utils import send_due_date_reminder

@receiver(post_save, sender=Todo)
def schedule_todo_reminder(sender, instance, created, **kwargs):
    if created and not instance.reminder_sent and instance.needs_reminder:
        # Schedule the reminder task 6 hours before the due date
        reminder_time = instance.expires_at - timedelta(hours=6)
        
        send_due_date_reminder(instance.id, schedule=reminder_time)

        notification_service = NotificationService()

        # Define template name and context data
        template_name = "task_reminder"
        context = {
            "username": instance.user.username,
            "task_name": instance.title,
            "due_date": instance.due_date.strftime("%Y-%m-%d")
        }
        
        # Define channels and send the notification
        channels = ["in_app", "push", "email"]
        notification_service.send_notification(user=instance.user, template_name=template_name, context=context, channels=channels)