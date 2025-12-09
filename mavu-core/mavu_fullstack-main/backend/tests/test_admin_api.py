#!/usr/bin/env python3
"""Quick test script for admin API endpoints."""
import sys
from fastapi.testclient import TestClient
from main import app

# Create test client
client = TestClient(app)

def test_admin_stats():
    """Test admin stats endpoint."""
    print("Testing /admin/stats...")
    response = client.get(
        "/admin/stats",
        headers={"X-User-Id": "admin@mavuai.com"}
    )
    print(f"  Status: {response.status_code}")
    if response.status_code == 200:
        print(f"  Response: {response.json()}")
        return True
    else:
        print(f"  Error: {response.text}")
        return False

def test_list_users():
    """Test list users endpoint."""
    print("\nTesting /admin/users...")
    response = client.get(
        "/admin/users",
        headers={"X-User-Id": "admin@mavuai.com"}
    )
    print(f"  Status: {response.status_code}")
    if response.status_code == 200:
        users = response.json()
        print(f"  Found {len(users)} user(s)")
        for user in users:
            print(f"    - {user['user_id']} (Admin: {user['is_admin']})")
        return True
    else:
        print(f"  Error: {response.text}")
        return False

def test_get_user():
    """Test get specific user endpoint."""
    print("\nTesting /admin/users/admin@mavuai.com...")
    response = client.get(
        "/admin/users/admin@mavuai.com",
        headers={"X-User-Id": "admin@mavuai.com"}
    )
    print(f"  Status: {response.status_code}")
    if response.status_code == 200:
        user = response.json()
        print(f"  User: {user['user_id']}")
        print(f"  Email: {user['email']}")
        print(f"  Admin: {user['is_admin']}")
        return True
    else:
        print(f"  Error: {response.text}")
        return False

def main():
    """Run all tests."""
    print("=" * 60)
    print("Admin API Tests")
    print("=" * 60)

    tests = [
        test_admin_stats,
        test_list_users,
        test_get_user,
    ]

    passed = 0
    failed = 0

    for test in tests:
        try:
            if test():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"  Exception: {e}")
            failed += 1

    print("\n" + "=" * 60)
    print(f"Results: {passed} passed, {failed} failed")
    print("=" * 60)

    return 0 if failed == 0 else 1

if __name__ == "__main__":
    sys.exit(main())
