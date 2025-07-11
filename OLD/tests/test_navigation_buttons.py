"""
Test script to verify navigation buttons work in the integrated PDF viewer
"""

import sys
import logging
from pathlib import Path
from PyQt6.QtWidgets import QApplication
from src.gui.fax_job_window import FaxJobWindow
from src.database.models import ContactRepository, FaxJobRepository
from src.database.connection import DatabaseConnection

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

def test_navigation():
    """Test the navigation buttons"""
    app = QApplication(sys.argv)
    
    # Setup database connection
    db = DatabaseConnection()
    db.connect()
    
    # Create repositories
    contact_repo = ContactRepository(db)
    fax_job_repo = FaxJobRepository(db)
    
    # Test PDF path
    test_pdf = "C:/FaxCache/test.pdf"
    if not Path(test_pdf).exists():
        print(f"Test PDF not found: {test_pdf}")
        return
    
    # Create fax job window
    window = FaxJobWindow([test_pdf], contact_repo, fax_job_repo)
    window.show()
    
    print("Fax Job Window opened. Test the navigation buttons:")
    print("1. Select the PDF from the list")
    print("2. Try the Previous/Next buttons")
    print("3. Try the Exclude Page button")
    print("4. Check the logs for navigation messages")
    
    app.exec()

if __name__ == "__main__":
    test_navigation()
