#!/usr/bin/env python3
"""Create root user for OnlineJudge"""

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'oj.settings')
django.setup()

from account.models import User, UserProfile, AdminType
from options.options import SysOptions

def create_root_user():
    """Create root user if not exists"""
    username = "root"
    password = "rootroot"
    email = "root@admin.com"
    
    # Check if user exists
    if User.objects.filter(username=username).exists():
        print(f"User '{username}' already exists!")
        user = User.objects.get(username=username)
        # Make sure it's a super admin
        user.admin_type = AdminType.SUPER_ADMIN
        user.save()
        print(f"Updated user to SUPER_ADMIN")
        return True
    
    # Create user
    user = User.objects.create(
        username=username,
        email=email,
        admin_type=AdminType.SUPER_ADMIN,
        is_disabled=False
    )
    user.set_password(password)
    user.save()
    
    # Create user profile
    UserProfile.objects.create(
        user=user,
        real_name="Administrator"
    )
    
    print(f"✓ Created super admin user:")
    print(f"  Username: {username}")
    print(f"  Password: {password}")
    print(f"  Email: {email}")
    
    # Initialize system options
    if not SysOptions.judge_server_token:
        SysOptions.judge_server_token = "YOUR_TOKEN_HERE"
        print(f"✓ Set judge server token: YOUR_TOKEN_HERE")
    
    return True


if __name__ == "__main__":
    if create_root_user():
        print("\n✓ Root user ready!")
    else:
        print("\n✗ Failed to create root user")