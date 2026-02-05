"""
Test script for the Email Plugin API
Run this script to test the email sending functionality
"""

import requests
import json
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration
BASE_URL = os.getenv('BASE_URL', 'http://localhost:5000')


def test_health_check():
    """Test the health check endpoint"""
    print("Testing health check endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/")
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        return response.status_code == 200
    except Exception as e:
        print(f"Error: {e}")
        return False


def test_plugin_info():
    """Test the plugin info endpoint"""
    print("\nTesting plugin info endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/api/email/info")
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        return response.status_code == 200
    except Exception as e:
        print(f"Error: {e}")
        return False


def test_send_email(to_email, subject, body, is_html=False):
    """Test sending an email"""
    print(f"\nTesting send email endpoint...")
    print(f"To: {to_email}")
    print(f"Subject: {subject}")
    
    try:
        payload = {
            "to_email": to_email,
            "subject": subject,
            "body": body,
            "is_html": is_html
        }
        
        response = requests.post(
            f"{BASE_URL}/api/email/send",
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        return response.status_code == 200
    except Exception as e:
        print(f"Error: {e}")
        return False


def test_openplugin_manifest():
    """Test the OpenPlugin manifest endpoint"""
    print("\nTesting OpenPlugin manifest endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/api/openplugin/manifest")
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        return response.status_code == 200
    except Exception as e:
        print(f"Error: {e}")
        return False


if __name__ == "__main__":
    print("=" * 50)
    print("OpenPlugin Email Plugin - Test Script")
    print("=" * 50)
    
    # Run tests
    health_ok = test_health_check()
    info_ok = test_plugin_info()
    manifest_ok = test_openplugin_manifest()
    
    # Test email sending (optional - uncomment and provide email)
    # test_send_email(
    #     to_email="test@example.com",
    #     subject="Test Email from OpenPlugin",
    #     body="This is a test email sent from the OpenPlugin Email Plugin.",
    #     is_html=False
    # )
    
    print("\n" + "=" * 50)
    print("Test Summary:")
    print(f"Health Check: {'✓' if health_ok else '✗'}")
    print(f"Plugin Info: {'✓' if info_ok else '✗'}")
    print(f"OpenPlugin Manifest: {'✓' if manifest_ok else '✗'}")
    print("=" * 50)
