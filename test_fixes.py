#!/usr/bin/env python3
"""
Test script for IronLifter gym management fixes
Tests security, validation, performance, and error handling improvements
"""

import requests
import json
import os
from datetime import datetime

class IronLifterTester:
    def __init__(self, base_url="http://127.0.0.1:5000"):
        self.base_url = base_url
        self.session = requests.Session()
        self.test_results = []
        
    def log_test(self, test_name, passed, details=""):
        """Log test result"""
        status = "PASS" if passed else "FAIL"
        result = f"[{status}] {test_name}: {details}"
        self.test_results.append(result)
        print(result)
        
    def test_login(self):
        """Test login functionality"""
        print("\n=== Testing Login ===")
        try:
            # Test login page loads
            response = self.session.get(f"{self.base_url}/login")
            self.log_test("Login page loads", response.status_code == 200, f"Status: {response.status_code}")
            
            # Test login with admin credentials
            login_data = {
                'username': 'admin',
                'password': 'change_this_password_immediately',
                'csrf_token': self.get_csrf_token(response.text)
            }
            
            response = self.session.post(f"{self.base_url}/login", data=login_data)
            self.log_test("Admin login successful", response.status_code == 302, f"Status: {response.status_code}")
            
        except Exception as e:
            self.log_test("Login test", False, f"Exception: {str(e)}")
    
    def get_csrf_token(self, html_content):
        """Extract CSRF token from HTML"""
        import re
        pattern = r'name="csrf_token" type="hidden" value="([^"]+)"'
        match = re.search(pattern, html_content)
        return match.group(1) if match else ""
    
    def test_member_validation(self):
        """Test member creation validation"""
        print("\n=== Testing Member Validation ===")
        try:
            # Get member creation page
            response = self.session.get(f"{self.base_url}/members/new")
            self.log_test("Member form loads", response.status_code == 200)
            
            csrf_token = self.get_csrf_token(response.text)
            
            # Test invalid email
            invalid_data = {
                'name': 'Test User',
                'phone': '1234567890',
                'email': 'invalid-email',
                'date_of_birth': '1990-01-01',
                'join_date': datetime.now().strftime('%Y-%m-%d'),
                'plan_id': '1',
                'csrf_token': csrf_token
            }
            
            response = self.session.post(f"{self.base_url}/members/new", data=invalid_data)
            self.log_test("Invalid email rejected", "Validation errors" in response.text or response.status_code != 302)
            
            # Test XSS attempt
            xss_data = {
                'name': '<script>alert("xss")</script>',
                'phone': '1234567890',
                'email': 'test@example.com',
                'date_of_birth': '1990-01-01',
                'join_date': datetime.now().strftime('%Y-%m-%d'),
                'plan_id': '1',
                'csrf_token': csrf_token
            }
            
            response = self.session.post(f"{self.base_url}/members/new", data=xss_data)
            self.log_test("XSS attempt sanitized", '<script>' not in response.text)
            
        except Exception as e:
            self.log_test("Member validation test", False, f"Exception: {str(e)}")
    
    def test_search_validation(self):
        """Test search functionality with validation"""
        print("\n=== Testing Search Validation ===")
        try:
            # Test SQL injection attempt
            malicious_search = "1' OR '1'='1"
            response = self.session.get(f"{self.base_url}/members/live_search", params={'q': malicious_search})
            self.log_test("SQL injection blocked", response.status_code == 200 and "error" not in response.text.lower())
            
            # Test XSS in search
            xss_search = "<script>alert('xss')</script>"
            response = self.session.get(f"{self.base_url}/members/live_search", params={'q': xss_search})
            self.log_test("Search XSS sanitized", "<script>" not in response.text)
            
            # Test short search (should be rejected)
            short_search = "a"
            response = self.session.get(f"{self.base_url}/members/live_search", params={'q': short_search})
            self.log_test("Short search rejected", "members" in response.text and len(response.text) < 1000)
            
        except Exception as e:
            self.log_test("Search validation test", False, f"Exception: {str(e)}")
    
    def test_file_upload_security(self):
        """Test file upload security"""
        print("\n=== Testing File Upload Security ===")
        try:
            # Create a fake image file for testing
            fake_image_content = b"Not really an image content"
            
            files = {'photo': ('test.txt', fake_image_content, 'text/plain')}
            data = {
                'name': 'Test User',
                'phone': '1234567890',
                'email': 'test@example.com',
                'date_of_birth': '1990-01-01',
                'join_date': datetime.now().strftime('%Y-%m-%d'),
                'plan_id': '1'
            }
            
            # Get CSRF token first
            response = self.session.get(f"{self.base_url}/members/new")
            csrf_token = self.get_csrf_token(response.text)
            data['csrf_token'] = csrf_token
            
            response = self.session.post(f"{self.base_url}/members/new", files=files, data=data)
            self.log_test("Invalid file type rejected", "File type not allowed" in response.text or response.status_code != 302)
            
        except Exception as e:
            self.log_test("File upload security test", False, f"Exception: {str(e)}")
    
    def test_api_security(self):
        """Test API endpoint security"""
        print("\n=== Testing API Security ===")
        try:
            # Test kiosk endpoint without token
            checkin_data = {'member_id': '12345'}
            response = requests.post(f"{self.base_url}/api/checkin", json=checkin_data)
            self.log_test("API blocks unauthorized access", response.status_code == 401)
            
            # Test with wrong token
            headers = {'X-Kiosk-Secret': 'wrong_token'}
            response = requests.post(f"{self.base_url}/api/checkin", json=checkin_data, headers=headers)
            self.log_test("API rejects wrong token", response.status_code == 401)
            
        except Exception as e:
            self.log_test("API security test", False, f"Exception: {str(e)}")
    
    def test_error_handling(self):
        """Test error handling"""
        print("\n=== Testing Error Handling ===")
        try:
            # Test 404 error
            response = requests.get(f"{self.base_url}/nonexistent-page")
            self.log_test("404 error handled gracefully", response.status_code == 404)
            
            # Test accessing protected route without login
            response = requests.get(f"{self.base_url}/members")
            self.log_test("Protected route redirects", response.status_code == 302 or response.status_code == 401)
            
        except Exception as e:
            self.log_test("Error handling test", False, f"Exception: {str(e)}")
    
    def run_all_tests(self):
        """Run all tests"""
        print("Starting IronLifter Security and Validation Tests...")
        print("=" * 50)
        
        self.test_login()
        self.test_member_validation()
        self.test_search_validation()
        self.test_file_upload_security()
        self.test_api_security()
        self.test_error_handling()
        
        print("\n" + "=" * 50)
        print("TEST SUMMARY")
        print("=" * 50)
        
        passed = len([r for r in self.test_results if "[PASS]" in r])
        failed = len([r for r in self.test_results if "[FAIL]" in r])
        
        print(f"Total Tests: {len(self.test_results)}")
        print(f"Passed: {passed}")
        print(f"Failed: {failed}")
        
        if failed > 0:
            print("\nFailed Tests:")
            for result in self.test_results:
                if "[FAIL]" in result:
                    print(f"  - {result}")
        
        return failed == 0

if __name__ == "__main__":
    tester = IronLifterTester()
    success = tester.run_all_tests()
    
    print(f"\nOverall Result: {'SUCCESS' if success else 'FAILURE'}")
    exit(0 if success else 1)
