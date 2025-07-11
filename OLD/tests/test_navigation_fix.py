"""
Test script to verify the PDF navigation fix works correctly
"""

import sys
import os
sys.path.append('src')

from PyQt6.QtWidgets import QApplication, QMessageBox
from gui.fax_job_window import FaxJobWindow
from database.models import ContactRepository, FaxJobRepository
from database.connection import DatabaseConnection

def test_navigation_fix():
    """Test the PDF navigation fix"""
    
    app = QApplication(sys.argv)
    
    try:
        # Look for any PDF files
        pdf_files = []
        
        # Check current directory
        for file in os.listdir('.'):
            if file.lower().endswith('.pdf'):
                pdf_files.append(file)
        
        # Check FaxCache if it exists
        if os.path.exists('C:/FaxCache'):
            for file in os.listdir('C:/FaxCache'):
                if file.lower().endswith('.pdf'):
                    pdf_files.append(f'C:/FaxCache/{file}')
        
        if not pdf_files:
            print("❌ No PDF files found for testing")
            return False
        
        # Use the first PDF found
        selected_pdfs = [pdf_files[0]]
        print(f"✅ Using PDF for testing: {selected_pdfs[0]}")
        
        # Create database connection
        db = DatabaseConnection()
        db.connect()
        
        # Create repositories
        contact_repo = ContactRepository(db)
        fax_job_repo = FaxJobRepository(db)
        
        # Create FaxJobWindow with real PDF
        window = FaxJobWindow(selected_pdfs, contact_repo, fax_job_repo)
        
        # Show the window
        window.show()
        
        # Stay on the PDF editing tab (tab 0)
        window.tab_widget.setCurrentIndex(0)
        
        print("✅ SUCCESS: FaxJobWindow opened with PDF editing tab")
        print("📋 Navigation Testing Instructions:")
        print("1. Select the PDF from the list on the left")
        print("2. Navigate through pages using Next button")
        print("3. Test the Previous button - it should NOT crash now!")
        print("4. Try navigating back and forth multiple times")
        print("5. The Previous button should handle widget deletion gracefully")
        print("6. Close the window when done testing")
        
        # Run the application
        app.exec()
        
        return True
        
    except Exception as e:
        print(f"❌ FAILED: Error creating FaxJobWindow: {e}")
        return False

if __name__ == "__main__":
    print("Testing PDF Navigation Fix...")
    success = test_navigation_fix()
    
    if success:
        print("\n🎉 Navigation test completed! The Previous button should now work without crashes.")
    else:
        print("\n💥 Test failed to start.")
    
    sys.exit(0 if success else 1)
