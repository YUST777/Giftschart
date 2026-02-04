#!/usr/bin/env python3
"""
Quick Test for Supabase Backup System

Tests all components without actually syncing data.
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.supabase_client import (
    SUPABASE_ENABLED,
    PSYCOPG2_AVAILABLE,
    test_connection,
    init_tables
)

def main():
    print("=" * 60)
    print("🧪 Supabase Backup System Test")
    print("=" * 60)
    print()
    
    # Test 1: Check configuration
    print("1️⃣  Checking Supabase configuration...")
    if SUPABASE_ENABLED:
        print("   ✅ Supabase configured in .env")
    else:
        print("   ❌ Supabase NOT configured")
        print("   💡 Add Supabase credentials to .env file")
        return 1
    
    # Test 2: Check psycopg2
    print()
    print("2️⃣  Checking psycopg2 installation...")
    if PSYCOPG2_AVAILABLE:
        print("   ✅ psycopg2 installed")
    else:
        print("   ❌ psycopg2 NOT installed")
        print("   💡 Run: pip install psycopg2-binary")
        return 1
    
    # Test 3: Test connection
    print()
    print("3️⃣  Testing Supabase connection...")
    if test_connection():
        print("   ✅ Connection successful")
    else:
        print("   ❌ Connection failed")
        print("   💡 Check your password and network")
        return 1
    
    # Test 4: Initialize tables
    print()
    print("4️⃣  Initializing Supabase tables...")
    if init_tables():
        print("   ✅ Tables created/verified")
    else:
        print("   ❌ Table creation failed")
        return 1
    
    # Test 5: Check SQLite databases
    print()
    print("5️⃣  Checking SQLite databases...")
    from config.paths import PREMIUM_DB_FILE, USER_REQUESTS_DB_FILE
    
    if os.path.exists(PREMIUM_DB_FILE):
        size = os.path.getsize(PREMIUM_DB_FILE) / 1024
        print(f"   ✅ premium_system.db found ({size:.1f} KB)")
    else:
        print("   ⚠️  premium_system.db not found (will be created)")
    
    if os.path.exists(USER_REQUESTS_DB_FILE):
        size = os.path.getsize(USER_REQUESTS_DB_FILE) / 1024
        print(f"   ✅ user_requests.db found ({size:.1f} KB)")
    else:
        print("   ⚠️  user_requests.db not found (will be created)")
    
    # Summary
    print()
    print("=" * 60)
    print("🎉 All Tests Passed!")
    print("=" * 60)
    print()
    print("Next steps:")
    print("  1. Run initial backup:")
    print("     python3 schedulers/supabase_backup_sync.py")
    print()
    print("  2. Start automatic scheduler:")
    print("     nohup python3 schedulers/run_supabase_backup.py > supabase_backup.log 2>&1 &")
    print()
    
    return 0

if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n⚠️  Test interrupted")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Test error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
