#!/usr/bin/env python
"""
API Key Validation Script
Check if an API key is valid and view its details
"""
import sys
import os
import argparse
from datetime import datetime, timezone

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.db.database import SessionLocal
from app.core.security import verify_api_key, hash_api_key
from app.models import APIKey, Company


def validate_key(api_key: str) -> dict:
    """Validate an API key and return details"""
    db = SessionLocal()

    try:
        # Hash the key
        key_hash = hash_api_key(api_key)

        # Try to verify the key
        verification = verify_api_key(db, api_key)

        if verification:
            company, key_obj = verification

            result = {
                "valid": True,
                "api_key_id": str(key_obj.id),
                "api_key_name": key_obj.name or "(unnamed)",
                "is_active": key_obj.is_active,
                "created_at": key_obj.created_at.isoformat(),
                "expires_at": key_obj.expires_at.isoformat() if key_obj.expires_at else "Never",
                "last_used_at": key_obj.last_used_at.isoformat() if key_obj.last_used_at else "Never used",
                "is_expired": key_obj.is_expired(),
                "rate_limit_per_minute": key_obj.rate_limit_per_minute,
                "rate_limit_per_hour": key_obj.rate_limit_per_hour,
                "company_id": str(company.id),
                "company_name": company.name,
                "company_is_active": company.is_active,
            }
        else:
            # Check if key exists but is invalid
            key_obj = db.query(APIKey).filter(APIKey.key_hash == key_hash).first()

            if key_obj:
                company = db.query(Company).filter(Company.id == key_obj.company_id).first()

                reasons = []
                if not key_obj.is_active:
                    reasons.append("API key is revoked/inactive")
                if key_obj.is_expired():
                    reasons.append(f"API key expired at {key_obj.expires_at.isoformat()}")
                if company and not company.is_active:
                    reasons.append("Associated company is inactive")

                result = {
                    "valid": False,
                    "exists": True,
                    "reasons": reasons,
                    "api_key_id": str(key_obj.id),
                    "api_key_name": key_obj.name or "(unnamed)",
                    "is_active": key_obj.is_active,
                    "is_expired": key_obj.is_expired(),
                    "company_name": company.name if company else "Unknown",
                }
            else:
                result = {
                    "valid": False,
                    "exists": False,
                    "reasons": ["API key not found in database"],
                }

        return result

    finally:
        db.close()


def format_result(result: dict, api_key: str) -> str:
    """Format validation result for display"""
    output = []

    output.append("=" * 70)
    output.append("API KEY VALIDATION REPORT")
    output.append("=" * 70)

    # Show key (partially masked)
    masked_key = api_key[:15] + "..." + api_key[-8:] if len(api_key) > 25 else api_key
    output.append(f"\n🔑 API Key: {masked_key}")

    if result["valid"]:
        output.append("\n✅ Status: VALID - This API key is working correctly!")

        output.append(f"\n📋 API Key Details:")
        output.append(f"  • ID: {result['api_key_id']}")
        output.append(f"  • Name: {result['api_key_name']}")
        output.append(f"  • Created: {result['created_at']}")
        output.append(f"  • Expires: {result['expires_at']}")
        output.append(f"  • Last Used: {result['last_used_at']}")

        output.append(f"\n🏢 Company Details:")
        output.append(f"  • ID: {result['company_id']}")
        output.append(f"  • Name: {result['company_name']}")
        output.append(f"  • Active: {'Yes' if result['company_is_active'] else 'No'}")

        output.append(f"\n⚡ Rate Limits:")
        output.append(f"  • Per Minute: {result['rate_limit_per_minute'] or 'Default (60)'}")
        output.append(f"  • Per Hour: {result['rate_limit_per_hour'] or 'Default (1000)'}")

        output.append("\n✨ You can use this API key to make API requests!")

    else:
        output.append("\n❌ Status: INVALID - This API key cannot be used")

        if result["exists"]:
            output.append(f"\n⚠️  The key exists in the database but is not valid:")
            for reason in result["reasons"]:
                output.append(f"  • {reason}")

            output.append(f"\n📋 API Key Details:")
            output.append(f"  • ID: {result['api_key_id']}")
            output.append(f"  • Name: {result['api_key_name']}")
            output.append(f"  • Active: {'Yes' if result['is_active'] else 'No'}")
            output.append(f"  • Expired: {'Yes' if result['is_expired'] else 'No'}")
            output.append(f"  • Company: {result['company_name']}")

            output.append("\n💡 Possible solutions:")
            if "revoked" in str(result["reasons"]):
                output.append("  • Generate a new API key")
            if "expired" in str(result["reasons"]):
                output.append("  • Generate a new API key with a later expiration date")
            if "company is inactive" in str(result["reasons"]):
                output.append("  • Contact support to reactivate the company")
        else:
            output.append("\n🔍 The key was not found in the database")
            output.append("\n💡 Possible causes:")
            output.append("  • The key was never created (may be a fake/demo key)")
            output.append("  • You're using the wrong database")
            output.append("  • The key was deleted from the database")
            output.append("\n💡 Solution:")
            output.append("  • Run 'python seed_and_show_key.py' to create a valid API key")
            output.append("  • Or use the API to create a new key: POST /v1/auth/keys")

    output.append("=" * 70)

    return "\n".join(output)


def main():
    parser = argparse.ArgumentParser(
        description="Validate a TextSQL API key",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Validate an API key
  python validate_api_key.py textsql_test_abc123xyz789

  # Or provide via argument
  python validate_api_key.py -k textsql_test_abc123xyz789
        """
    )

    parser.add_argument(
        "api_key",
        nargs="?",
        help="API key to validate"
    )

    parser.add_argument(
        "-k", "--key",
        help="API key to validate (alternative to positional argument)"
    )

    args = parser.parse_args()

    # Get API key
    api_key = args.api_key or args.key

    if not api_key:
        print("❌ Error: Please provide an API key to validate")
        parser.print_help()
        sys.exit(1)

    # Validate the key
    try:
        result = validate_key(api_key)
        print(format_result(result, api_key))

        # Exit with appropriate code
        sys.exit(0 if result["valid"] else 1)

    except Exception as e:
        print(f"❌ Error validating API key: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
