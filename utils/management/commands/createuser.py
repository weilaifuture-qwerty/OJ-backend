from django.core.management.base import BaseCommand
from django.contrib.auth.hashers import make_password
from django.db import transaction

from account.models import User, UserProfile, AdminType, ProblemPermission


class Command(BaseCommand):
    help = 'Create a user with username, password, and real name'

    def add_arguments(self, parser):
        parser.add_argument('--username', type=str, required=True, help='Username for the new user')
        parser.add_argument('--password', type=str, required=True, help='Password for the new user')
        parser.add_argument('--real_name', type=str, default='', help='Real name of the user (optional)')
        parser.add_argument('--email', type=str, default=None, help='Email address (optional, defaults to username@example.com)')
        parser.add_argument('--admin', action='store_true', help='Create as admin user')
        parser.add_argument('--super_admin', action='store_true', help='Create as super admin user')

    def handle(self, *args, **options):
        username = options['username'].lower()
        password = options['password']
        real_name = options['real_name']
        email = options['email'] or f"{username}@example.com"
        
        # Determine admin type
        if options['super_admin']:
            admin_type = AdminType.SUPER_ADMIN
            problem_permission = ProblemPermission.ALL
        elif options['admin']:
            admin_type = AdminType.ADMIN
            problem_permission = ProblemPermission.OWN
        else:
            admin_type = AdminType.REGULAR_USER
            problem_permission = ProblemPermission.NONE
        
        # Check if user already exists
        if User.objects.filter(username=username).exists():
            self.stdout.write(self.style.ERROR(f'User "{username}" already exists'))
            return
        
        if User.objects.filter(email=email).exists():
            self.stdout.write(self.style.ERROR(f'Email "{email}" already exists'))
            return
        
        try:
            with transaction.atomic():
                # Create user
                user = User(
                    username=username,
                    email=email,
                    admin_type=admin_type,
                    problem_permission=problem_permission,
                    open_api=False,
                    two_factor_auth=False,
                    is_disabled=False
                )
                user.set_password(password)
                user.save()
                
                # Create user profile
                UserProfile.objects.create(
                    user=user,
                    real_name=real_name
                )
                
                self.stdout.write(self.style.SUCCESS(f'Successfully created user "{username}"'))
                self.stdout.write(f'  Username: {username}')
                self.stdout.write(f'  Email: {email}')
                self.stdout.write(f'  Real Name: {real_name or "(not set)"}')
                self.stdout.write(f'  Admin Type: {admin_type}')
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error creating user: {str(e)}'))