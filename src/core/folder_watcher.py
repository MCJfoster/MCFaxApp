"""
Folder Monitoring Module (1.1) for MCFax Application
Detects new PDF files in user-specified folder to trigger fax job creation
"""

import os
import time
import logging
from typing import Callable, Optional, List, Set
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileCreatedEvent, FileModifiedEvent

class PDFFileHandler(FileSystemEventHandler):
    """File system event handler for PDF files"""
    
    def __init__(self, callback: Callable[[str], None], 
                 naming_filter: Optional[str] = None,
                 recursive: bool = False):
        """
        Initialize PDF file handler
        
        Args:
            callback: Function to call when PDF is detected
            naming_filter: Optional naming convention filter (e.g., "fax_*.pdf")
            recursive: Whether to monitor subfolders
        """
        super().__init__()
        self.callback = callback
        self.naming_filter = naming_filter
        self.recursive = recursive
        self.processed_files: Set[str] = set()
        self.logger = logging.getLogger(__name__)
        
    def on_created(self, event):
        """Handle file creation events"""
        if not event.is_directory:
            self._handle_file_event(event.src_path, "created")
    
    def on_modified(self, event):
        """Handle file modification events"""
        if not event.is_directory:
            self._handle_file_event(event.src_path, "modified")
    
    def _handle_file_event(self, file_path: str, event_type: str):
        """Process file events for PDF files"""
        try:
            # Check if it's a PDF file
            if not file_path.lower().endswith('.pdf'):
                return
            
            # Avoid processing the same file multiple times
            if file_path in self.processed_files:
                return
            
            # Apply naming filter if specified
            if self.naming_filter and not self._matches_naming_filter(file_path):
                return
            
            # Wait a moment to ensure file is fully written
            time.sleep(0.5)
            
            # Verify file exists and is readable
            if not os.path.exists(file_path):
                return
            
            try:
                # Try to open file to ensure it's not locked
                with open(file_path, 'rb') as f:
                    f.read(1024)  # Read first 1KB to test
            except (IOError, PermissionError):
                self.logger.warning(f"File {file_path} is not ready or locked, skipping")
                return
            
            # Mark as processed and notify callback
            self.processed_files.add(file_path)
            self.logger.info(f"PDF file {event_type}: {file_path}")
            
            # Call the callback function
            self.callback(file_path)
            
        except Exception as e:
            self.logger.error(f"Error processing file event for {file_path}: {e}")
    
    def _matches_naming_filter(self, file_path: str) -> bool:
        """Check if file matches naming convention filter"""
        if not self.naming_filter:
            return True
        
        filename = os.path.basename(file_path)
        
        # Simple wildcard matching
        if '*' in self.naming_filter:
            prefix, suffix = self.naming_filter.split('*', 1)
            return filename.startswith(prefix) and filename.endswith(suffix)
        else:
            return filename == self.naming_filter

class FolderWatcher:
    """
    Folder Monitoring Module (1.1)
    Monitors specified folder for new PDF files and triggers callbacks
    """
    
    def __init__(self):
        """Initialize folder watcher"""
        self.observer: Optional[Observer] = None
        self.watched_folder: Optional[str] = None
        self.recursive: bool = False
        self.naming_filter: Optional[str] = None
        self.callback: Optional[Callable[[str], None]] = None
        self.is_monitoring: bool = False
        self.logger = logging.getLogger(__name__)
        
    def set_folder(self, folder_path: str, recursive: bool = False) -> bool:
        """
        Set the folder to monitor
        
        Args:
            folder_path: Path to folder to monitor
            recursive: Whether to monitor subfolders
            
        Returns:
            bool: True if folder is valid and set successfully
        """
        try:
            # Validate folder path
            if not os.path.exists(folder_path):
                self.logger.error(f"Folder does not exist: {folder_path}")
                return False
            
            if not os.path.isdir(folder_path):
                self.logger.error(f"Path is not a directory: {folder_path}")
                return False
            
            # Stop current monitoring if active
            if self.is_monitoring:
                self.stop_monitoring()
            
            self.watched_folder = os.path.abspath(folder_path)
            self.recursive = recursive
            
            self.logger.info(f"Folder set for monitoring: {self.watched_folder} (recursive: {recursive})")
            return True
            
        except Exception as e:
            self.logger.error(f"Error setting folder: {e}")
            return False
    
    def set_naming_filter(self, filter_pattern: Optional[str]):
        """
        Set naming convention filter for PDF files
        
        Args:
            filter_pattern: Pattern like "fax_*.pdf" or None for no filter
        """
        self.naming_filter = filter_pattern
        if filter_pattern:
            self.logger.info(f"Naming filter set: {filter_pattern}")
        else:
            self.logger.info("Naming filter cleared")
    
    def set_callback(self, callback: Callable[[str], None]):
        """
        Set callback function to be called when PDF is detected
        
        Args:
            callback: Function that takes file path as parameter
        """
        self.callback = callback
        self.logger.info("PDF detection callback set")
    
    def start_monitoring(self) -> bool:
        """
        Start monitoring the specified folder
        
        Returns:
            bool: True if monitoring started successfully
        """
        try:
            if not self.watched_folder:
                self.logger.error("No folder specified for monitoring")
                return False
            
            if not self.callback:
                self.logger.error("No callback function specified")
                return False
            
            if self.is_monitoring:
                self.logger.warning("Already monitoring, stopping previous monitoring")
                self.stop_monitoring()
            
            # Create file handler
            handler = PDFFileHandler(
                callback=self.callback,
                naming_filter=self.naming_filter,
                recursive=self.recursive
            )
            
            # Create and start observer
            self.observer = Observer()
            self.observer.schedule(handler, self.watched_folder, recursive=self.recursive)
            self.observer.start()
            
            self.is_monitoring = True
            self.logger.info(f"Started monitoring folder: {self.watched_folder}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error starting folder monitoring: {e}")
            return False
    
    def stop_monitoring(self):
        """Stop folder monitoring"""
        try:
            if self.observer and self.is_monitoring:
                self.observer.stop()
                self.observer.join(timeout=5)  # Wait up to 5 seconds
                self.observer = None
                self.is_monitoring = False
                self.logger.info("Stopped folder monitoring")
            
        except Exception as e:
            self.logger.error(f"Error stopping folder monitoring: {e}")
    
    def get_status(self) -> dict:
        """
        Get current monitoring status
        
        Returns:
            dict: Status information
        """
        return {
            'is_monitoring': self.is_monitoring,
            'watched_folder': self.watched_folder,
            'recursive': self.recursive,
            'naming_filter': self.naming_filter,
            'has_callback': self.callback is not None
        }
    
    def scan_existing_files(self) -> List[str]:
        """
        Scan for existing PDF files in the monitored folder
        
        Returns:
            list: List of existing PDF file paths
        """
        if not self.watched_folder:
            return []
        
        pdf_files = []
        
        try:
            if self.recursive:
                # Recursive scan
                for root, dirs, files in os.walk(self.watched_folder):
                    for file in files:
                        if file.lower().endswith('.pdf'):
                            file_path = os.path.join(root, file)
                            if not self.naming_filter or self._matches_naming_filter(file_path):
                                pdf_files.append(file_path)
            else:
                # Top-level scan only
                for item in os.listdir(self.watched_folder):
                    item_path = os.path.join(self.watched_folder, item)
                    if os.path.isfile(item_path) and item.lower().endswith('.pdf'):
                        if not self.naming_filter or self._matches_naming_filter(item_path):
                            pdf_files.append(item_path)
            
            self.logger.info(f"Found {len(pdf_files)} existing PDF files")
            return sorted(pdf_files)
            
        except Exception as e:
            self.logger.error(f"Error scanning existing files: {e}")
            return []
    
    def _matches_naming_filter(self, file_path: str) -> bool:
        """Check if file matches naming convention filter"""
        if not self.naming_filter:
            return True
        
        filename = os.path.basename(file_path)
        
        # Simple wildcard matching
        if '*' in self.naming_filter:
            prefix, suffix = self.naming_filter.split('*', 1)
            return filename.startswith(prefix) and filename.endswith(suffix)
        else:
            return filename == self.naming_filter
    
    def __enter__(self):
        """Context manager entry"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.stop_monitoring()

# Utility functions for folder monitoring
def validate_folder_path(folder_path: str) -> tuple[bool, str]:
    """
    Validate folder path for monitoring
    
    Args:
        folder_path: Path to validate
        
    Returns:
        tuple: (is_valid, error_message)
    """
    try:
        if not folder_path or not folder_path.strip():
            return False, "Folder path cannot be empty"
        
        if not os.path.exists(folder_path):
            return False, "Folder does not exist"
        
        if not os.path.isdir(folder_path):
            return False, "Path is not a directory"
        
        # Test read access
        try:
            os.listdir(folder_path)
        except PermissionError:
            return False, "No read permission for folder"
        
        return True, ""
        
    except Exception as e:
        return False, f"Error validating folder: {str(e)}"

def get_folder_info(folder_path: str) -> dict:
    """
    Get information about a folder
    
    Args:
        folder_path: Path to analyze
        
    Returns:
        dict: Folder information
    """
    try:
        if not os.path.exists(folder_path):
            return {'exists': False}
        
        stat = os.stat(folder_path)
        
        # Count PDF files
        pdf_count = 0
        subfolder_count = 0
        
        try:
            for item in os.listdir(folder_path):
                item_path = os.path.join(folder_path, item)
                if os.path.isfile(item_path) and item.lower().endswith('.pdf'):
                    pdf_count += 1
                elif os.path.isdir(item_path):
                    subfolder_count += 1
        except PermissionError:
            pdf_count = -1  # Indicates permission error
            subfolder_count = -1
        
        return {
            'exists': True,
            'path': os.path.abspath(folder_path),
            'size_bytes': stat.st_size,
            'modified_time': stat.st_mtime,
            'pdf_count': pdf_count,
            'subfolder_count': subfolder_count,
            'readable': pdf_count >= 0
        }
        
    except Exception as e:
        return {
            'exists': False,
            'error': str(e)
        }
