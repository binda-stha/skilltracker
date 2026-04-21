#!/usr/bin/env python
"""
Test Flask Routes
"""

import requests

def test_routes():
    base_url = 'http://localhost:5000'

    print("🧪 Testing Flask Routes...")

    try:
        # Test login page
        response = requests.get(f'{base_url}/login', timeout=5)
        print(f"✅ Login page: {response.status_code}")

        # Test sorted-skills route (should redirect to login)
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        response = requests.get(f'{base_url}/sorted-skills', headers=headers, timeout=5, allow_redirects=False)
        print(f"🔄 Sorted skills route: {response.status_code}")
        if response.status_code == 302:
            location = response.headers.get('Location', 'Unknown')
            print(f"   Redirects to: {location}")
        elif response.status_code == 404:
            print(f"   404 Error - Route not found!")
            print(f"   Response: {response.text[:200]}...")

        # Test skill-recommendations route (should redirect to login)
        response = requests.get(f'{base_url}/skill-recommendations', headers=headers, timeout=5, allow_redirects=False)
        print(f"🔄 Skill recommendations route: {response.status_code}")
        if response.status_code == 302:
            location = response.headers.get('Location', 'Unknown')
            print(f"   Redirects to: {location}")
        elif response.status_code == 404:
            print(f"   404 Error - Route not found!")
            print(f"   Response: {response.text[:200]}...")

        print("✅ Route testing completed!")

    except requests.exceptions.RequestException as e:
        print(f"❌ Request error: {e}")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == '__main__':
    test_routes()