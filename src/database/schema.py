"""
Database schema management for MCFax Application
Creates and manages MS SQL Server tables as specified in TODO.txt
"""

import logging
from typing import Dict, List
from .connection import DatabaseConnection

class DatabaseSchema:
    """Manages database schema creation and validation"""
    
    def __init__(self, db_connection: DatabaseConnection):
        """
        Initialize schema manager
        
        Args:
            db_connection: Database connection instance
        """
        self.db = db_connection
        self.logger = logging.getLogger(__name__)
    
    def create_schema(self) -> bool:
        """
        Create all required tables and indexes
        
        Returns:
            bool: True if schema creation successful
        """
        try:
            self._create_contacts_table()
            self._create_fax_jobs_table()
            self._create_fax_contact_history_table()
            self._create_indexes()
            self.logger.info("Database schema created successfully")
            return True
        except Exception as e:
            self.logger.error(f"Failed to create database schema: {e}")
            return False
    
    def _create_contacts_table(self):
        """Create Contacts table"""
        create_table_sql = """
        IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='Contacts' AND xtype='U')
        CREATE TABLE Contacts (
            contact_id BIGINT IDENTITY(1,1) PRIMARY KEY,
            name NVARCHAR(100) NOT NULL,
            fax_number NVARCHAR(20) NOT NULL,
            organization NVARCHAR(100) NULL,
            phone_number NVARCHAR(20) NULL,
            email NVARCHAR(100) NULL,
            notes NVARCHAR(MAX) NULL,
            created_at DATETIME DEFAULT GETDATE(),
            updated_at DATETIME DEFAULT GETDATE()
        )
        """
        self.db.execute_non_query(create_table_sql)
        self.logger.info("Contacts table created/verified")
    
    def _create_fax_jobs_table(self):
        """Create FaxJobs table"""
        create_table_sql = """
        IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='FaxJobs' AND xtype='U')
        CREATE TABLE FaxJobs (
            fax_id BIGINT IDENTITY(1,1) PRIMARY KEY,
            fax_entry_url NVARCHAR(255) NULL,
            sender_name NVARCHAR(100) NOT NULL,
            sender_email NVARCHAR(100) NULL,
            recipient_id BIGINT NULL,
            recipient_fax NVARCHAR(20) NOT NULL,
            status NVARCHAR(50) DEFAULT 'Preprocessing',
            priority NVARCHAR(20) DEFAULT 'Medium',
            max_attempts INT DEFAULT 3,
            retry_interval INT DEFAULT 5,
            created_at DATETIME DEFAULT GETDATE(),
            sent_at DATETIME NULL,
            completed_at DATETIME NULL,
            pdf_path NVARCHAR(255) NULL,
            xml_path NVARCHAR(255) NULL,
            cover_page_details NVARCHAR(MAX) NULL,
            error_message NVARCHAR(MAX) NULL,
            page_count INT DEFAULT 0,
            file_size_mb DECIMAL(10,2) DEFAULT 0,
            FOREIGN KEY (recipient_id) REFERENCES Contacts(contact_id)
        )
        """
        self.db.execute_non_query(create_table_sql)
        self.logger.info("FaxJobs table created/verified")
    
    def _create_fax_contact_history_table(self):
        """Create FaxContactHistory table"""
        create_table_sql = """
        IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='FaxContactHistory' AND xtype='U')
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
        self.db.execute_non_query(create_table_sql)
        self.logger.info("FaxContactHistory table created/verified")
    
    def _create_indexes(self):
        """Create performance indexes"""
        indexes = [
            # Contacts indexes
            "CREATE NONCLUSTERED INDEX IF NOT EXISTS IX_Contacts_FaxNumber ON Contacts(fax_number)",
            "CREATE NONCLUSTERED INDEX IF NOT EXISTS IX_Contacts_Name ON Contacts(name)",
            
            # FaxJobs indexes
            "CREATE NONCLUSTERED INDEX IF NOT EXISTS IX_FaxJobs_Status ON FaxJobs(status)",
            "CREATE NONCLUSTERED INDEX IF NOT EXISTS IX_FaxJobs_CreatedAt ON FaxJobs(created_at)",
            "CREATE NONCLUSTERED INDEX IF NOT EXISTS IX_FaxJobs_RecipientId ON FaxJobs(recipient_id)",
            "CREATE NONCLUSTERED INDEX IF NOT EXISTS IX_FaxJobs_FaxEntryUrl ON FaxJobs(fax_entry_url)",
            
            # FaxContactHistory indexes
            "CREATE NONCLUSTERED INDEX IF NOT EXISTS IX_FaxContactHistory_FaxId ON FaxContactHistory(fax_id)",
            "CREATE NONCLUSTERED INDEX IF NOT EXISTS IX_FaxContactHistory_ContactId ON FaxContactHistory(contact_id)",
            "CREATE NONCLUSTERED INDEX IF NOT EXISTS IX_FaxContactHistory_Timestamp ON FaxContactHistory(timestamp)"
        ]
        
        for index_sql in indexes:
            try:
                self.db.execute_non_query(index_sql)
            except Exception as e:
                # Some SQL Server versions don't support IF NOT EXISTS for indexes
                # Try without it for compatibility
                if "IF NOT EXISTS" in index_sql:
                    try:
                        simplified_sql = index_sql.replace(" IF NOT EXISTS", "")
                        self.db.execute_non_query(simplified_sql)
                    except:
                        # Index might already exist, continue
                        pass
                else:
                    self.logger.warning(f"Failed to create index: {e}")
        
        self.logger.info("Database indexes created/verified")
    
    def validate_schema(self) -> Dict[str, bool]:
        """
        Validate that all required tables exist
        
        Returns:
            dict: Table existence status
        """
        tables = ['Contacts', 'FaxJobs', 'FaxContactHistory']
        results = {}
        
        for table in tables:
            query = """
            SELECT COUNT(*) 
            FROM INFORMATION_SCHEMA.TABLES 
            WHERE TABLE_NAME = ? AND TABLE_TYPE = 'BASE TABLE'
            """
            count = self.db.execute_scalar(query, (table,))
            results[table] = count > 0
        
        return results
    
    def get_table_info(self, table_name: str) -> List[Dict]:
        """
        Get column information for a table
        
        Args:
            table_name: Name of the table
            
        Returns:
            list: Column information
        """
        query = """
        SELECT 
            COLUMN_NAME,
            DATA_TYPE,
            IS_NULLABLE,
            CHARACTER_MAXIMUM_LENGTH,
            COLUMN_DEFAULT
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_NAME = ?
        ORDER BY ORDINAL_POSITION
        """
        
        rows = self.db.execute_query(query, (table_name,))
        return [
            {
                'column_name': row[0],
                'data_type': row[1],
                'is_nullable': row[2],
                'max_length': row[3],
                'default_value': row[4]
            }
            for row in rows
        ]
    
    def drop_schema(self) -> bool:
        """
        Drop all tables (use with caution!)
        
        Returns:
            bool: True if successful
        """
        try:
            # Drop in reverse order due to foreign key constraints
            tables = ['FaxContactHistory', 'FaxJobs', 'Contacts']
            
            for table in tables:
                drop_sql = f"IF EXISTS (SELECT * FROM sysobjects WHERE name='{table}' AND xtype='U') DROP TABLE {table}"
                self.db.execute_non_query(drop_sql)
            
            self.logger.info("Database schema dropped successfully")
            return True
        except Exception as e:
            self.logger.error(f"Failed to drop database schema: {e}")
            return False
    
    def get_schema_status(self) -> Dict:
        """
        Get comprehensive schema status
        
        Returns:
            dict: Schema status information
        """
        try:
            validation = self.validate_schema()
            
            # Get row counts
            row_counts = {}
            for table in validation.keys():
                if validation[table]:
                    count = self.db.execute_scalar(f"SELECT COUNT(*) FROM {table}")
                    row_counts[table] = count
                else:
                    row_counts[table] = 0
            
            return {
                'tables_exist': validation,
                'row_counts': row_counts,
                'all_tables_exist': all(validation.values()),
                'total_contacts': row_counts.get('Contacts', 0),
                'total_fax_jobs': row_counts.get('FaxJobs', 0),
                'total_history_records': row_counts.get('FaxContactHistory', 0)
            }
        except Exception as e:
            return {
                'error': str(e),
                'tables_exist': {},
                'row_counts': {},
                'all_tables_exist': False
            }
