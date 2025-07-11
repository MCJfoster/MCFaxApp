"""
PDF Browser Module
Handles browsing and listing PDF files in the temp folder
"""

import os
import logging
from pathlib import Path
from typing import List, Optional, Dict, Any
from datetime import datetime
import PyPDF2
import pdfplumber

class PDFInfo:
    """Information about a PDF file"""
    
    def __init__(self, file_path: str):
        self.file_path = Path(file_path)
        self.name = self.file_path.name
        self.size_bytes = 0
        self.size_mb = 0.0
        self.page_count = 0
        self.created_time = None
        self.modified_time = None
        self.is_valid = False
        self.error_message = None
        
        self._analyze_file()
    
    def _analyze_file(self):
        """Analyze the PDF file to extract information"""
        try:
            if not self.file_path.exists():
                self.error_message = "File does not exist"
                return
            
            # Get file stats
            stat = self.file_path.stat()
            self.size_bytes = stat.st_size
            self.size_mb = self.size_bytes / (1024 * 1024)
            self.created_time = datetime.fromtimestamp(stat.st_ctime)
            self.modified_time = datetime.fromtimestamp(stat.st_mtime)
            
            # Try to read PDF and get page count
            try:
                with open(self.file_path, 'rb') as file:
                    pdf_reader = PyPDF2.PdfReader(file)
                    self.page_count = len(pdf_reader.pages)
                    self.is_valid = True
            except Exception as e:
                self.error_message = f"Invalid PDF: {str(e)}"
                self.is_valid = False
                
        except Exception as e:
            self.error_message = f"Error analyzing file: {str(e)}"
            self.is_valid = False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            'file_path': str(self.file_path),
            'name': self.name,
            'size_bytes': self.size_bytes,
            'size_mb': round(self.size_mb, 2),
            'page_count': self.page_count,
            'created_time': self.created_time.isoformat() if self.created_time else None,
            'modified_time': self.modified_time.isoformat() if self.modified_time else None,
            'is_valid': self.is_valid,
            'error_message': self.error_message
        }
    
    def __str__(self):
        if self.is_valid:
            return f"{self.name} ({self.page_count} pages, {self.size_mb:.1f} MB)"
        else:
            return f"{self.name} (Invalid: {self.error_message})"

class PDFBrowser:
    """
    PDF Browser for listing and managing PDF files in a directory
    """
    
    def __init__(self, folder_path: str):
        """
        Initialize PDF browser
        
        Args:
            folder_path: Path to folder containing PDF files
        """
        self.folder_path = Path(folder_path)
        self.logger = logging.getLogger(__name__)
        self._pdf_cache = {}
        self._last_scan_time = None
        
        if not self.folder_path.exists():
            self.logger.warning(f"PDF folder does not exist: {folder_path}")
        elif not self.folder_path.is_dir():
            self.logger.error(f"PDF path is not a directory: {folder_path}")
    
    def get_pdf_files(self, force_refresh: bool = False) -> List[PDFInfo]:
        """
        Get list of PDF files in the folder
        
        Args:
            force_refresh: Force refresh of file list
            
        Returns:
            List of PDFInfo objects
        """
        try:
            if not self.folder_path.exists():
                self.logger.warning(f"PDF folder does not exist: {self.folder_path}")
                return []
            
            # Check if we need to refresh
            current_time = datetime.now()
            if (not force_refresh and 
                self._last_scan_time and 
                (current_time - self._last_scan_time).seconds < 5):
                # Return cached results if scanned recently
                return list(self._pdf_cache.values())
            
            pdf_files = []
            new_cache = {}
            
            # Scan for PDF files
            for file_path in self.folder_path.glob("*.pdf"):
                if file_path.is_file():
                    # Check if we have cached info and file hasn't changed
                    file_key = str(file_path)
                    if (file_key in self._pdf_cache and 
                        file_path.stat().st_mtime == self._pdf_cache[file_key].modified_time.timestamp()):
                        # Use cached info
                        pdf_info = self._pdf_cache[file_key]
                    else:
                        # Create new info
                        pdf_info = PDFInfo(str(file_path))
                    
                    new_cache[file_key] = pdf_info
                    pdf_files.append(pdf_info)
            
            # Update cache
            self._pdf_cache = new_cache
            self._last_scan_time = current_time
            
            # Sort by name
            pdf_files.sort(key=lambda x: x.name.lower())
            
            self.logger.info(f"Found {len(pdf_files)} PDF files in {self.folder_path}")
            return pdf_files
            
        except Exception as e:
            self.logger.error(f"Error scanning PDF files: {e}")
            return []
    
    def get_pdf_info(self, file_name: str) -> Optional[PDFInfo]:
        """
        Get information about a specific PDF file
        
        Args:
            file_name: Name of the PDF file
            
        Returns:
            PDFInfo object or None if not found
        """
        file_path = self.folder_path / file_name
        if file_path.exists():
            return PDFInfo(str(file_path))
        return None
    
    def get_total_size(self, pdf_files: List[str]) -> float:
        """
        Calculate total size of selected PDF files in MB
        
        Args:
            pdf_files: List of PDF file paths
            
        Returns:
            Total size in MB
        """
        total_size = 0.0
        for pdf_path in pdf_files:
            try:
                file_path = Path(pdf_path)
                if file_path.exists():
                    total_size += file_path.stat().st_size / (1024 * 1024)
            except Exception as e:
                self.logger.error(f"Error getting size for {pdf_path}: {e}")
        
        return total_size
    
    def validate_pdf_selection(self, pdf_files: List[str], max_size_mb: float = 36.0) -> Dict[str, Any]:
        """
        Validate a selection of PDF files
        
        Args:
            pdf_files: List of PDF file paths
            max_size_mb: Maximum allowed total size in MB
            
        Returns:
            Dictionary with validation results
        """
        result = {
            'is_valid': True,
            'errors': [],
            'warnings': [],
            'total_size_mb': 0.0,
            'total_pages': 0,
            'file_count': len(pdf_files)
        }
        
        if not pdf_files:
            result['is_valid'] = False
            result['errors'].append("No PDF files selected")
            return result
        
        total_size = 0.0
        total_pages = 0
        
        for pdf_path in pdf_files:
            try:
                file_path = Path(pdf_path)
                
                if not file_path.exists():
                    result['errors'].append(f"File not found: {file_path.name}")
                    result['is_valid'] = False
                    continue
                
                # Get file size
                size_mb = file_path.stat().st_size / (1024 * 1024)
                total_size += size_mb
                
                # Try to get page count
                try:
                    with open(file_path, 'rb') as file:
                        pdf_reader = PyPDF2.PdfReader(file)
                        pages = len(pdf_reader.pages)
                        total_pages += pages
                        
                        if pages == 0:
                            result['warnings'].append(f"File has no pages: {file_path.name}")
                            
                except Exception as e:
                    result['errors'].append(f"Invalid PDF: {file_path.name} - {str(e)}")
                    result['is_valid'] = False
                    
            except Exception as e:
                result['errors'].append(f"Error processing {pdf_path}: {str(e)}")
                result['is_valid'] = False
        
        result['total_size_mb'] = round(total_size, 2)
        result['total_pages'] = total_pages
        
        # Check size limit
        if total_size > max_size_mb:
            result['errors'].append(f"Total size ({total_size:.1f} MB) exceeds limit ({max_size_mb} MB)")
            result['is_valid'] = False
        
        # Warnings for large files
        if total_size > max_size_mb * 0.8:
            result['warnings'].append(f"Total size ({total_size:.1f} MB) is close to limit ({max_size_mb} MB)")
        
        return result
    
    def search_pdfs(self, search_term: str) -> List[PDFInfo]:
        """
        Search for PDF files by name
        
        Args:
            search_term: Search term to match against file names
            
        Returns:
            List of matching PDFInfo objects
        """
        all_pdfs = self.get_pdf_files()
        search_lower = search_term.lower()
        
        matching_pdfs = []
        for pdf_info in all_pdfs:
            if search_lower in pdf_info.name.lower():
                matching_pdfs.append(pdf_info)
        
        return matching_pdfs
    
    def get_folder_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the PDF folder
        
        Returns:
            Dictionary with folder statistics
        """
        try:
            if not self.folder_path.exists():
                return {
                    'exists': False,
                    'error': 'Folder does not exist'
                }
            
            pdf_files = self.get_pdf_files()
            valid_files = [pdf for pdf in pdf_files if pdf.is_valid]
            invalid_files = [pdf for pdf in pdf_files if not pdf.is_valid]
            
            total_size = sum(pdf.size_mb for pdf in valid_files)
            total_pages = sum(pdf.page_count for pdf in valid_files)
            
            return {
                'exists': True,
                'folder_path': str(self.folder_path),
                'total_files': len(pdf_files),
                'valid_files': len(valid_files),
                'invalid_files': len(invalid_files),
                'total_size_mb': round(total_size, 2),
                'total_pages': total_pages,
                'last_scan': self._last_scan_time.isoformat() if self._last_scan_time else None
            }
            
        except Exception as e:
            return {
                'exists': False,
                'error': str(e)
            }

# Utility functions
def is_valid_pdf(file_path: str) -> bool:
    """
    Check if a file is a valid PDF
    
    Args:
        file_path: Path to the file
        
    Returns:
        True if valid PDF, False otherwise
    """
    try:
        with open(file_path, 'rb') as file:
            PyPDF2.PdfReader(file)
        return True
    except:
        return False

def get_pdf_page_count(file_path: str) -> int:
    """
    Get the number of pages in a PDF file
    
    Args:
        file_path: Path to the PDF file
        
    Returns:
        Number of pages, or 0 if error
    """
    try:
        with open(file_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            return len(pdf_reader.pages)
    except:
        return 0

def get_pdf_text_preview(file_path: str, max_chars: int = 500) -> str:
    """
    Get a text preview of the PDF content
    
    Args:
        file_path: Path to the PDF file
        max_chars: Maximum number of characters to return
        
    Returns:
        Text preview or error message
    """
    try:
        with pdfplumber.open(file_path) as pdf:
            text = ""
            for page in pdf.pages[:3]:  # First 3 pages only
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
                if len(text) > max_chars:
                    break
            
            if len(text) > max_chars:
                text = text[:max_chars] + "..."
            
            return text.strip() if text.strip() else "No text content found"
            
    except Exception as e:
        return f"Error reading PDF: {str(e)}"
