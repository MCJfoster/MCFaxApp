"""
Data models for MCFax Application
Defines data structures for FaxJobs, Contacts, and FaxContactHistory
"""

import json
from datetime import datetime
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, asdict
from .connection import DatabaseConnection

@dataclass
class Contact:
    """Contact data model"""
    contact_id: Optional[int] = None
    name: str = ""
    fax_number: str = ""
    organization: Optional[str] = None
    phone_number: Optional[str] = None
    email: Optional[str] = None
    notes: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Contact':
        """Create Contact from dictionary"""
        return cls(**data)
    
    def validate(self) -> List[str]:
        """Validate contact data and return list of errors"""
        errors = []
        
        if not self.name or not self.name.strip():
            errors.append("Name is required")
        
        if not self.fax_number or not self.fax_number.strip():
            errors.append("Fax number is required")
        
        # Basic fax number validation (digits, spaces, hyphens, parentheses, plus)
        if self.fax_number:
            import re
            if not re.match(r'^[\d\s\-\(\)\+]+$', self.fax_number):
                errors.append("Fax number contains invalid characters")
        
        # Email validation if provided
        if self.email:
            import re
            email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            if not re.match(email_pattern, self.email):
                errors.append("Invalid email format")
        
        return errors

@dataclass
class CoverPageDetails:
    """Cover page details data model"""
    attn: Optional[str] = None
    cc: Optional[str] = None
    comments: Optional[str] = None
    company: Optional[str] = None
    date: Optional[str] = None
    fax: Optional[str] = None
    from_field: Optional[str] = None  # 'from' is a Python keyword
    msg: Optional[str] = None
    org: Optional[str] = None
    pages: Optional[int] = None
    phone: Optional[str] = None
    re: Optional[str] = None
    subject: Optional[str] = None
    to: Optional[str] = None
    # Checkbox fields
    urgent: bool = False
    for_review: bool = False
    please_comment: bool = False
    please_reply: bool = False
    
    def to_json(self) -> str:
        """Convert to JSON string for database storage"""
        return json.dumps(asdict(self))
    
    @classmethod
    def from_json(cls, json_str: str) -> 'CoverPageDetails':
        """Create CoverPageDetails from JSON string"""
        if not json_str:
            return cls()
        try:
            data = json.loads(json_str)
            return cls(**data)
        except (json.JSONDecodeError, TypeError):
            return cls()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return asdict(self)

@dataclass
class FaxJob:
    """Fax job data model"""
    fax_id: Optional[int] = None
    fax_entry_url: Optional[str] = None
    sender_name: str = ""
    sender_email: Optional[str] = None
    recipient_id: Optional[int] = None
    recipient_fax: str = ""
    status: str = "Preprocessing"
    priority: str = "Medium"
    max_attempts: int = 3
    retry_interval: int = 5
    created_at: Optional[datetime] = None
    sent_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    pdf_path: Optional[str] = None
    xml_path: Optional[str] = None
    cover_page_details: Optional[CoverPageDetails] = None
    error_message: Optional[str] = None
    page_count: int = 0
    file_size_mb: float = 0.0
    
    def __post_init__(self):
        """Post-initialization processing"""
        if self.cover_page_details is None:
            self.cover_page_details = CoverPageDetails()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        data = asdict(self)
        # Convert cover_page_details to JSON string for database storage
        if self.cover_page_details:
            data['cover_page_details'] = self.cover_page_details.to_json()
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'FaxJob':
        """Create FaxJob from dictionary"""
        # Handle cover_page_details conversion
        if 'cover_page_details' in data and isinstance(data['cover_page_details'], str):
            data['cover_page_details'] = CoverPageDetails.from_json(data['cover_page_details'])
        elif 'cover_page_details' in data and isinstance(data['cover_page_details'], dict):
            data['cover_page_details'] = CoverPageDetails(**data['cover_page_details'])
        
        return cls(**data)
    
    def validate(self) -> List[str]:
        """Validate fax job data and return list of errors"""
        errors = []
        
        if not self.sender_name or not self.sender_name.strip():
            errors.append("Sender name is required")
        
        if not self.recipient_fax or not self.recipient_fax.strip():
            errors.append("Recipient fax number is required")
        
        # Validate priority
        valid_priorities = ["1st", "High", "Medium/High", "Medium", "Medium/Low", "Low"]
        if self.priority not in valid_priorities:
            errors.append(f"Priority must be one of: {', '.join(valid_priorities)}")
        
        # Validate status
        valid_statuses = ["Preprocessing", "Queued", "Sending", "Sent", "Failed", "Cancelled"]
        if self.status not in valid_statuses:
            errors.append(f"Status must be one of: {', '.join(valid_statuses)}")
        
        # Validate retry settings
        if self.max_attempts < 1 or self.max_attempts > 10:
            errors.append("Max attempts must be between 1 and 10")
        
        if self.retry_interval < 1 or self.retry_interval > 60:
            errors.append("Retry interval must be between 1 and 60 minutes")
        
        # Validate file size (36MB limit as per TODO.txt)
        if self.file_size_mb > 36:
            errors.append("File size cannot exceed 36MB")
        
        return errors

@dataclass
class FaxContactHistory:
    """Fax contact history data model"""
    history_id: Optional[int] = None
    fax_id: int = 0
    contact_id: int = 0
    action: str = ""
    timestamp: Optional[datetime] = None
    details: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'FaxContactHistory':
        """Create FaxContactHistory from dictionary"""
        return cls(**data)
    
    def validate(self) -> List[str]:
        """Validate history record and return list of errors"""
        errors = []
        
        if self.fax_id <= 0:
            errors.append("Valid fax_id is required")
        
        if self.contact_id <= 0:
            errors.append("Valid contact_id is required")
        
        if not self.action or not self.action.strip():
            errors.append("Action is required")
        
        # Validate action types
        valid_actions = ["Sent", "Received", "Failed", "Cancelled", "Queued", "Processing"]
        if self.action not in valid_actions:
            errors.append(f"Action must be one of: {', '.join(valid_actions)}")
        
        return errors

class ContactRepository:
    """Repository for Contact operations"""
    
    def __init__(self, db_connection: DatabaseConnection):
        self.db = db_connection
    
    def create(self, contact: Contact) -> Optional[int]:
        """Create a new contact and return the contact_id"""
        errors = contact.validate()
        if errors:
            raise ValueError(f"Contact validation failed: {', '.join(errors)}")
        
        query = """
        INSERT INTO Contacts (name, fax_number, organization, phone_number, email, notes)
        VALUES (?, ?, ?, ?, ?, ?)
        """
        params = (
            contact.name,
            contact.fax_number,
            contact.organization,
            contact.phone_number,
            contact.email,
            contact.notes
        )
        
        with self.db.get_cursor() as cursor:
            cursor.execute(query, params)
            cursor.execute("SELECT @@IDENTITY")
            contact_id = cursor.fetchone()[0]
            return int(contact_id)
    
    def get_by_id(self, contact_id: int) -> Optional[Contact]:
        """Get contact by ID"""
        query = "SELECT * FROM Contacts WHERE contact_id = ?"
        rows = self.db.execute_query(query, (contact_id,))
        
        if rows:
            row = rows[0]
            return Contact(
                contact_id=row[0],
                name=row[1],
                fax_number=row[2],
                organization=row[3],
                phone_number=row[4],
                email=row[5],
                notes=row[6],
                created_at=None,  # Not in existing table
                updated_at=None   # Not in existing table
            )
        return None
    
    def get_by_fax_number(self, fax_number: str) -> Optional[Contact]:
        """Get contact by fax number"""
        query = "SELECT * FROM Contacts WHERE fax_number = ?"
        rows = self.db.execute_query(query, (fax_number,))
        
        if rows:
            row = rows[0]
            return Contact(
                contact_id=row[0],
                name=row[1],
                fax_number=row[2],
                organization=row[3],
                phone_number=row[4],
                email=row[5],
                notes=row[6],
                created_at=None,  # Not in existing table
                updated_at=None   # Not in existing table
            )
        return None
    
    def get_all(self) -> List[Contact]:
        """Get all contacts"""
        query = "SELECT * FROM Contacts ORDER BY name"
        rows = self.db.execute_query(query)
        
        contacts = []
        for row in rows:
            contact = Contact(
                contact_id=row[0],
                name=row[1],
                fax_number=row[2],
                organization=row[3],
                phone_number=row[4],
                email=row[5],
                notes=row[6],
                created_at=None,  # Not in existing table
                updated_at=None   # Not in existing table
            )
            contacts.append(contact)
        
        return contacts
    
    def update(self, contact: Contact) -> bool:
        """Update an existing contact"""
        if not contact.contact_id:
            raise ValueError("Contact ID is required for update")
        
        errors = contact.validate()
        if errors:
            raise ValueError(f"Contact validation failed: {', '.join(errors)}")
        
        query = """
        UPDATE Contacts 
        SET name = ?, fax_number = ?, organization = ?, phone_number = ?, 
            email = ?, notes = ?
        WHERE contact_id = ?
        """
        params = (
            contact.name,
            contact.fax_number,
            contact.organization,
            contact.phone_number,
            contact.email,
            contact.notes,
            contact.contact_id
        )
        
        rows_affected = self.db.execute_non_query(query, params)
        return rows_affected > 0
    
    def delete(self, contact_id: int) -> bool:
        """Delete a contact"""
        query = "DELETE FROM Contacts WHERE contact_id = ?"
        rows_affected = self.db.execute_non_query(query, (contact_id,))
        return rows_affected > 0
    
    def search(self, search_term: str) -> List[Contact]:
        """Search contacts by name, organization, or fax number"""
        query = """
        SELECT * FROM Contacts 
        WHERE name LIKE ? OR organization LIKE ? OR fax_number LIKE ?
        ORDER BY name
        """
        search_pattern = f"%{search_term}%"
        rows = self.db.execute_query(query, (search_pattern, search_pattern, search_pattern))
        
        contacts = []
        for row in rows:
            contact = Contact(
                contact_id=row[0],
                name=row[1],
                fax_number=row[2],
                organization=row[3],
                phone_number=row[4],
                email=row[5],
                notes=row[6],
                created_at=None,  # Not in existing table
                updated_at=None   # Not in existing table
            )
            contacts.append(contact)
        
        return contacts

class FaxJobRepository:
    """Repository for FaxJob operations"""
    
    def __init__(self, db_connection: DatabaseConnection):
        self.db = db_connection
    
    def create(self, fax_job: FaxJob) -> Optional[int]:
        """Create a new fax job and return the fax_id"""
        errors = fax_job.validate()
        if errors:
            raise ValueError(f"FaxJob validation failed: {', '.join(errors)}")
        
        query = """
        INSERT INTO FaxJobs (
            fax_entry_url, sender_name, sender_email, recipient_id, recipient_fax,
            status, priority, max_attempts, retry_interval, pdf_path, xml_path,
            cover_page_details, page_count, file_size_mb
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        
        cover_page_json = fax_job.cover_page_details.to_json() if fax_job.cover_page_details else None
        
        params = (
            fax_job.fax_entry_url,
            fax_job.sender_name,
            fax_job.sender_email,
            fax_job.recipient_id,
            fax_job.recipient_fax,
            fax_job.status,
            fax_job.priority,
            fax_job.max_attempts,
            fax_job.retry_interval,
            fax_job.pdf_path,
            fax_job.xml_path,
            cover_page_json,
            fax_job.page_count,
            fax_job.file_size_mb
        )
        
        with self.db.get_cursor() as cursor:
            cursor.execute(query, params)
            cursor.execute("SELECT @@IDENTITY")
            fax_id = cursor.fetchone()[0]
            return int(fax_id)
    
    def get_by_id(self, fax_id: int) -> Optional[FaxJob]:
        """Get fax job by ID"""
        query = "SELECT * FROM FaxJobs WHERE fax_id = ?"
        rows = self.db.execute_query(query, (fax_id,))
        
        if rows:
            return self._row_to_fax_job(rows[0])
        return None
    
    def get_all(self) -> List[FaxJob]:
        """Get all fax jobs"""
        query = "SELECT * FROM FaxJobs ORDER BY created_at DESC"
        rows = self.db.execute_query(query)
        
        return [self._row_to_fax_job(row) for row in rows]
    
    def update_status(self, fax_id: int, status: str, error_message: str = None) -> bool:
        """Update fax job status"""
        if status == "Sent":
            query = """
            UPDATE FaxJobs 
            SET status = ?, sent_at = GETDATE(), error_message = ?
            WHERE fax_id = ?
            """
        elif status in ["Failed", "Cancelled"]:
            query = """
            UPDATE FaxJobs 
            SET status = ?, completed_at = GETDATE(), error_message = ?
            WHERE fax_id = ?
            """
        else:
            query = """
            UPDATE FaxJobs 
            SET status = ?, error_message = ?
            WHERE fax_id = ?
            """
        
        params = (status, error_message, fax_id)
        rows_affected = self.db.execute_non_query(query, params)
        return rows_affected > 0
    
    def _row_to_fax_job(self, row) -> FaxJob:
        """Convert database row to FaxJob object"""
        cover_page_details = CoverPageDetails.from_json(row[15]) if row[15] else CoverPageDetails()
        
        return FaxJob(
            fax_id=row[0],
            fax_entry_url=row[1],
            sender_name=row[2],
            sender_email=row[3],
            recipient_id=row[4],
            recipient_fax=row[5],
            status=row[6],
            priority=row[7],
            max_attempts=row[8],
            retry_interval=row[9],
            created_at=row[10],
            sent_at=row[11],
            completed_at=row[12],
            pdf_path=row[13],
            xml_path=row[14],
            cover_page_details=cover_page_details,
            error_message=row[16],
            page_count=row[17],
            file_size_mb=float(row[18]) if row[18] else 0.0
        )
