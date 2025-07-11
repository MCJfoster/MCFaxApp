"""
Database connection management for MS SQL Server
"""

import pyodbc
import logging
from typing import Optional, Any, Dict
from contextlib import contextmanager
from core.settings_portable import get_settings

class DatabaseConnection:
    """Manages MS SQL Server database connections for MCFax application"""
    
    def __init__(self, server: str = None, database: str = None, 
                 username: str = None, password: str = None):
        """
        Initialize database connection parameters
        
        Args:
            server: SQL Server IP address (optional, loads from settings if not provided)
            database: Database name (optional, loads from settings if not provided)
            username: SQL Server username (optional, loads from settings if not provided)
            password: SQL Server password (optional, loads from settings if not provided)
        """
        # Load settings
        settings = get_settings()
        
        # Use provided parameters or load from settings with fallback to hardcoded defaults
        self.server = server or settings.get("database.server", "10.70.1.251")
        self.database = database or settings.get("database.database", "MCFAX")
        self.username = username or settings.get("database.username", "SA")
        self.password = password or settings.get("database.password", "Blue$8080")
        self.connection_string = (
            f"DRIVER={{ODBC Driver 17 for SQL Server}};"
            f"SERVER={self.server};"
            f"DATABASE={self.database};"
            f"UID={self.username};"
            f"PWD={self.password};"
            f"TrustServerCertificate=yes;"
        )
        self._connection: Optional[pyodbc.Connection] = None
        
        # Setup logging
        self.logger = logging.getLogger(__name__)
        
    def connect(self) -> bool:
        """
        Establish connection to the database
        
        Returns:
            bool: True if connection successful, False otherwise
        """
        try:
            self._connection = pyodbc.connect(self.connection_string)
            self.logger.info(f"Successfully connected to database {self.database} on {self.server}")
            return True
        except pyodbc.Error as e:
            self.logger.error(f"Failed to connect to database: {e}")
            return False
    
    def disconnect(self):
        """Close the database connection"""
        if self._connection:
            self._connection.close()
            self._connection = None
            self.logger.info("Database connection closed")
    
    @property
    def is_connected(self) -> bool:
        """Check if database connection is active"""
        try:
            if self._connection:
                # Test connection with a simple query
                cursor = self._connection.cursor()
                cursor.execute("SELECT 1")
                cursor.fetchone()
                cursor.close()
                return True
        except (pyodbc.Error, AttributeError):
            pass
        return False
    
    @contextmanager
    def get_cursor(self):
        """
        Context manager for database cursor operations
        
        Yields:
            pyodbc.Cursor: Database cursor for executing queries
        """
        if not self.is_connected:
            if not self.connect():
                raise ConnectionError("Unable to establish database connection")
        
        cursor = self._connection.cursor()
        try:
            yield cursor
            self._connection.commit()
        except Exception as e:
            self._connection.rollback()
            self.logger.error(f"Database operation failed: {e}")
            raise
        finally:
            cursor.close()
    
    def execute_query(self, query: str, params: tuple = None) -> list:
        """
        Execute a SELECT query and return results
        
        Args:
            query: SQL SELECT query
            params: Query parameters
            
        Returns:
            list: Query results
        """
        with self.get_cursor() as cursor:
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            return cursor.fetchall()
    
    def execute_non_query(self, query: str, params: tuple = None) -> int:
        """
        Execute INSERT, UPDATE, or DELETE query
        
        Args:
            query: SQL query
            params: Query parameters
            
        Returns:
            int: Number of affected rows
        """
        with self.get_cursor() as cursor:
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            return cursor.rowcount
    
    def execute_scalar(self, query: str, params: tuple = None) -> Any:
        """
        Execute query and return single value
        
        Args:
            query: SQL query
            params: Query parameters
            
        Returns:
            Any: Single value result
        """
        with self.get_cursor() as cursor:
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            result = cursor.fetchone()
            return result[0] if result else None
    
    def test_connection(self) -> Dict[str, Any]:
        """
        Test database connection and return status information
        
        Returns:
            dict: Connection status and database information
        """
        try:
            if not self.connect():
                return {
                    'connected': False,
                    'error': 'Failed to establish connection',
                    'server': self.server,
                    'database': self.database
                }
            
            # Get database information
            with self.get_cursor() as cursor:
                cursor.execute("SELECT @@VERSION")
                version = cursor.fetchone()[0]
                
                cursor.execute("SELECT DB_NAME()")
                db_name = cursor.fetchone()[0]
                
                cursor.execute("SELECT GETDATE()")
                server_time = cursor.fetchone()[0]
            
            return {
                'connected': True,
                'server': self.server,
                'database': db_name,
                'version': version,
                'server_time': server_time,
                'connection_string': self.connection_string.replace(self.password, '***')
            }
            
        except Exception as e:
            return {
                'connected': False,
                'error': str(e),
                'server': self.server,
                'database': self.database
            }
    
    def __enter__(self):
        """Context manager entry"""
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.disconnect()
