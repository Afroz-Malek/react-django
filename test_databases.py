import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'stockstar_backend.settings')
django.setup()

from django.db import connections

print("="*60)
print("Testing Database Connections")
print("="*60)

# Test default database
print("\n1. Testing 'default' database (SQLite)...")
try:
    conn = connections['default']
    with conn.cursor() as cursor:
        cursor.execute("SELECT 1")
    print(f"   ✅ SUCCESS - default database is working")
    print(f"   Database file: db.sqlite3")
except Exception as e:
    print(f"   ❌ FAILED - Error: {e}")

# Test fyers database
print("\n2. Testing 'fyers' database (SQLite)...")
try:
    conn = connections['fyers']
    with conn.cursor() as cursor:
        cursor.execute("SELECT 1")
    print(f"   ✅ SUCCESS - fyers database is working")
    print(f"   Database file: db_fyers.sqlite3")
except Exception as e:
    print(f"   ❌ FAILED - Error: {e}")

print("\n" + "="*60)
print("Test Complete!")
print("="*60)