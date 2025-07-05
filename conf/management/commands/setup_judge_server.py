from django.core.management.base import BaseCommand
from django.utils import timezone
from conf.models import JudgeServer
from options.options import SysOptions


class Command(BaseCommand):
    help = 'Setup judge server configuration'

    def handle(self, *args, **options):
        # Set the judge server token
        token = "YOUR_TOKEN_HERE"
        SysOptions.judge_server_token = token
        self.stdout.write(self.style.SUCCESS(f'Set judge server token: {token}'))
        
        # Check/create judge server entry
        judge_server_url = "http://judge-server:8080"  # Internal Docker URL
        external_url = "http://localhost:12358"  # External URL for testing
        
        # Try to find existing judge server
        judge_server = JudgeServer.objects.filter(
            service_url__in=[judge_server_url, external_url, "http://127.0.0.1:12358"]
        ).first()
        
        if judge_server:
            # Update existing
            judge_server.last_heartbeat = timezone.now()
            judge_server.hostname = "docker-judge-server"
            judge_server.save()
            self.stdout.write(self.style.SUCCESS(f'Updated existing judge server: {judge_server.service_url}'))
        else:
            # Create new
            judge_server = JudgeServer.objects.create(
                hostname="docker-judge-server",
                ip="127.0.0.1",
                judger_version="2.3.2",
                cpu_core=4,
                memory_usage=0.0,
                cpu_usage=0.0,
                last_heartbeat=timezone.now(),
                create_time=timezone.now(),
                task_number=0,
                service_url=external_url,  # Use external URL
                is_disabled=False
            )
            self.stdout.write(self.style.SUCCESS(f'Created judge server: {judge_server.service_url}'))
        
        self.stdout.write(self.style.SUCCESS('\nJudge server configuration complete!'))
        self.stdout.write('You can now test submissions.')
        
        # Show current configuration
        self.stdout.write('\nCurrent configuration:')
        self.stdout.write(f'- Token: {SysOptions.judge_server_token}')
        self.stdout.write(f'- Judge Server URL: {judge_server.service_url}')
        self.stdout.write(f'- Status: {judge_server.status}')