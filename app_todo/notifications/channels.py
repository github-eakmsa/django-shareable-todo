# app/notifications/channels.py
from abc import ABC, abstractmethod

from app_todo.models import Notification

from app_todo.utils import send_email

from firebase_admin import messaging

class BaseNotificationChannel(ABC):
    @abstractmethod
    def send(self, notification: Notification, subject=None):
        pass

class InAppNotificationChannel(BaseNotificationChannel):
    def send(self, notification: Notification):
        # Save notification to the database for in-app display
        notification.save()

class EmailNotificationChannel(BaseNotificationChannel):
    def send(self, notification: Notification, subject="Notification"):
        subject=subject
        message=notification.message
        recipient_list=[notification.user.email]
        
        send_email(subject, message, recipient_list, html_message=message)

class PushNotificationChannel(BaseNotificationChannel):
    def send(self, notification: Notification, subject="Notification"):
         
        registration_id = notification.user.user_profile.fcm_token
        title = subject
        body = notification.message    
    
        # Create a notification message
        message = messaging.Message(
            notification=messaging.Notification(
                title=title,
                body=body
            ),
            token=registration_id
        )
        # Send the message
        response = messaging.send(message)
        print('Successfully sent message:', response)
