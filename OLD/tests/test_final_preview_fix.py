"""
Test script to verify the final preview functionality works correctly
"""

import sys
import os
sys.path.append('src')

from PyQt6.QtWidgets import QApplication, QMessageBox
from gui.fax_job_window import FaxJobWindow
from database.models import ContactRepository, FaxJobRepository
from database.connection import DatabaseConnection

def test_final_preview():
    """Test the final preview functionality"""
    
    app = QApplication(sys.argv)
    
    try:
        # Create database connection
        db = DatabaseConnection()
        db.connect()
        
        # Create repositories
        contact_repo = ContactRepository(db)
        fax_job_repo = FaxJobRepository(db)
        
        # Create FaxJobWindow with test data
        selected_pdfs = ["test.pdf"]  # Mock PDF file
        window = FaxJobWindow(selected_pdfs, contact_repo, fax_job_repo)
        
        # Show the window
        window.show()
        
        # Navigate to the preview tab
        window.tab_widget.setCurrentIndex(3)  # Preview tab is index 3
        
        print("✅ SUCCESS: FaxJobWindow opened successfully")
        print("📋 Instructions:")
        print("1. Fill out the recipient and cover page information")
        print("2. Go to the Preview tab")
        print("3. Click 'Generate Final Preview'")
        print("4. Test the navigation buttons (Previous/Next)")
        print("5. Test the zoom controls")
        print("6. Close the window when done testing")
        
        # Run the application
        app.exec()
        
        return True
        
    except Exception as e:
        print(f"❌ FAILED: Error creating FaxJobWindow: {e}")
        return False

if __name__ == "__main__":
    print("Testing Final Preview Fix...")
    success = test_final_preview()
    
    if success:
        print("\n🎉 Test completed! Check if the final preview works correctly.")
    else:
        print("\n💥 Test failed to start.")
    
    sys.exit(0 if success else 1)
