from django import forms
from .models import Todo
from django.contrib.auth.models import User


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
class TodoForm(forms.ModelForm):

	# create meta class
	class Meta:
		# specify model to be used
		model = Todo

		# specify fields to be used
		fields = [
			"title",
			"body",
		]