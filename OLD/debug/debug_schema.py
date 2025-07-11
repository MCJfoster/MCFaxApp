"""
Debug script to check actual database schema
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from database import DatabaseConnection, DatabaseSchema

def main():
    db = DatabaseConnection()
    schema = DatabaseSchema(db)
    
    # Get table info for Contacts
    print("Contacts table structure:")
    contacts_info = schema.get_table_info('Contacts')
    for i, col in enumerate(contacts_info):
        print(f"  {i}: {col['column_name']} ({col['data_type']})")
    
    print("\nFaxJobs table structure:")
    faxjobs_info = schema.get_table_info('FaxJobs')
    for i, col in enumerate(faxjobs_info):
        print(f"  {i}: {col['column_name']} ({col['data_type']})")

if __name__ == "__main__":
    main()
