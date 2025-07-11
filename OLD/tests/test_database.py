"""
Test script for Database Module (1.4)
Tests database connection, schema creation, and basic operations
"""

import sys
import os
import logging

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from database import DatabaseConnection, DatabaseSchema, Contact, ContactRepository

def setup_logging():
    """Setup basic logging"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

def test_database_connection():
    """Test database connection"""
    print("=" * 50)
    print("Testing Database Connection (1.4)")
    print("=" * 50)
    
    # Create database connection
    db = DatabaseConnection()
    
    # Test connection
    print("Testing database connection...")
    connection_info = db.test_connection()
    
    if connection_info['connected']:
        print("✓ Database connection successful!")
        print(f"  Server: {connection_info['server']}")
        print(f"  Database: {connection_info['database']}")
        print(f"  Version: {connection_info['version'][:50]}...")
        print(f"  Server Time: {connection_info['server_time']}")
    else:
        print("✗ Database connection failed!")
        print(f"  Error: {connection_info['error']}")
        return False
    
    return True

def test_database_schema():
    """Test database schema creation"""
    print("\n" + "=" * 50)
    print("Testing Database Schema Creation")
    print("=" * 50)
    
    db = DatabaseConnection()
    schema = DatabaseSchema(db)
    
    # Check current schema status
    print("Checking current schema status...")
    status = schema.get_schema_status()
    
    if 'error' in status:
        print(f"✗ Error checking schema: {status['error']}")
        return False
    
    print(f"Current schema status:")
    for table, exists in status['tables_exist'].items():
        print(f"  {table}: {'✓' if exists else '✗'}")
    
    # Create schema if needed
    if not status['all_tables_exist']:
        print("\nCreating database schema...")
        if schema.create_schema():
            print("✓ Database schema created successfully!")
        else:
            print("✗ Failed to create database schema!")
            return False
    else:
        print("✓ All tables already exist!")
    
    # Verify schema after creation
    print("\nVerifying schema...")
    final_status = schema.get_schema_status()
    
    if final_status['all_tables_exist']:
        print("✓ Schema verification successful!")
        print(f"  Total contacts: {final_status['total_contacts']}")
        print(f"  Total fax jobs: {final_status['total_fax_jobs']}")
        print(f"  Total history records: {final_status['total_history_records']}")
    else:
        print("✗ Schema verification failed!")
        return False
    
    return True

def test_contact_operations():
    """Test contact CRUD operations"""
    print("\n" + "=" * 50)
    print("Testing Contact Operations (1.5)")
    print("=" * 50)
    
    db = DatabaseConnection()
    contact_repo = ContactRepository(db)
    
    # Create test contact
    print("Creating test contact...")
    test_contact = Contact(
        name="Test Contact",
        fax_number="555-123-4567",
        organization="Test Organization",
        phone_number="555-987-6543",
        email="test@example.com",
        notes="This is a test contact"
    )
    
    try:
        contact_id = contact_repo.create(test_contact)
        if contact_id:
            print(f"✓ Contact created successfully! ID: {contact_id}")
        else:
            print("✗ Failed to create contact!")
            return False
    except Exception as e:
        print(f"✗ Error creating contact: {e}")
        return False
    
    # Retrieve contact
    print("Retrieving contact...")
    try:
        retrieved_contact = contact_repo.get_by_id(contact_id)
        if retrieved_contact and retrieved_contact.name == "Test Contact":
            print("✓ Contact retrieved successfully!")
            print(f"  Name: {retrieved_contact.name}")
            print(f"  Fax: {retrieved_contact.fax_number}")
            print(f"  Organization: {retrieved_contact.organization}")
        else:
            print("✗ Failed to retrieve contact!")
            return False
    except Exception as e:
        print(f"✗ Error retrieving contact: {e}")
        return False
    
    # Update contact
    print("Updating contact...")
    try:
        retrieved_contact.notes = "Updated test contact"
        if contact_repo.update(retrieved_contact):
            print("✓ Contact updated successfully!")
        else:
            print("✗ Failed to update contact!")
            return False
    except Exception as e:
        print(f"✗ Error updating contact: {e}")
        return False
    
    # Search contacts
    print("Searching contacts...")
    try:
        search_results = contact_repo.search("Test")
        if search_results and len(search_results) > 0:
            print(f"✓ Search successful! Found {len(search_results)} contact(s)")
        else:
            print("✗ Search failed or no results!")
            return False
    except Exception as e:
        print(f"✗ Error searching contacts: {e}")
        return False
    
    # Clean up - delete test contact
    print("Cleaning up test contact...")
    try:
        if contact_repo.delete(contact_id):
            print("✓ Test contact deleted successfully!")
        else:
            print("✗ Failed to delete test contact!")
    except Exception as e:
        print(f"✗ Error deleting contact: {e}")
    
    return True

def main():
    """Main test function"""
    setup_logging()
    
    print("MCFax Application - Database Module Test")
    print("Testing Core Components 1.4 and 1.5")
    print()
    
    # Test database connection
    if not test_database_connection():
        print("\n❌ Database connection test failed!")
        return False
    
    # Test database schema
    if not test_database_schema():
        print("\n❌ Database schema test failed!")
        return False
    
    # Test contact operations
    if not test_contact_operations():
        print("\n❌ Contact operations test failed!")
        return False
    
    print("\n" + "=" * 50)
    print("🎉 All Database Module tests passed!")
    print("✓ Database Module (1.4) - Working")
    print("✓ Contact Management (1.5) - Working")
    print("=" * 50)
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
