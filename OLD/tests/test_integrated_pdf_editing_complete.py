#!/usr/bin/env python3
"""
Test script for the complete integrated PDF editing functionality
Tests the new integrated PDF viewer/editor in the fax job window
"""

import sys
import os
import logging
from pathlib import Path
from PyQt6.QtWidgets import QApplication, QMessageBox
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from database.connection import DatabaseConnection
from database.models import ContactRepository, FaxJobRepository
from gui.fax_job_window import FaxJobWindow

def setup_logging():
    """Setup logging configuration"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('logs/test_integrated_editing.log'),
            logging.StreamHandler()
        ]
    )

def create_test_pdf():
    """Create a simple test PDF for testing"""
    try:
        from reportlab.pdfgen import canvas
        from reportlab.lib.pagesizes import letter
        
        test_pdf_path = "test_integrated_editing.pdf"
        
        # Create a simple multi-page PDF
        c = canvas.Canvas(test_pdf_path, pagesize=letter)
        
        # Page 1
        c.drawString(100, 750, "Test PDF for Integrated Editing - Page 1")
        c.drawString(100, 700, "This is some text that can be redacted")
        c.drawString(100, 650, "This text can be highlighted")
        c.drawString(100, 600, "You can add annotations here")
        c.drawString(100, 550, "Test drawing and editing functionality")
        c.showPage()
        
        # Page 2
        c.drawString(100, 750, "Test PDF for Integrated Editing - Page 2")
        c.drawString(100, 700, "Second page content")
        c.drawString(100, 650, "More text for testing")
        c.drawString(100, 600, "This page can be excluded")
        c.showPage()
        
        # Page 3
        c.drawString(100, 750, "Test PDF for Integrated Editing - Page 3")
        c.drawString(100, 700, "Final page content")
        c.drawString(100, 650, "Test page navigation")
        c.showPage()
        
        c.save()
        
        print(f"✅ Created test PDF: {test_pdf_path}")
        return test_pdf_path
        
    except ImportError:
        print("⚠️ ReportLab not available, using existing PDF if available")
        # Look for any existing PDF in the current directory
        for pdf_file in Path(".").glob("*.pdf"):
            print(f"✅ Using existing PDF: {pdf_file}")
            return str(pdf_file)
        
        print("❌ No PDF available for testing")
        return None

def test_integrated_pdf_editing():
    """Test the integrated PDF editing functionality"""
    print("🧪 Testing Integrated PDF Editing Functionality")
    print("=" * 60)
    
    # Setup logging
    setup_logging()
    
    # Create test PDF
    test_pdf = create_test_pdf()
    if not test_pdf:
        print("❌ Cannot run test without a PDF file")
        return False
    
    # Create Qt application
    app = QApplication(sys.argv)
    
    try:
        # Setup database
        db = DatabaseConnection()
        contact_repo = ContactRepository(db)
        fax_job_repo = FaxJobRepository(db)
        
        # Create fax job window with test PDF
        selected_pdfs = [test_pdf]
        fax_window = FaxJobWindow(selected_pdfs, contact_repo, fax_job_repo)
        
        print("✅ Created fax job window with integrated PDF editing")
        
        # Show the window
        fax_window.show()
        
        # Test instructions
        instructions = """
🎯 INTEGRATED PDF EDITING TEST INSTRUCTIONS:

1. PDF LOADING:
   • Select the test PDF from the list on the left
   • Verify the PDF loads in the right panel
   • Check that all controls are enabled

2. NAVIGATION:
   • Use Previous/Next buttons to navigate pages
   • Verify page counter updates correctly
   • Test zoom in/out functionality

3. DRAWING TOOLS:
   • Click "Redact" and draw on the PDF
   • Try different brush sizes (1-50)
   • Test all three colors: Black, Grey, White
   • Switch between Redact, Highlight, and Add Text modes

4. BRUSH CONTROLS:
   • Adjust brush size slider
   • Verify size label updates (e.g., "15px")
   • Click color buttons (Black/Grey/White)
   • Verify only one color is selected at a time

5. EDITING FEATURES:
   • Draw some redactions on the PDF
   • Use Undo button to undo last action
   • Try excluding a page with the "Exclude Page" button
   • Verify excluded pages show red overlay and "EXCLUDED" text

6. INTEGRATION:
   • Verify all controls work together smoothly
   • Check that the PDF viewer updates in real-time
   • Test that brush settings apply immediately

7. LAYOUT:
   • Verify the left panel is narrower (PDF list)
   • Verify the right panel is wider (PDF viewer/editor)
   • Check that all controls fit properly in the toolbar

✅ SUCCESS CRITERIA:
   - PDF loads and displays correctly
   - All drawing tools work (redact, highlight, text)
   - Brush size and color controls function
   - Page navigation works
   - Undo functionality works
   - Page exclusion works
   - Layout is properly proportioned

❌ FAILURE INDICATORS:
   - PDF doesn't load or shows errors
   - Drawing tools don't work or crash
   - Controls are disabled when they should be enabled
   - Brush settings don't apply
   - Layout is broken or cramped

Press OK to start testing, or Cancel to exit.
        """
        
        # Show instructions
        msg_box = QMessageBox()
        msg_box.setWindowTitle("Integrated PDF Editing Test")
        msg_box.setText(instructions)
        msg_box.setStandardButtons(QMessageBox.StandardButton.Ok | QMessageBox.StandardButton.Cancel)
        msg_box.setDefaultButton(QMessageBox.StandardButton.Ok)
        
        if msg_box.exec() == QMessageBox.StandardButton.Ok:
            print("🚀 Starting integrated PDF editing test...")
            print("📝 Follow the instructions in the fax job window")
            print("🔍 Test all the integrated PDF editing features")
            
            # Run the application
            result = app.exec()
            
            print("\n" + "=" * 60)
            print("🏁 Test completed!")
            print("📊 Please verify that all features worked correctly")
            
            return result == 0
        else:
            print("❌ Test cancelled by user")
            return False
            
    except Exception as e:
        print(f"❌ Error during test: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        # Cleanup
        if test_pdf and test_pdf.startswith("test_"):
            try:
                os.remove(test_pdf)
                print(f"🧹 Cleaned up test file: {test_pdf}")
            except:
                pass

if __name__ == "__main__":
    print("🧪 Integrated PDF Editing Test")
    print("Testing the new integrated PDF viewer/editor functionality")
    print("This test verifies that PDF editing works directly in the fax job window")
    print()
    
    success = test_integrated_pdf_editing()
    
    if success:
        print("✅ Integrated PDF editing test completed successfully!")
        print("🎉 The new integrated functionality is working!")
    else:
        print("❌ Integrated PDF editing test failed!")
        print("🔧 Check the implementation for issues")
    
    sys.exit(0 if success else 1)
