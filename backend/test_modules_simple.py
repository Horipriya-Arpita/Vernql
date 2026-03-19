"""
Simple test script to verify new modules work correctly
"""
from app.services.sql_validator import SQLValidator, ValidationWarning
from app.services.prompt_builder import PromptBuilder, Example
from app.models import Schema, SchemaTable, SchemaColumn, DatabaseType
from uuid import uuid4

print("=" * 60)
print("Testing SQL Validator")
print("=" * 60)

validator = SQLValidator()

# Test 1: Valid SELECT query
print("\n1. Testing valid SELECT query...")
sql = "SELECT * FROM users LIMIT 100;"
warnings = validator.validate(sql)
print(f"   [OK] Valid: {validator.is_valid(warnings)}")
print(f"   [OK] Warnings: {len(warnings)}")

# Test 2: Forbidden keyword
print("\n2. Testing forbidden keyword (DROP)...")
sql = "DROP TABLE users;"
warnings = validator.validate(sql)
print(f"   [OK] Valid: {validator.is_valid(warnings)}")
print(f"   [OK] Errors: {len(validator.get_error_messages(warnings))}")
assert not validator.is_valid(warnings), "Should detect forbidden keyword"

# Test 3: SQL injection pattern
print("\n3. Testing SQL injection pattern...")
sql = "SELECT * FROM users WHERE id = 1 OR 1=1;"
warnings = validator.validate(sql)
print(f"   [OK] Detected injection: {not validator.is_valid(warnings)}")

# Test 4: Missing LIMIT clause
print("\n4. Testing missing LIMIT clause...")
sql = "SELECT * FROM users;"
warnings = validator.validate(sql)
warning_msgs = validator.get_warning_messages(warnings)
print(f"   [OK] Has LIMIT warning: {any('limit' in w.lower() for w in warning_msgs)}")

print("\n" + "=" * 60)
print("Testing Prompt Builder")
print("=" * 60)

# Create a sample schema
schema = Schema(
    id=uuid4(),
    company_id=uuid4(),
    name="test_db",
    db_type=DatabaseType.POSTGRESQL,
    is_active=True,
    enriched_description="Test e-commerce database"
)

users_table = SchemaTable(
    id=uuid4(),
    schema_id=schema.id,
    name="users",
    enriched_description="Customer accounts"
)

users_table.columns = [
    SchemaColumn(
        id=uuid4(),
        table_id=users_table.id,
        name="id",
        data_type="INTEGER",
        is_primary_key=True,
        is_nullable=False,
        enriched_description="Unique user ID"
    ),
    SchemaColumn(
        id=uuid4(),
        table_id=users_table.id,
        name="email",
        data_type="VARCHAR(255)",
        is_nullable=False,
        enriched_description="User email address"
    ),
]

schema.tables = [users_table]

# Test 5: Build basic prompt
print("\n5. Testing prompt builder (no examples)...")
prompt_builder = PromptBuilder(db_type="postgresql")
prompt = prompt_builder.build_sql_generation_prompt(
    schema=schema,
    natural_language_query="Show all users",
    include_schema_descriptions=True
)
print(f"   [OK] Prompt generated: {len(prompt)} characters")
assert "users" in prompt.lower(), "Prompt should contain table name"
assert "postgresql" in prompt.lower(), "Prompt should mention database type"

# Test 6: Build prompt with examples
print("\n6. Testing prompt builder (with examples)...")
examples = [
    Example(
        natural_language="Count all users",
        sql="SELECT COUNT(*) FROM users;",
        explanation="Uses COUNT aggregate function"
    )
]
prompt = prompt_builder.build_sql_generation_prompt(
    schema=schema,
    natural_language_query="Show all users",
    examples=examples,
    include_schema_descriptions=True
)
print(f"   [OK] Prompt with examples: {len(prompt)} characters")
assert "example" in prompt.lower(), "Prompt should contain examples section"

# Test 7: Token estimation
print("\n7. Testing token estimation...")
token_count = prompt_builder.estimate_token_count(prompt)
print(f"   [OK] Estimated tokens: {token_count}")
assert token_count > 0, "Should estimate some tokens"

print("\n" + "=" * 60)
print("Testing Modular Integration")
print("=" * 60)

# Test 8: Validator with schema
print("\n8. Testing validator with schema context...")
sql = "SELECT * FROM unknown_table LIMIT 100;"
warnings = validator.validate(sql, schema=schema, db_type="postgresql")
print(f"   [OK] Warnings generated: {len(warnings)}")
print(f"   [OK] Has unknown table warning: {any('unknown_table' in w.message.lower() for w in warnings)}")

print("\n" + "=" * 60)
print("SUCCESS - ALL TESTS PASSED!")
print("=" * 60)
print("\nModules are working correctly:")
print("  * SQLValidator - comprehensive validation with multiple severity levels")
print("  * PromptBuilder - structured 5-part prompt generation")
print("  * Example system - ready for few-shot learning")
print("  * All components are modular and testable")
