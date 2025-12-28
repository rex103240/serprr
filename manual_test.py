#!/usr/bin/env python3
"""
Manual testing script for IronLifter fixes
"""

import requests
import re

def test_login():
    """Test login manually"""
    session = requests.Session()
    
    # Get login page
    response = session.get("http://127.0.0.1:5000/login")
    print(f"Login page status: {response.status_code}")
    
    # Extract CSRF token
    csrf_match = re.search(r'name="csrf_token" type="hidden" value="([^"]+)"', response.text)
    csrf_token = csrf_match.group(1) if csrf_match else "NO_TOKEN_FOUND"
    print(f"CSRF token: {csrf_token[:20]}...")
    
    # Try login
    login_data = {
        'username': 'admin',
        'password': 'change_this_password_immediately',
        'csrf_token': csrf_token
    }
    
    response = session.post("http://127.0.0.1:5000/login", data=login_data)
    print(f"Login response status: {response.status_code}")
    print(f"Login response headers: {dict(response.headers)}")
    
    if response.status_code == 302:
        print("Login successful - redirected")
    else:
        print("Login failed")
        print(f"Response content: {response.text[:500]}")

def test_search():
    """Test search validation"""
    print("\n=== Testing Search ===")
    
    # Test XSS in search
    response = requests.get("http://127.0.0.1:5000/members/live_search", params={'q': '<script>alert("xss")</script>'})
    print(f"XSS search status: {response.status_code}")
    print(f"XSS in response: {'<script>' in response.text}")
    
    # Test short search
    response = requests.get("http://127.0.0.1:5000/members/live_search", params={'q': 'a'})
    print(f"Short search status: {response.status_code}")
    print(f"Response length: {len(response.text)}")

def test_api():
    """Test API security"""
    print("\n=== Testing API ===")
    
    # Test without token
    response = requests.post("http://127.0.0.1:5000/api/checkin", json={'member_id': '12345'})
    print(f"API no token status: {response.status_code}")
    print(f"API response: {response.text}")
    
    # Test with wrong token
    headers = {'X-Kiosk-Secret': 'wrong_token'}
    response = requests.post("http://127.0.0.1:5000/api/checkin", json={'member_id': '12345'}, headers=headers)
    print(f"API wrong token status: {response.status_code}")
    print(f"API response: {response.text}")

if __name__ == "__main__":
    test_login()
    test_search()
    test_api()
