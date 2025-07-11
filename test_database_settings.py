#!/usr/bin/env python3
"""
Test script to verify database settings integration
"""

import json
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from core.settings_portable import get_settings
from database.connection import DatabaseConnection

def test_database_settings():
    """Test that database settings are properly loaded from settings.json"""
    
    print("Testing Database Settings Integration")
    print("=" * 50)
    
    # Test 1: Verify settings are loaded
    settings = get_settings()
    db_settings = settings.get("database")
    
    print(f"1. Database settings from settings.json:")
    print(f"   Server: {db_settings.get('server')}")
    print(f"   Database: {db_settings.get('database')}")
    print(f"   Username: {db_settings.get('username')}")
    print(f"   Password: {'*' * len(db_settings.get('password', ''))}")
    
    # Test 2: Verify DatabaseConnection uses settings
    db_conn = DatabaseConnection()
    
    print(f"\n2. DatabaseConnection instance values:")
    print(f"   Server: {db_conn.server}")
    print(f"   Database: {db_conn.database}")
    print(f"   Username: {db_conn.username}")
    print(f"   Password: {'*' * len(db_conn.password)}")
    
    # Test 3: Verify settings match
    settings_match = (
        db_conn.server == db_settings.get('server') and
        db_conn.database == db_settings.get('database') and
        db_conn.username == db_settings.get('username') and
        db_conn.password == db_settings.get('password')
    )
    
    print(f"\n3. Settings match: {settings_match}")
    
    # Test 4: Test connection (optional - only if database is available)
    try:
        connection_result = db_conn.test_connection()
        print(f"\n4. Database connection test:")
        print(f"   Connected: {connection_result.get('connected')}")
        if connection_result.get('connected'):
            print(f"   Server: {connection_result.get('server')}")
            print(f"   Database: {connection_result.get('database')}")
        else:
            print(f"   Error: {connection_result.get('error')}")
    except Exception as e:
        print(f"\n4. Database connection test failed: {e}")
    
    # Test 5: Test with custom parameters (should override settings)
    custom_db = DatabaseConnection(server="custom.server.com", database="CustomDB")
    print(f"\n5. Custom parameters override test:")
    print(f"   Custom server: {custom_db.server}")
    print(f"   Custom database: {custom_db.database}")
    print(f"   Settings username: {custom_db.username}")  # Should still use settings
    print(f"   Settings password: {'*' * len(custom_db.password)}")  # Should still use settings
    
    print("\n" + "=" * 50)
    print("Database settings integration test completed!")
    
    return settings_match

if __name__ == "__main__":
    success = test_database_settings()
    sys.exit(0 if success else 1)
