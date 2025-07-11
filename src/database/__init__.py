"""
Database module for MCFax Application
Handles MS SQL Server connectivity and data operations
"""

from .connection import DatabaseConnection
from .models import FaxJob, Contact, FaxContactHistory, ContactRepository, FaxJobRepository
from .schema import DatabaseSchema

__all__ = ['DatabaseConnection', 'FaxJob', 'Contact', 'FaxContactHistory', 'DatabaseSchema', 'ContactRepository', 'FaxJobRepository']
