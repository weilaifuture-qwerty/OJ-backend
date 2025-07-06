from django.apps import AppConfig


class SubmissionConfig(AppConfig):
    name = 'submission'
    
    def ready(self):
        # Import signal handlers
        from . import signals