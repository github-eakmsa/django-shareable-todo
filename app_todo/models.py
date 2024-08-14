from django.db import models
from django.contrib.auth import get_user_model
User = get_user_model()

class Todo(models.Model):
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='todos')
    title = models.CharField(max_length=50)
    body = models.CharField(max_length=250)
    attachments = models.CharField(max_length=250)
    expires_at = models.DateTimeField(auto_now=True)
    shared_with = models.ManyToManyField(User, blank=True, related_name='shared_todos')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.title}"
