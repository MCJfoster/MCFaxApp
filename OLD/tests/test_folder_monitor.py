"""
Test script for Folder Monitoring Module (1.1)
Tests folder monitoring, PDF detection, and callback functionality
"""

import sys
import os
import time
import tempfile
import logging
from pathlib import Path

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from core.folder_watcher import FolderWatcher, validate_folder_path, get_folder_info

def setup_logging():
    """Setup basic logging"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

def create_test_pdf(file_path: str):
    """Create a simple test PDF file"""
    # Create a minimal PDF content
    pdf_content = b"""%PDF-1.4
1 0 obj
<<
/Type /Catalog
/Pages 2 0 R
>>
endobj

2 0 obj
<<
/Type /Pages
/Kids [3 0 R]
/Count 1
>>
endobj

3 0 obj
<<
/Type /Page
/Parent 2 0 R
/MediaBox [0 0 612 792]
/Contents 4 0 R
>>
endobj

4 0 obj
<<
/Length 44
>>
stream
BT
/F1 12 Tf
100 700 Td
(Test PDF) Tj
ET
endstream
endobj

xref
0 5
0000000000 65535 f 
0000000009 00000 n 
0000000058 00000 n 
0000000115 00000 n 
0000000204 00000 n 
trailer
<<
/Size 5
/Root 1 0 R
>>
startxref
297
%%EOF"""
    
    with open(file_path, 'wb') as f:
        f.write(pdf_content)

def test_folder_validation():
    """Test folder path validation"""
    print("=" * 50)
    print("Testing Folder Validation")
    print("=" * 50)
    
    # Test invalid paths
    test_cases = [
        ("", "Empty path"),
        ("nonexistent_folder", "Non-existent folder"),
        (__file__, "File instead of folder")
    ]
    
    for path, description in test_cases:
        is_valid, error = validate_folder_path(path)
        if not is_valid:
            print(f"✓ {description}: Correctly rejected - {error}")
        else:
            print(f"✗ {description}: Should have been rejected")
    
    # Test valid path
    temp_dir = tempfile.mkdtemp()
    try:
        is_valid, error = validate_folder_path(temp_dir)
        if is_valid:
            print(f"✓ Valid folder: Correctly accepted - {temp_dir}")
        else:
            print(f"✗ Valid folder: Should have been accepted - {error}")
    finally:
        os.rmdir(temp_dir)
    
    return True

def test_folder_info():
    """Test folder information gathering"""
    print("\n" + "=" * 50)
    print("Testing Folder Information")
    print("=" * 50)
    
    # Create test folder with PDFs
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create some test PDFs
        create_test_pdf(os.path.join(temp_dir, "test1.pdf"))
        create_test_pdf(os.path.join(temp_dir, "fax_test2.pdf"))
        create_test_pdf(os.path.join(temp_dir, "document.pdf"))
        
        # Create a subfolder
        subfolder = os.path.join(temp_dir, "subfolder")
        os.makedirs(subfolder)
        create_test_pdf(os.path.join(subfolder, "sub_test.pdf"))
        
        # Get folder info
        info = get_folder_info(temp_dir)
        
        if info['exists'] and info['pdf_count'] == 3 and info['subfolder_count'] == 1:
            print("✓ Folder info correctly gathered")
            print(f"  PDFs found: {info['pdf_count']}")
            print(f"  Subfolders: {info['subfolder_count']}")
            print(f"  Path: {info['path']}")
        else:
            print("✗ Folder info gathering failed")
            print(f"  Expected: 3 PDFs, 1 subfolder")
            print(f"  Got: {info['pdf_count']} PDFs, {info['subfolder_count']} subfolders")
            return False
    
    return True

def test_folder_watcher():
    """Test folder monitoring functionality"""
    print("\n" + "=" * 50)
    print("Testing Folder Monitoring (1.1)")
    print("=" * 50)
    
    detected_files = []
    
    def pdf_callback(file_path):
        """Callback function for PDF detection"""
        detected_files.append(file_path)
        print(f"  📄 PDF detected: {os.path.basename(file_path)}")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        # Initialize folder watcher
        watcher = FolderWatcher()
        
        # Test setting folder
        if not watcher.set_folder(temp_dir, recursive=False):
            print("✗ Failed to set folder")
            return False
        print(f"✓ Folder set: {temp_dir}")
        
        # Test setting callback
        watcher.set_callback(pdf_callback)
        print("✓ Callback set")
        
        # Test naming filter
        watcher.set_naming_filter("fax_*.pdf")
        print("✓ Naming filter set: fax_*.pdf")
        
        # Test status
        status = watcher.get_status()
        if status['watched_folder'] == os.path.abspath(temp_dir) and not status['is_monitoring']:
            print("✓ Status check passed")
        else:
            print("✗ Status check failed")
            return False
        
        # Start monitoring
        if not watcher.start_monitoring():
            print("✗ Failed to start monitoring")
            return False
        print("✓ Monitoring started")
        
        # Wait a moment for monitoring to initialize
        time.sleep(1)
        
        # Create test files
        print("\nCreating test files...")
        
        # This should NOT be detected (doesn't match filter)
        create_test_pdf(os.path.join(temp_dir, "regular.pdf"))
        time.sleep(1)
        
        # This SHOULD be detected (matches filter)
        create_test_pdf(os.path.join(temp_dir, "fax_document.pdf"))
        time.sleep(1)
        
        # Another one that SHOULD be detected
        create_test_pdf(os.path.join(temp_dir, "fax_report.pdf"))
        time.sleep(1)
        
        # Stop monitoring
        watcher.stop_monitoring()
        print("✓ Monitoring stopped")
        
        # Check results
        if len(detected_files) == 2:
            print("✓ Correct number of files detected (2)")
            for file_path in detected_files:
                if "fax_" in os.path.basename(file_path):
                    print(f"  ✓ Correctly detected: {os.path.basename(file_path)}")
                else:
                    print(f"  ✗ Incorrectly detected: {os.path.basename(file_path)}")
                    return False
        else:
            print(f"✗ Wrong number of files detected: {len(detected_files)} (expected 2)")
            return False
    
    return True

def test_existing_file_scan():
    """Test scanning for existing PDF files"""
    print("\n" + "=" * 50)
    print("Testing Existing File Scan")
    print("=" * 50)
    
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create test files
        create_test_pdf(os.path.join(temp_dir, "existing1.pdf"))
        create_test_pdf(os.path.join(temp_dir, "fax_existing2.pdf"))
        create_test_pdf(os.path.join(temp_dir, "document.txt"))  # Not a PDF
        
        # Create subfolder with PDF
        subfolder = os.path.join(temp_dir, "sub")
        os.makedirs(subfolder)
        create_test_pdf(os.path.join(subfolder, "sub_existing.pdf"))
        
        watcher = FolderWatcher()
        watcher.set_folder(temp_dir, recursive=False)
        
        # Test non-recursive scan
        files = watcher.scan_existing_files()
        if len(files) == 2:  # Should find 2 PDFs in root folder
            print("✓ Non-recursive scan found correct number of files (2)")
        else:
            print(f"✗ Non-recursive scan found {len(files)} files (expected 2)")
            return False
        
        # Test recursive scan
        watcher.set_folder(temp_dir, recursive=True)
        files = watcher.scan_existing_files()
        if len(files) == 3:  # Should find 3 PDFs total
            print("✓ Recursive scan found correct number of files (3)")
        else:
            print(f"✗ Recursive scan found {len(files)} files (expected 3)")
            return False
        
        # Test with naming filter
        watcher.set_naming_filter("fax_*.pdf")
        files = watcher.scan_existing_files()
        if len(files) == 1:  # Should find 1 PDF matching filter
            print("✓ Filtered scan found correct number of files (1)")
        else:
            print(f"✗ Filtered scan found {len(files)} files (expected 1)")
            return False
    
    return True

def main():
    """Main test function"""
    setup_logging()
    
    print("MCFax Application - Folder Monitoring Module Test")
    print("Testing Core Component 1.1")
    print()
    
    # Test folder validation
    if not test_folder_validation():
        print("\n❌ Folder validation test failed!")
        return False
    
    # Test folder info
    if not test_folder_info():
        print("\n❌ Folder info test failed!")
        return False
    
    # Test folder watcher
    if not test_folder_watcher():
        print("\n❌ Folder watcher test failed!")
        return False
    
    # Test existing file scan
    if not test_existing_file_scan():
        print("\n❌ Existing file scan test failed!")
        return False
    
    print("\n" + "=" * 50)
    print("🎉 All Folder Monitoring tests passed!")
    print("✓ Folder Monitoring Module (1.1) - Working")
    print("=" * 50)
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
