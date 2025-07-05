#!/usr/bin/env python3
"""Simple script to configure judge server token"""

import requests
import secrets

# Default token or generate a new one
TOKEN = "YOUR_JUDGE_SERVER_TOKEN_HERE"  # Change this!

# If using docker judge server, it might have a default token
# Common default tokens to try:
DEFAULT_TOKENS = [
    "YOUR_TOKEN_HERE",
    "CHANGE_THIS",
    "token",
    secrets.token_urlsafe(32)  # Generate new if others don't work
]

def test_judge_server():
    """Test connection to judge server"""
    judge_url = "http://localhost:12358"
    
    print("Testing judge server connection...")
    
    for token in DEFAULT_TOKENS:
        print(f"\nTrying token: {token[:20]}...")
        
        headers = {"X-Judge-Server-Token": token}
        
        try:
            # Try ping endpoint
            response = requests.post(
                f"{judge_url}/ping",
                headers=headers,
                json={},
                timeout=5
            )
            
            if response.status_code == 200:
                print(f"✓ SUCCESS! Token works: {token}")
                
                # Save working token
                with open('working_judge_token.txt', 'w') as f:
                    f.write(token)
                print(f"\nToken saved to: working_judge_token.txt")
                
                # Try to get server info
                info_resp = requests.post(
                    f"{judge_url}/info",
                    headers=headers,
                    json={},
                    timeout=5
                )
                
                if info_resp.status_code == 200:
                    print("\nJudge Server Info:")
                    print(info_resp.json())
                
                return token
            else:
                print(f"✗ Token failed: {response.status_code}")
                
        except Exception as e:
            print(f"✗ Error: {e}")
    
    print("\n✗ No working token found!")
    print("\nTo fix this:")
    print("1. Check judge server logs: docker logs judgeserver-judge_server-1")
    print("2. Set token environment variable when starting judge server")
    print("3. Or use the token in Django admin panel")
    
    return None


def main():
    """Main function"""
    print("=== Judge Server Token Configuration ===\n")
    
    # Test connection
    working_token = test_judge_server()
    
    if working_token:
        print("\n\n=== Next Steps ===")
        print("1. Start Django server: python manage.py runserver")
        print("2. Login as admin (root/rootroot)")
        print("3. Go to: http://localhost:8000/admin/conf/judgeserver/")
        print("4. If no judge server exists, it will auto-register")
        print("5. Or manually set token in Django shell:")
        print(f"\n   python manage.py shell")
        print(f"   >>> from options.options import SysOptions")
        print(f"   >>> SysOptions.judge_server_token = '{working_token}'")
        print("\n6. Test submission: python test_judge_submission.py")


if __name__ == "__main__":
    main()