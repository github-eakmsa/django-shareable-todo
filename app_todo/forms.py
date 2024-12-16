from django import forms
from .models import Feedback, Todo, Comment, Workspace
from django.contrib.auth.models import User
from django.contrib.auth.forms import PasswordChangeForm

# creating a form
class FeedbackForm(forms.ModelForm):

	# create meta class
	class Meta:
		# specify model to be used
		model = Feedback

		# specify fields to be used
		fields = [
			"name",
			"email",
			"message",
		]

class CustomPasswordChangeForm(PasswordChangeForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

# creating a form
class UserForm(forms.ModelForm):

	# create meta class
	class Meta:
		# specify model to be used
		model = User

		# specify fields to be used
		fields = [
			# "name",
			"username",
			"password",
		]

# creating a form
class WorkspaceForm(forms.ModelForm):

	# create meta class
	class Meta:
		# specify model to be used
		model = Workspace

		# specify fields to be used
		fields = [
			# "user",
			"name",
		]

# creating a form
class TodoForm(forms.ModelForm):

	# create meta class
	class Meta:
		# specify model to be used
		model = Todo

		# specify fields to be used
		fields = [
			"title",
			"body",
			"duration",
			"expires_at",
			"needs_reminder",
			"status",
		]
	
class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['content']

class TodoStatusChangeForm(forms.ModelForm):
	# create meta class
	class Meta:
		# specify model to be used
		model = Todo

		# specify fields to be used
		fields = [
			"todo_status",
		]
      