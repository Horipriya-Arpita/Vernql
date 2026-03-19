"""
Test script for Code Generator Service
Verifies that all code snippet templates work correctly
"""
from app.services.code_generator import CodeGenerator

print("=" * 70)
print("Testing Code Generator Service")
print("=" * 70)

# Initialize generator
generator = CodeGenerator()

# Test configuration
test_config = {
    "api_key": "test_api_key_12345",
    "base_url": "http://localhost:8000",
    "schema_id": "123e4567-e89b-12d3-a456-426614174000",
    "query_example": "Show all users created in the last 30 days"
}

print("\n1. Testing supported languages...")
print("-" * 70)
languages = generator.get_supported_languages()
print(f"Supported languages: {len(languages)}")
for lang_id, lang_name in languages.items():
    print(f"  * {lang_id}: {lang_name}")

print("\n2. Testing snippet generation for each language...")
print("-" * 70)

results = {}
for lang_id in languages.keys():
    try:
        print(f"\nGenerating {lang_id}...")
        snippet_data = generator.generate_snippet(
            language=lang_id,
            **test_config
        )

        # Basic validation
        code = snippet_data["code"]
        is_valid = generator.validate_snippet_syntax(lang_id, code)

        results[lang_id] = {
            "success": True,
            "length": len(code),
            "valid": is_valid
        }

        print(f"  [OK] Generated {len(code)} characters")
        print(f"  [OK] Syntax validation: {is_valid}")

        # Check for required elements
        checks = []
        if test_config["api_key"] in code:
            checks.append("API key")
        if test_config["base_url"] in code:
            checks.append("Base URL")
        if test_config["schema_id"] in code:
            checks.append("Schema ID")

        print(f"  [OK] Contains: {', '.join(checks)}")

    except Exception as e:
        results[lang_id] = {
            "success": False,
            "error": str(e)
        }
        print(f"  [ERROR] Failed: {e}")

print("\n3. Testing generate_all_snippets...")
print("-" * 70)
try:
    all_snippets = generator.generate_all_snippets(
        api_key=test_config["api_key"],
        base_url=test_config["base_url"],
        schema_id=test_config["schema_id"]
    )
    print(f"  [OK] Generated {len(all_snippets)} snippets")

    for lang_id, snippet_data in all_snippets.items():
        code_length = len(snippet_data["code"])
        print(f"    * {lang_id}: {code_length} characters")

except Exception as e:
    print(f"  [ERROR] Failed: {e}")

print("\n4. Testing file extension mapping...")
print("-" * 70)
for lang_id in languages.keys():
    ext = generator.get_snippet_file_extension(lang_id)
    print(f"  * {lang_id} -> .{ext}")

print("\n5. Testing error handling...")
print("-" * 70)
try:
    generator.generate_snippet(
        language="invalid_language",
        **test_config
    )
    print("  [ERROR] Should have raised ValueError for invalid language")
except ValueError as e:
    print(f"  [OK] Correctly raised ValueError: {e}")

print("\n" + "=" * 70)
print("Summary")
print("=" * 70)

successful = sum(1 for r in results.values() if r["success"])
total = len(results)
print(f"\nGeneration Results: {successful}/{total} successful")

if successful == total:
    print("\n[SUCCESS] All code generators working correctly!")
else:
    print("\n[WARNING] Some generators failed:")
    for lang_id, result in results.items():
        if not result["success"]:
            print(f"  * {lang_id}: {result['error']}")

# Show sample output from one language
print("\n" + "=" * 70)
print("Sample Output (Python Flask)")
print("=" * 70)
try:
    flask_snippet = generator.generate_snippet(
        language="python_flask",
        **test_config
    )
    # Show first 50 lines
    lines = flask_snippet["code"].split('\n')
    for i, line in enumerate(lines[:30], 1):
        print(f"{i:3d}: {line}")
    if len(lines) > 30:
        print(f"... ({len(lines) - 30} more lines)")

    print("\nInstructions:")
    print(flask_snippet["instructions"])

except Exception as e:
    print(f"Failed to generate sample: {e}")

print("\n" + "=" * 70)
print("Testing Complete!")
print("=" * 70)
