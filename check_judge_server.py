#!/usr/bin/env python3
"""Quick check for judge server status"""

import subprocess
import requests
import json

def check_docker_containers():
    """Check if judge server Docker containers are running"""
    print("=== Checking Docker Containers ===\n")
    
    try:
        # Check for judge server containers
        result = subprocess.run(
            ["docker", "ps", "--format", "table {{.Names}}\t{{.Status}}\t{{.Ports}}"],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            print(result.stdout)
            
            # Check specifically for judge server
            if "judge" in result.stdout.lower() or "judger" in result.stdout.lower():
                print("\n✓ Judge server container found")
            else:
                print("\n✗ No judge server container found")
                print("\nTo start the judge server:")
                print("1. cd to your judge server directory")
                print("2. Run: docker-compose up -d")
        else:
            print("✗ Docker not running or not accessible")
            
    except FileNotFoundError:
        print("✗ Docker command not found. Is Docker installed?")
    except Exception as e:
        print(f"✗ Error checking Docker: {e}")


def check_judge_server_port():
    """Check if judge server port is accessible"""
    print("\n\n=== Checking Judge Server Port ===\n")
    
    # Common judge server ports
    ports_to_check = [8080, 12358]
    
    for port in ports_to_check:
        try:
            response = requests.get(f"http://localhost:{port}/", timeout=2)
            print(f"✓ Port {port} is accessible (Status: {response.status_code})")
        except requests.exceptions.ConnectionError:
            print(f"✗ Port {port} is not accessible")
        except Exception as e:
            print(f"✗ Error checking port {port}: {e}")


def check_backend_config():
    """Check backend configuration for judge server"""
    print("\n\n=== Checking Backend Configuration ===\n")
    
    config_file = "/Users/weilai/Desktop/Fufu_website/website10/OJ/OnlineJudge/oj/settings.py"
    try:
        with open(config_file, 'r') as f:
            content = f.read()
            
        # Check for judge server configuration
        if "JUDGE_SERVER_TOKEN" in content:
            print("✓ JUDGE_SERVER_TOKEN found in settings")
        else:
            print("✗ JUDGE_SERVER_TOKEN not found in settings")
            
        # Check for celery configuration
        if "CELERY_BROKER_URL" in content or "redis://" in content:
            print("✓ Celery/Redis configuration found")
        else:
            print("✗ Celery/Redis configuration not found")
            
    except FileNotFoundError:
        print(f"✗ Settings file not found: {config_file}")
    except Exception as e:
        print(f"✗ Error reading settings: {e}")


def check_redis():
    """Check if Redis is running"""
    print("\n\n=== Checking Redis ===\n")
    
    try:
        import redis
        r = redis.Redis(host='localhost', port=6379, db=0)
        r.ping()
        print("✓ Redis is running and accessible")
    except ImportError:
        print("⚠ Redis Python module not installed")
    except Exception as e:
        print(f"✗ Redis is not accessible: {e}")
        print("\nTo start Redis:")
        print("- On macOS: brew services start redis")
        print("- On Linux: sudo systemctl start redis")
        print("- Or run: redis-server")


def main():
    """Run all checks"""
    print("=== OnlineJudge Judge Server Status Check ===\n")
    
    check_docker_containers()
    check_judge_server_port()
    check_backend_config()
    check_redis()
    
    print("\n\n=== Summary ===")
    print("\nFor the judge server to work properly, you need:")
    print("1. Judge server Docker container running")
    print("2. Redis server running")
    print("3. Correct JUDGE_SERVER_TOKEN in backend settings")
    print("4. Network connectivity between backend and judge server")
    
    print("\n\nTo test submission functionality:")
    print("Run: python test_judge_submission.py")


if __name__ == "__main__":
    main()