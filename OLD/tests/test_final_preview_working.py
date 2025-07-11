"""
Test script to verify the final preview functionality works with real PDF
"""

import sys
import os
sys.path.append('src')

from PyQt6.QtWidgets import QApplication, QMessageBox
from gui.fax_job_window import FaxJobWindow
from database.models import ContactRepository, FaxJobRepository
from database.connection import DatabaseConnection

def test_final_preview_with_real_pdf():
    """Test the final preview functionality with a real PDF"""
    
    app = QApplication(sys.argv)
    
    try:
        # Look for any PDF files in the current directory or FaxCache
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
            print("Please place a PDF file in the current directory or C:/FaxCache")
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
        
        # Navigate to the preview tab
        window.tab_widget.setCurrentIndex(3)  # Preview tab is index 3
        
        print("✅ SUCCESS: FaxJobWindow opened with real PDF")
        print("📋 Testing Instructions:")
        print("1. Go to the Recipient tab and select a contact")
        print("2. Go to the Cover Page tab and fill out sender info")
        print("3. Go to the Preview tab")
        print("4. Click 'Generate Final Preview' - this should work now!")
        print("5. Test the navigation buttons (Previous/Next)")
        print("6. Test the zoom controls")
        print("7. Verify the preview shows cover page + PDF content")
        print("8. Close the window when done testing")
        
        # Run the application
        app.exec()
        
        return True
        
    except Exception as e:
        print(f"❌ FAILED: Error creating FaxJobWindow: {e}")
        return False

if __name__ == "__main__":
    print("Testing Final Preview with Real PDF...")
    success = test_final_preview_with_real_pdf()
    
    if success:
        print("\n🎉 Test completed! The final preview should now work correctly.")
    else:
        print("\n💥 Test failed to start.")
    
    sys.exit(0 if success else 1)
