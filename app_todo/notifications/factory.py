# app/notifications/factory.py
from .channels import InAppNotificationChannel, EmailNotificationChannel, PushNotificationChannel

class NotificationChannelFactory:
    @staticmethod
    def get_channel(channel_type: str):
        if channel_type == "in_app":
            return InAppNotificationChannel()
        elif channel_type == "email":
            return EmailNotificationChannel()
        elif channel_type == "push":
            return PushNotificationChannel()
        else:
            raise ValueError(f"Unknown notification channel: {channel_type}")
