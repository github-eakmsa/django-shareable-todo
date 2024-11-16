import os
from django.db import models
from django.contrib.auth import get_user_model
User = get_user_model()
from django.conf import settings
import uuid
from django_softdelete.models import SoftDeleteModel
from django.utils.timezone import timedelta


class UserProfile(models.Model):
    
    def generate_filename(instance, filename):
        ext = filename.split('.')[-1]
        filename = f"{uuid.uuid4()}.{ext}"
        return settings.PATH_FOR_USER_PROFILES + filename

    user = models.OneToOneField(User, blank=False, on_delete=models.CASCADE, related_name='user_profile')
    avatar = models.ImageField(upload_to=generate_filename)
    fcm_token = models.CharField(max_length=255, blank=True, null=True)
         
    def __str__(self):
        return self.user.email

class Workspace(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='workspaces')
    name = models.CharField(max_length=50)
    status = models.SmallIntegerField(default=settings.ACTIVE, choices=settings.RECORD_STATUS_CHOICES, blank=True)
    shared_with = models.ManyToManyField(User, blank=True, related_name='shared_workspaces')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        unique_together = ('user', 'name')
        return f"{self.name}"

class ActiveWorkspace(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='active_workspace')
    workspace = models.ForeignKey(Workspace, on_delete=models.CASCADE, related_name='active_workspace')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        unique_together = ('user')
        return f"{self.workspace}"

class Todo(SoftDeleteModel):

    # todo status constants 
    PENDING = 0
    IN_PROGRESS = 1
    COMPLETED = 2
    ON_PRIORITY = 3
    NEEDS_INFO = 4
    ON_HOLD = 5
    CANCELLED = 6

    # todo status choices 
    TODO_STATUS_CHOICES = (
        (PENDING, 'Pending'),
        (IN_PROGRESS, 'In Progress'),
        (COMPLETED, 'Completed'),
        (ON_PRIORITY, 'On Priority'), 
        (NEEDS_INFO, 'Needs Info'),
        (ON_HOLD, 'On Hold'),
        (CANCELLED, 'Cancelled'), 
    )
    
    workspace = models.ForeignKey(Workspace, on_delete=models.CASCADE, related_name='todos')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='todos')
    title = models.CharField(max_length=250)
    body = models.TextField(blank=True)
    duration = models.FloatField(blank=True, null=True)
    expires_at = models.DateTimeField()
    shared_with = models.ManyToManyField(User, blank=True, related_name='shared_todos')
    todo_status = models.SmallIntegerField(default=PENDING, choices=TODO_STATUS_CHOICES, blank=True)
    status = models.SmallIntegerField(default=settings.ACTIVE, choices=settings.RECORD_STATUS_CHOICES, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    needs_reminder = models.BooleanField(default=True)
    reminder_sent = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.title}"

class TodoAttachment(models.Model):

    def generate_filename(instance, filename):
        ext = filename.split('.')[-1]
        filename = f"{uuid.uuid4()}.{ext}"
        return settings.PATH_FOR_TODO_ATTACHMENTS + filename
    
    todo = models.ForeignKey(Todo, on_delete=models.CASCADE, related_name='todo_attachments')
    attachment = models.FileField(upload_to=generate_filename)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.attachment.url
    
    def filename(self):
        return os.path.basename(self.attachment.name)

    def delete(self, *args, **kwargs):
        os.remove(os.path.join(settings.MEDIA_ROOT, self.attachment.name))
        super(TodoAttachment,self).delete(*args,**kwargs)
        self.delete()
    
class TodoTimeline(models.Model):
    TODO_STATUS_CHOICES = settings.TODO_STATUS_CHOICES
    todo = models.ForeignKey(Todo, on_delete=models.CASCADE, related_name='todo_timeline')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    todo_status = models.SmallIntegerField(choices=TODO_STATUS_CHOICES, blank=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.todo_status

class Comment(models.Model):
    todo = models.ForeignKey(Todo, on_delete=models.CASCADE, related_name='comments')
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'Comment by {self.author} on {self.post}'

class Notification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    type = models.CharField(max_length=30)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username}: {self.message}"