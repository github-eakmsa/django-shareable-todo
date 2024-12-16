from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils.timezone import timedelta

from .models import Todo
from .tasks import send_due_date_reminder

@receiver(post_save, sender=Todo)
def schedule_todo_reminder(sender, instance, created, **kwargs):
    if created and not instance.reminder_sent and instance.needs_reminder:
        # Schedule the reminder task 6 hours before the due date
        reminder_time = instance.expires_at - timedelta(hours=6)
        
        send_due_date_reminder(instance.id, schedule=reminder_time)
