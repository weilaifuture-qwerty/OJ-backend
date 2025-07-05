#!/usr/bin/env python3
"""Configure judge server in database"""

import os
import sys
import django
from datetime import datetime

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'oj.settings')
django.setup()

from django.utils import timezone
from conf.models import JudgeServer
from options.options import SysOptions

def configure_judge_server():
    """Configure judge server"""
    print("Configuring judge server...")
    
    # Set judge server token
    if not SysOptions.judge_server_token:
        SysOptions.judge_server_token = "YOUR_TOKEN_HERE"
        print("✓ Set judge server token: YOUR_TOKEN_HERE")
    else:
        print(f"✓ Judge server token already set: {SysOptions.judge_server_token}")
    
    # Check if judge server already exists
    servers = JudgeServer.objects.all()
    if servers.exists():
        print(f"\nExisting judge servers:")
        for server in servers:
            print(f"  - {server.hostname} at {server.ip}")
            print(f"    Status: {'Enabled' if not server.is_disabled else 'Disabled'}")
            print(f"    Last heartbeat: {server.last_heartbeat}")
        
        # Update the first server
        server = servers.first()
        server.ip = "http://localhost:12358"
        server.service_url = "http://localhost:12358"
        server.last_heartbeat = timezone.now()
        server.is_disabled = False
        server.save()
        print(f"\n✓ Updated judge server: {server.hostname}")
    else:
        # Create new judge server
        server = JudgeServer.objects.create(
            hostname="local-judge-server",
            ip="http://localhost:12358",
            judger_version="2.3.1",
            cpu_core=4,
            memory_usage=0.0,
            cpu_usage=0.0,
            last_heartbeat=timezone.now(),
            create_time=timezone.now(),
            task_number=0,
            service_url="http://localhost:12358",
            is_disabled=False
        )
        print(f"\n✓ Created judge server: {server.hostname}")
        print(f"  URL: {server.service_url}")
        print(f"  Token: {SysOptions.judge_server_token}")
    
    # Test connection to judge server
    import requests
    try:
        response = requests.get("http://localhost:12358/", timeout=5)
        if response.status_code == 200:
            print(f"\n✓ Judge server is accessible")
        else:
            print(f"\n⚠️ Judge server returned status: {response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"\n✗ Cannot connect to judge server: {e}")
        print("  Make sure the judge server Docker container is running")
    
    return True


if __name__ == "__main__":
    if configure_judge_server():
        print("\n✓ Judge server configuration complete!")
        print("\nNext steps:")
        print("1. Start Dramatiq worker: python manage.py rundramatiq")
        print("2. Test submission: python test_judge_final.py")
    else:
        print("\n✗ Failed to configure judge server")