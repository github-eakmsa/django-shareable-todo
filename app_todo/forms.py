from django import forms
from .models import Todo, Comment, Workspace
from django.contrib.auth.models import User
from django.contrib.auth.forms import PasswordChangeForm

class CustomPasswordChangeForm(PasswordChangeForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Example: Add custom styling or placeholder text
        # self.fields['old_password'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Old Password'})
        # self.fields['new_password1'].widget.attrs.update({'class': 'form-control', 'placeholder': 'New Password'})
        # self.fields['new_password2'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Confirm New Password'})

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
      