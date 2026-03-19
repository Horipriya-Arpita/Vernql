#!/usr/bin/env python
"""
Database Seeding Script - Creates sample company and API key
Run this to bootstrap your database with a test API key
"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.db.seed import seed_database

if __name__ == "__main__":
    print("=" * 70)
    print("VERNQL DATABASE SEEDING")
    print("=" * 70)
    print("\nThis will create:")
    print("  - A sample company (Acme Corporation)")
    print("  - A valid API key (prefix: textsql_test_)")
    print("  - Sample schema with tables and queries")
    print("\n" + "=" * 70)

    try:
        seed_database()
        print("\n✅ SUCCESS! Copy the API key above and use it in your dashboard.")
        print("\nNext steps:")
        print("  1. Copy the API key (starts with 'textsql_test_')")
        print("  2. Open the dashboard")
        print("  3. Paste the API key in the authentication section")
        print("  4. Try uploading a schema or generating queries")
        print("=" * 70)
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        sys.exit(1)
