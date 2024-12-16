
from background_task import background

from django.utils.timezone import now, timedelta

from django.conf import settings
from django.urls import reverse
from app_todo.models import Todo
from app_todo.notifications.service import NotificationService

@background(schedule=60) # Set an initial delay or keep it to run immediately
def send_due_date_reminder(todo_id):
    todo = Todo.objects.get(id=todo_id)
    current_time = now()
    reminder_time = todo.expires_at - timedelta(hours=6)
    
    if current_time >= reminder_time and not todo.reminder_sent:
        
        notification_service = NotificationService()

        # Define template name and context data
        template_name = "task_reminder"
        context = {
            "todoTitle": todo.title,
            "todoExpiryDate": todo.expires_at.strftime("%Y-%m-%d"),
            'todoDetailLink': str(settings.APP_URL)+str(reverse("todos.detail", args=[todo.id])),
        }
        
        # Define channels and send the notification
        channels = ["in_app", "push", "email"]
        notification_service.send_notification(user=todo.user, template_name=template_name, context=context, channels=channels)
