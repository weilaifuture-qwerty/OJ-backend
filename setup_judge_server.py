#!/usr/bin/env python3
"""Setup judge server configuration"""

import os
import sys
import django
import requests
import secrets

# Setup Django environment
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "oj.settings")
django.setup()

from options.options import SysOptions
from conf.models import JudgeServer
from django.utils import timezone

def setup_judge_server():
    """Configure judge server in the system"""
    
    print("=== Setting up Judge Server ===\n")
    
    # Generate a secure token if not exists
    current_token = SysOptions.judge_server_token
    print(f"Current token: {current_token[:10]}..." if current_token else "No token set")
    
    # If no token or using default, generate a new one
    if not current_token or current_token == "CHANGE_THIS":
        new_token = secrets.token_urlsafe(32)
        SysOptions.judge_server_token = new_token
        print(f"Generated new token: {new_token}")
        token = new_token
    else:
        token = current_token
        print(f"Using existing token")
    
    # Check if judge server is accessible
    judge_server_url = "http://localhost:12358"
    print(f"\nChecking judge server at {judge_server_url}...")
    
    try:
        # Test connection with token
        headers = {"X-Judge-Server-Token": token}
        response = requests.post(
            f"{judge_server_url}/ping",
            headers=headers,
            json={},
            timeout=5
        )
        print(f"Ping response: {response.status_code}")
        
        if response.status_code == 200:
            print("✓ Judge server is accessible")
            
            # Try to get judge server info
            info_response = requests.post(
                f"{judge_server_url}/info",
                headers=headers,
                json={},
                timeout=5
            )
            if info_response.status_code == 200:
                info = info_response.json()
                print(f"\nJudge Server Info:")
                print(f"- Version: {info.get('judger_version', 'Unknown')}")
                print(f"- Hostname: {info.get('hostname', 'Unknown')}")
                print(f"- CPU Cores: {info.get('cpu_core', 'Unknown')}")
        else:
            print(f"✗ Judge server returned status {response.status_code}")
            print(f"Response: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("✗ Could not connect to judge server")
        print("Make sure the judge server is running on port 12358")
    except Exception as e:
        print(f"✗ Error: {e}")
    
    # Register judge server in database
    print("\nRegistering judge server in database...")
    
    # Check if already exists
    existing_servers = JudgeServer.objects.filter(
        service_url__contains="12358"
    )
    
    if existing_servers.exists():
        print(f"Found {existing_servers.count()} existing judge server(s)")
        for server in existing_servers:
            print(f"- {server.hostname} at {server.service_url} (Status: {server.status})")
            # Update heartbeat
            server.last_heartbeat = timezone.now()
            server.save()
    else:
        # Create new judge server entry
        judge_server = JudgeServer.objects.create(
            hostname="local-judge-server",
            ip="127.0.0.1",
            judger_version="2.0.0",
            cpu_core=4,
            memory_usage=0.0,
            cpu_usage=0.0,
            last_heartbeat=timezone.now(),
            create_time=timezone.now(),
            task_number=0,
            service_url=judge_server_url,
            is_disabled=False
        )
        print(f"✓ Created judge server: {judge_server.hostname}")
    
    print("\n=== Configuration Complete ===")
    print(f"\nJudge Server Token: {token}")
    print("\nIMPORTANT: You need to configure the judge server with this token!")
    print("\nFor docker-based judge server, create a token.txt file:")
    print(f"echo '{token}' > token.txt")
    print("docker cp token.txt judgeserver-judge_server-1:/code/token.txt")
    print("\nOr set it as an environment variable when starting the container:")
    print(f"docker run -e TOKEN={token} ...")
    
    print("\n\nTo test the setup:")
    print("1. python manage.py runserver")
    print("2. python test_judge_submission.py")
    
    # Save token to a file for reference
    with open('judge_server_token.txt', 'w') as f:
        f.write(token)
    print(f"\nToken saved to: judge_server_token.txt")


if __name__ == "__main__":
    setup_judge_server()