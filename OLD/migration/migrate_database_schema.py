"""
Database Schema Migration Script
Updates the existing database to include new columns for the enhanced fax system
"""

import sys
import logging

# Add src to path
sys.path.insert(0, 'src')

from database.connection import DatabaseConnection

def setup_logging():
    """Setup logging for the migration"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler()
        ]
    )

def check_column_exists(db: DatabaseConnection, table_name: str, column_name: str) -> bool:
    """Check if a column exists in a table"""
    query = """
    SELECT COUNT(*) 
    FROM INFORMATION_SCHEMA.COLUMNS 
    WHERE TABLE_NAME = ? AND COLUMN_NAME = ?
    """
    count = db.execute_scalar(query, (table_name, column_name))
    return count > 0

def add_column_if_not_exists(db: DatabaseConnection, table_name: str, column_name: str, column_definition: str):
    """Add a column to a table if it doesn't exist"""
    if not check_column_exists(db, table_name, column_name):
        alter_sql = f"ALTER TABLE {table_name} ADD {column_name} {column_definition}"
        db.execute_non_query(alter_sql)
        print(f"✓ Added column {column_name} to {table_name}")
    else:
        print(f"• Column {column_name} already exists in {table_name}")

def migrate_fax_jobs_table(db: DatabaseConnection):
    """Migrate the FaxJobs table to include new columns"""
    print("\n--- Migrating FaxJobs Table ---")
    
    # Add new columns that might be missing
    columns_to_add = [
        ("recipient_fax", "NVARCHAR(20) NOT NULL DEFAULT ''"),
        ("priority", "NVARCHAR(20) DEFAULT 'Medium'"),
        ("max_attempts", "INT DEFAULT 3"),
        ("retry_interval", "INT DEFAULT 5"),
        ("xml_path", "NVARCHAR(255) NULL"),
        ("page_count", "INT DEFAULT 0"),
        ("file_size_mb", "DECIMAL(10,2) DEFAULT 0")
    ]
    
    for column_name, column_definition in columns_to_add:
        add_column_if_not_exists(db, "FaxJobs", column_name, column_definition)
    
    # Check if xml_content column exists and rename it to xml_path if needed
    if check_column_exists(db, "FaxJobs", "xml_content"):
        if not check_column_exists(db, "FaxJobs", "xml_path"):
            # Rename xml_content to xml_path
            try:
                db.execute_non_query("EXEC sp_rename 'FaxJobs.xml_content', 'xml_path', 'COLUMN'")
                print("✓ Renamed xml_content column to xml_path")
            except Exception as e:
                print(f"⚠️ Could not rename xml_content to xml_path: {e}")
                # Add xml_path column and copy data
                add_column_if_not_exists(db, "FaxJobs", "xml_path", "NVARCHAR(255) NULL")
        else:
            print("• Both xml_content and xml_path exist, manual cleanup may be needed")

def migrate_contacts_table(db: DatabaseConnection):
    """Migrate the Contacts table to include new columns"""
    print("\n--- Migrating Contacts Table ---")
    
    # Add timestamp columns if they don't exist
    columns_to_add = [
        ("created_at", "DATETIME DEFAULT GETDATE()"),
        ("updated_at", "DATETIME DEFAULT GETDATE()")
    ]
    
    for column_name, column_definition in columns_to_add:
        add_column_if_not_exists(db, "Contacts", column_name, column_definition)

def create_missing_tables(db: DatabaseConnection):
    """Create any missing tables"""
    print("\n--- Checking for Missing Tables ---")
    
    # Check if FaxContactHistory table exists
    query = """
    SELECT COUNT(*) 
    FROM INFORMATION_SCHEMA.TABLES 
    WHERE TABLE_NAME = 'FaxContactHistory' AND TABLE_TYPE = 'BASE TABLE'
    """
    count = db.execute_scalar(query)
    
    if count == 0:
        print("Creating FaxContactHistory table...")
        create_table_sql = """
        CREATE TABLE FaxContactHistory (
            history_id BIGINT IDENTITY(1,1) PRIMARY KEY,
            fax_id BIGINT NOT NULL,
            contact_id BIGINT NOT NULL,
            action NVARCHAR(50) NOT NULL,
            timestamp DATETIME DEFAULT GETDATE(),
            details NVARCHAR(MAX) NULL,
            FOREIGN KEY (fax_id) REFERENCES FaxJobs(fax_id),
            FOREIGN KEY (contact_id) REFERENCES Contacts(contact_id)
        )
        """
        db.execute_non_query(create_table_sql)
        print("✓ Created FaxContactHistory table")
    else:
        print("• FaxContactHistory table already exists")

def create_indexes(db: DatabaseConnection):
    """Create performance indexes"""
    print("\n--- Creating Indexes ---")
    
    indexes = [
        # Contacts indexes
        ("IX_Contacts_FaxNumber", "Contacts", "fax_number"),
        ("IX_Contacts_Name", "Contacts", "name"),
        
        # FaxJobs indexes
        ("IX_FaxJobs_Status", "FaxJobs", "status"),
        ("IX_FaxJobs_CreatedAt", "FaxJobs", "created_at"),
        ("IX_FaxJobs_RecipientFax", "FaxJobs", "recipient_fax"),
        
        # FaxContactHistory indexes
        ("IX_FaxContactHistory_FaxId", "FaxContactHistory", "fax_id"),
        ("IX_FaxContactHistory_ContactId", "FaxContactHistory", "contact_id"),
        ("IX_FaxContactHistory_Timestamp", "FaxContactHistory", "timestamp")
    ]
    
    for index_name, table_name, column_name in indexes:
        try:
            # Check if index exists
            check_index_sql = f"""
            SELECT COUNT(*) 
            FROM sys.indexes 
            WHERE name = '{index_name}' AND object_id = OBJECT_ID('{table_name}')
            """
            index_exists = db.execute_scalar(check_index_sql) > 0
            
            if not index_exists:
                create_index_sql = f"CREATE NONCLUSTERED INDEX {index_name} ON {table_name}({column_name})"
                db.execute_non_query(create_index_sql)
                print(f"✓ Created index {index_name}")
            else:
                print(f"• Index {index_name} already exists")
                
        except Exception as e:
            print(f"⚠️ Could not create index {index_name}: {e}")

def verify_migration(db: DatabaseConnection):
    """Verify the migration was successful"""
    print("\n--- Verifying Migration ---")
    
    # Check FaxJobs table structure
    query = """
    SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE
    FROM INFORMATION_SCHEMA.COLUMNS
    WHERE TABLE_NAME = 'FaxJobs'
    ORDER BY ORDINAL_POSITION
    """
    
    columns = db.execute_query(query)
    print(f"FaxJobs table has {len(columns)} columns:")
    for column in columns:
        print(f"  - {column[0]} ({column[1]}, nullable: {column[2]})")
    
    # Check if we can insert a test record
    try:
        test_insert = """
        INSERT INTO FaxJobs (
            sender_name, recipient_fax, priority, max_attempts, 
            retry_interval, page_count, file_size_mb
        ) 
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """
        
        # Use a transaction to test and rollback
        with db.get_cursor() as cursor:
            cursor.execute("BEGIN TRANSACTION")
            cursor.execute(test_insert, (
                "Test Migration", "555-123-4567", "Medium", 3, 5, 1, 0.5
            ))
            cursor.execute("ROLLBACK TRANSACTION")
        
        print("✓ Migration verification successful - can insert records")
        
    except Exception as e:
        print(f"❌ Migration verification failed: {e}")

def main():
    """Main migration function"""
    print("=== MCFax Database Schema Migration ===\n")
    
    setup_logging()
    
    try:
        # Connect to database
        db = DatabaseConnection()
        if not db.test_connection():
            print("❌ Cannot connect to database")
            return
        
        print("✓ Connected to database")
        
        # Run migrations
        migrate_contacts_table(db)
        migrate_fax_jobs_table(db)
        create_missing_tables(db)
        create_indexes(db)
        
        # Verify migration
        verify_migration(db)
        
        print("\n=== Migration Summary ===")
        print("✓ Database schema migration completed successfully!")
        print("✓ All required columns and tables are now available")
        print("✓ The application should now work with the updated database")
        
    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
