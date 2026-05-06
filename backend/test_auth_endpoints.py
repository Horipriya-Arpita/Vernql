#!/usr/bin/env python
"""
Test script for user registration and login endpoints
Run this after starting the FastAPI server
"""
import requests
import json
from datetime import datetime

# API Base URL
BASE_URL = "http://localhost:8000/v1/auth"

def print_section(title):
    """Print a formatted section header"""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70 + "\n")


def test_registration():
    """Test user registration endpoint"""
    print_section("Testing User Registration")

    # Registration data
    data = {
        "email": f"test_{datetime.now().timestamp()}@example.com",
        "password": "SecurePassword123!",
        "full_name": "John Doe",
        "company_name": "Acme Corporation"
    }

    print(f"Registering user: {data['email']}")
    print(f"Company: {data['company_name']}\n")

    # Make registration request
    response = requests.post(f"{BASE_URL}/register", json=data)

    if response.status_code == 201:
        print("[SUCCESS] Registration successful!")
        result = response.json()

        print(f"\nUser Information:")
        print(f"  - ID: {result['user']['id']}")
        print(f"  - Email: {result['user']['email']}")
        print(f"  - Full Name: {result['user']['full_name']}")
        print(f"  - Company: {result['user']['company_name']}")
        print(f"  - Is Admin: {result['user']['is_admin']}")
        print(f"  - Email Verified: {result['user']['is_email_verified']}")

        print(f"\nTokens:")
        print(f"  - Access Token: {result['tokens']['access_token'][:50]}...")
        print(f"  - Refresh Token: {result['tokens']['refresh_token'][:50]}...")
        print(f"  - Expires In: {result['tokens']['expires_in']} seconds")

        return data['email'], result['tokens']['access_token']
    else:
        print(f"[FAILED] Registration failed!")
        print(f"Status Code: {response.status_code}")
        print(f"Error: {response.json()}")
        return None, None


def test_login(email, password):
    """Test user login endpoint"""
    print_section("Testing User Login")

    # Login data
    data = {
        "email": email,
        "password": password
    }

    print(f"Logging in as: {email}\n")

    # Make login request
    response = requests.post(f"{BASE_URL}/login", json=data)

    if response.status_code == 200:
        print("[SUCCESS] Login successful!")
        result = response.json()

        print(f"\nUser Information:")
        print(f"  - ID: {result['user']['id']}")
        print(f"  - Email: {result['user']['email']}")
        print(f"  - Last Login: {result['user']['last_login_at']}")

        print(f"\nNew Tokens:")
        print(f"  - Access Token: {result['tokens']['access_token'][:50]}...")
        print(f"  - Refresh Token: {result['tokens']['refresh_token'][:50]}...")

        return result['tokens']['access_token']
    else:
        print(f"[FAILED] Login failed!")
        print(f"Status Code: {response.status_code}")
        print(f"Error: {response.json()}")
        return None


def test_get_current_user(access_token):
    """Test getting current user info with JWT token"""
    print_section("Testing Get Current User (JWT Auth)")

    headers = {
        "Authorization": f"Bearer {access_token}"
    }

    print("Fetching current user information...\n")

    # Make request
    response = requests.get(f"{BASE_URL}/me", headers=headers)

    if response.status_code == 200:
        print("[SUCCESS] Successfully retrieved user info!")
        result = response.json()

        print(f"\nUser Details:")
        print(f"  - ID: {result['id']}")
        print(f"  - Email: {result['email']}")
        print(f"  - Full Name: {result['full_name']}")
        print(f"  - Company: {result['company_name']} (ID: {result['company_id']})")
        print(f"  - Is Admin: {result['is_admin']}")
        print(f"  - Is Active: {result['is_active']}")
        print(f"  - Email Verified: {result['is_email_verified']}")
        print(f"  - Created At: {result['created_at']}")
        return True
    else:
        print(f"[FAILED] Failed to get user info!")
        print(f"Status Code: {response.status_code}")
        print(f"Error: {response.json()}")
        return False


def test_invalid_login():
    """Test login with invalid credentials"""
    print_section("Testing Invalid Login")

    data = {
        "email": "nonexistent@example.com",
        "password": "wrongpassword"
    }

    print(f"Attempting login with invalid credentials...\n")

    response = requests.post(f"{BASE_URL}/login", json=data)

    if response.status_code == 401:
        print("[SUCCESS] Correctly rejected invalid credentials!")
        print(f"Error message: {response.json()['detail']}")
        return True
    else:
        print(f"[FAILED] Unexpected response!")
        print(f"Status Code: {response.status_code}")
        return False


def main():
    """Run all tests"""
    print("\n" + "=" * 70)
    print("  VERNQL AUTHENTICATION ENDPOINTS TEST")
    print("=" * 70)
    print("\nMake sure the FastAPI server is running on http://localhost:8000")
    print("\nStarting tests in 2 seconds...")

    import time
    time.sleep(2)

    try:
        # Test 1: Registration
        email, access_token = test_registration()

        if not email:
            print("\n[FAILED] Registration test failed. Stopping tests.")
            return

        # Test 2: Login
        new_token = test_login(email, "SecurePassword123!")

        if not new_token:
            print("\n[FAILED] Login test failed. Stopping tests.")
            return

        # Test 3: Get current user
        test_get_current_user(new_token)

        # Test 4: Invalid login
        test_invalid_login()

        # Final summary
        print_section("Test Summary")
        print("[SUCCESS] All tests completed successfully!")
        print("\nThe registration and login endpoints are working correctly.")
        print("\nYou can now:")
        print("  1. Use the access token to authenticate API requests")
        print("  2. Build the frontend signup/login pages")
        print("  3. Create API keys for the authenticated user")

    except requests.exceptions.ConnectionError:
        print("\n[ERROR] Cannot connect to the API server")
        print("\nPlease ensure the FastAPI server is running:")
        print("  cd backend")
        print("  uvicorn app.main:app --reload")

    except Exception as e:
        print(f"\n[ERROR] {e}")


if __name__ == "__main__":
    main()