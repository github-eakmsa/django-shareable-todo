# notifications/template_manager.py
from string import Template
from django.conf import settings
import os

class TemplateManager:
    TEMPLATE_DIR = os.path.join(settings.BASE_DIR, 'app_todo', 'notifications', 'templates')

    @staticmethod
    def get_template_content(template_name, template_type='body'):
        # Construct the path for the template file based on the template name and type
        file_path = os.path.join(TemplateManager.TEMPLATE_DIR, f"{template_name}_{template_type}.txt")
        
        if not os.path.exists(file_path):
            raise ValueError(f"Template file '{file_path}' does not exist.")

        with open(file_path, 'r') as template_file:
            return Template(template_file.read())

    @staticmethod
    def render(template_name, context):
        # Get the subject and body templates
        subject_template = TemplateManager.get_template_content(template_name, 'subject')
        body_template = TemplateManager.get_template_content(template_name, 'body')
        
        # Substitute placeholders with values from context
        rendered_subject = subject_template.safe_substitute(context)
        rendered_body = body_template.safe_substitute(context)
        
        return rendered_subject, rendered_body
