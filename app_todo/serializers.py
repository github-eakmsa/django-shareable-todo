
from rest_framework import serializers
from .models import Notification, Todo

class FCMTokenSerializer(serializers.Serializer):
    fcm_token = serializers.CharField(max_length=255)

class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = ['id', 'user', 'type', 'message', 'is_read', 'created_at']

class TodoSerializer(serializers.ModelSerializer):
    roll_no = serializers.SerializerMethodField()
    class Meta:
        model = Todo
        fields = ['roll_no', 'id', 'title', 'body', 'duration', 'expires_at', 'created_at']
    
    def get_roll_no(self, obj):
        # Calculate the roll number based on the object's position in the queryset
        return self.context['roll_number_index'] + 1