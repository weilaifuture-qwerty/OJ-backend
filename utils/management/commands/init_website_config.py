from django.core.management.base import BaseCommand
from django.db import connection
from options.options import SysOptions
from options.models import SysOptions as SysOptionsModel


class Command(BaseCommand):
    help = 'Initialize website configuration and verify system setup'

    def add_arguments(self, parser):
        parser.add_argument(
            '--verify-only',
            action='store_true',
            help='Only verify configuration without making changes',
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('=== Website Configuration Check ==='))
        
        # Check database connection
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                self.stdout.write(self.style.SUCCESS('✓ Database connection: OK'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'✗ Database connection: FAILED - {str(e)}'))
            return
        
        # Check if SysOptions table exists and has data
        try:
            count = SysOptionsModel.objects.count()
            self.stdout.write(self.style.SUCCESS(f'✓ SysOptions table: {count} entries found'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'✗ SysOptions table: FAILED - {str(e)}'))
            return
        
        # Check required configuration options
        required_options = [
            'website_base_url',
            'website_name', 
            'website_name_shortcut',
            'website_footer',
            'allow_register',
            'submission_list_show_all',
            'judge_server_token',
            'languages'
        ]
        
        missing_options = []
        
        for option_key in required_options:
            try:
                if not SysOptionsModel.objects.filter(key=option_key).exists():
                    missing_options.append(option_key)
                else:
                    value = getattr(SysOptions, option_key)
                    self.stdout.write(f'  ✓ {option_key}: {value}')
            except Exception as e:
                self.stdout.write(self.style.WARNING(f'  ⚠ {option_key}: Error accessing - {str(e)}'))
                missing_options.append(option_key)
        
        if missing_options:
            self.stdout.write(self.style.WARNING(f'Missing options: {missing_options}'))
            
            if not options['verify_only']:
                self.stdout.write('Initializing missing options...')
                try:
                    SysOptions._init_option()
                    self.stdout.write(self.style.SUCCESS('✓ Options initialized successfully'))
                    
                    # Verify after initialization
                    for option_key in missing_options:
                        try:
                            value = getattr(SysOptions, option_key)
                            self.stdout.write(f'  ✓ {option_key}: {value}')
                        except Exception as e:
                            self.stdout.write(self.style.ERROR(f'  ✗ {option_key}: Still failing - {str(e)}'))
                            
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f'✗ Initialization failed: {str(e)}'))
        else:
            self.stdout.write(self.style.SUCCESS('✓ All required options are present'))
        
        # Test website API endpoint simulation
        try:
            from conf.views import WebsiteConfigAPI
            from rest_framework.test import APIRequestFactory
            
            factory = APIRequestFactory()
            request = factory.get('/api/website/')
            view = WebsiteConfigAPI()
            view.format_kwarg = {}
            
            response = view.get(request)
            if response.status_code == 200:
                self.stdout.write(self.style.SUCCESS('✓ Website API endpoint: Working correctly'))
                self.stdout.write(f'  Response data: {response.data}')
            else:
                self.stdout.write(self.style.ERROR(f'✗ Website API endpoint: Status {response.status_code}'))
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'✗ Website API endpoint test failed: {str(e)}'))
        
        self.stdout.write(self.style.SUCCESS('\n=== Configuration Check Complete ==='))