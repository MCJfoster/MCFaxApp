#!/usr/bin/env python3
"""
Test script for UI improvements to the Fax Job Window
Tests the new progress button and enhanced summary functionality
"""

import sys
import os
import logging
from pathlib import Path
from PyQt6.QtWidgets import QApplication, QMessageBox
from PyQt6.QtCore import QTimer

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from gui.fax_job_window import FaxJobWindow
from database.models import ContactRepository, FaxJobRepository
from database.connection import get_database_connection

def setup_logging():
    """Setup logging for the test"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('logs/test_ui_improvements.log'),
            logging.StreamHandler()
        ]
    )

def create_test_pdfs():
    """Create some test PDF files for testing"""
    test_pdfs = []
    
    # Check if we have any existing PDFs in the current directory
    for pdf_file in Path('.').glob('*.pdf'):
        test_pdfs.append(str(pdf_file))
        if len(test_pdfs) >= 3:  # Limit to 3 for testing
            break
    
    if not test_pdfs:
        print("No PDF files found in current directory for testing.")
        print("Please add some PDF files to test the fax job window.")
        return []
    
    return test_pdfs

def test_ui_improvements():
    """Test the UI improvements"""
    print("Testing UI Improvements...")
    print("=" * 50)
    
    # Create test PDFs list
    test_pdfs = create_test_pdfs()
    if not test_pdfs:
        return False
    
    print(f"Found {len(test_pdfs)} test PDF files:")
    for pdf in test_pdfs:
        print(f"  - {Path(pdf).name}")
    
    try:
        # Create database connection
        conn = get_database_connection()
        
        # Create repositories
        contact_repo = ContactRepository(conn)
        fax_job_repo = FaxJobRepository(conn)
        
        # Create and show the fax job window
        print("\nOpening Fax Job Window...")
        fax_window = FaxJobWindow(test_pdfs, contact_repo, fax_job_repo)
        
        # Show the window
        fax_window.show()
        
        print("\nUI Improvements to test:")
        print("1. Cover Page tab should NOT have textual preview (only visual)")
        print("2. Preview & Submit tab should have enhanced summary with:")
        print("   - Detailed recipient info")
        print("   - File sizes and page counts")
        print("   - 36MB size validation")
        print("   - Validation status")
        print("3. Generate Final Preview button should:")
        print("   - Show progress animation from left to right")
        print("   - Change text to 'Generating Final Preview' during processing")
        print("   - Show progress percentage")
        print("4. Next button should be hidden on the Preview & Submit tab")
        print("5. Summary should only update when clicking on Preview & Submit tab")
        
        print("\nTest Instructions:")
        print("1. Navigate through the tabs and observe the changes")
        print("2. Go to Preview & Submit tab and check the enhanced summary")
        print("3. Try clicking 'Generate Final Preview' to see the progress animation")
        print("4. Verify that the Next button is hidden on the final tab")
        print("5. Close the window when done testing")
        
        # Set up a timer to provide testing guidance
        def show_testing_tips():
            QMessageBox.information(
                fax_window,
                "UI Testing Tips",
                "UI Improvements Active!\n\n"
                "✓ Cover page tab: No text preview (visual only)\n"
                "✓ Progress button: Animated progress bar\n"
                "✓ Enhanced summary: Detailed info with validation\n"
                "✓ Next button: Hidden on final tab\n\n"
                "Navigate through tabs to see the improvements!"
            )
        
        # Show tips after 2 seconds
        QTimer.singleShot(2000, show_testing_tips)
        
        return True
        
    except Exception as e:
        print(f"Error during testing: {e}")
        logging.error(f"Test error: {e}")
        return False

def main():
    """Main test function"""
    print("MCFax UI Improvements Test")
    print("=" * 40)
    
    # Setup logging
    setup_logging()
    
    # Create logs directory
    Path("logs").mkdir(exist_ok=True)
    
    # Create QApplication
    app = QApplication(sys.argv)
    
    try:
        # Run the test
        success = test_ui_improvements()
        
        if success:
            print("\nTest setup complete! Interact with the UI to test improvements.")
            print("Close the fax job window to exit the test.")
            
            # Run the application
            sys.exit(app.exec())
        else:
            print("Test setup failed!")
            return 1
            
    except KeyboardInterrupt:
        print("\nTest interrupted by user")
        return 0
    except Exception as e:
        print(f"Test failed with error: {e}")
        logging.error(f"Test failed: {e}")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
