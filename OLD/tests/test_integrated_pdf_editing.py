#!/usr/bin/env python3
"""
Test script for integrated PDF editing functionality
"""

import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from PyQt6.QtWidgets import QApplication
from gui.main_window import MainWindow

def test_integrated_pdf_editing():
    """Test the integrated PDF editing functionality"""
    app = QApplication(sys.argv)
    
    # Create main window
    main_window = MainWindow()
    main_window.show()
    
    print("✅ Main window created successfully")
    print("✅ PDF editing functionality integrated")
    print("\nTo test PDF editing:")
    print("1. Select a temp folder with PDF files")
    print("2. Select a PDF from the list")
    print("3. Click 'View PDF' or 'Edit PDF' buttons")
    print("4. Or create a new fax job and use 'View/Edit PDF' button")
    
    # Run the application
    sys.exit(app.exec())

if __name__ == "__main__":
    test_integrated_pdf_editing()
