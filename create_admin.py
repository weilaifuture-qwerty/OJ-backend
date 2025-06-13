import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'oj.settings')
django.setup()

from account.models import User, UserProfile, AdminType, ProblemPermission

def create_admin_user():
    username = 'admin'
    password = 'admin123'  # You should change this password
    email = 'admin@example.com'

    if not User.objects.filter(username=username).exists():
        user = User.objects.create(
            username=username,
            email=email,
            admin_type=AdminType.SUPER_ADMIN,
            problem_permission=ProblemPermission.ALL,
            is_disabled=False
        )
        user.set_password(password)
        user.save()

        # Create user profile
        UserProfile.objects.create(
            user=user,
            real_name='Administrator',
            acm_problems_status={},
            oi_problems_status={}
        )
        print(f"Admin user created successfully with username: {username} and password: {password}")
    else:
        print("Admin user already exists")

if __name__ == '__main__':
    create_admin_user() 