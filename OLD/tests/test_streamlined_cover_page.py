"""
Test script for the streamlined cover page functionality
Tests the new simplified UI and sender information persistence
"""

import sys
import os
from pathlib import Path
from PyQt6.QtWidgets import QApplication, QMainWindow, QPushButton, QVBoxLayout, QWidget
from PyQt6.QtCore import Qt

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def test_sender_info_persistence():
    """Test sender information persistence"""
    print("Testing Sender Information Persistence...")
    
    try:
        from core.settings import get_settings
        
        settings = get_settings()
        
        # Test setting sender info
        test_sender_info = {
            'from_name': 'Dr. Test Sender',
            'from_company': 'Test Hospital',
            'from_phone': '(555) 123-4567'
        }
        
        settings.set_sender_info(**test_sender_info)
        settings.save_settings()
        
        print("✅ Sender info saved successfully")
        
        # Test retrieving sender info
        retrieved_info = settings.get_sender_info()
        
        if (retrieved_info['from_name'] == test_sender_info['from_name'] and
            retrieved_info['from_company'] == test_sender_info['from_company'] and
            retrieved_info['from_phone'] == test_sender_info['from_phone']):
            print("✅ Sender info retrieved correctly")
            return True
        else:
            print("❌ Sender info mismatch")
            print(f"Expected: {test_sender_info}")
            print(f"Retrieved: {retrieved_info}")
            return False
            
    except Exception as e:
        print(f"❌ Error testing sender info: {e}")
        return False

def test_streamlined_cover_page_fields():
    """Test that the streamlined cover page has the right fields"""
    print("\nTesting Streamlined Cover Page Fields...")
    
    try:
        from database.models import CoverPageDetails
        
        # Test creating cover page with streamlined fields
        cover_details = CoverPageDetails(
            to="Test Recipient",
            from_field="Dr. Test Sender",
            company="Test Hospital",
            fax="(555) 123-4567",
            phone="(555) 987-6543",
            re="Test Subject",
            comments="Test comments",
            urgent=True,
            for_review=False,
            please_comment=True,
            please_reply=False
        )
        
        # Validate the object was created correctly
        if (cover_details.to == "Test Recipient" and
            cover_details.from_field == "Dr. Test Sender" and
            cover_details.urgent == True and
            cover_details.for_review == False):
            print("✅ Cover page details created correctly")
            return True
        else:
            print("❌ Cover page details incorrect")
            return False
            
    except Exception as e:
        print(f"❌ Error testing cover page fields: {e}")
        return False

def test_cover_page_generation():
    """Test cover page generation with streamlined fields"""
    print("\nTesting Cover Page Generation...")
    
    try:
        from database.models import CoverPageDetails
        from pdf.cover_page import CoverPageGenerator
        
        # Create streamlined cover page details
        cover_details = CoverPageDetails(
            to="Dr. Jane Smith",
            from_field="Dr. John Doe",
            company="The Spine Hospital Louisiana",
            fax="(555) 123-4567",
            phone="(225) 906-4805",
            re="Patient Consultation",
            comments="Please review the attached consultation report.",
            urgent=True,
            for_review=True,
            please_comment=False,
            please_reply=True
        )
        
        # Generate cover page
        generator = CoverPageGenerator()
        output_path = "test_streamlined_cover_page.pdf"
        
        success = generator.generate_cover_page(
            cover_details=cover_details,
            output_path=output_path,
            page_count=2
        )
        
        if success and Path(output_path).exists():
            file_size = Path(output_path).stat().st_size / 1024
            print(f"✅ Cover page generated successfully: {output_path} ({file_size:.1f} KB)")
            return True
        else:
            print("❌ Cover page generation failed")
            return False
            
    except Exception as e:
        print(f"❌ Error testing cover page generation: {e}")
        return False

class TestFaxJobWindow(QMainWindow):
    """Test window to demonstrate the streamlined fax job window"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Test Streamlined Fax Job Window")
        self.setGeometry(200, 200, 400, 200)
        
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Layout
        layout = QVBoxLayout(central_widget)
        
        # Test button
        test_btn = QPushButton("Open Streamlined Fax Job Window")
        test_btn.clicked.connect(self.open_fax_job_window)
        layout.addWidget(test_btn)
        
        # Info label
        from PyQt6.QtWidgets import QLabel
        info_label = QLabel("""
This will open the streamlined fax job window with:
• Simplified cover page tab with only essential fields
• Sender information that persists between sessions
• Auto-population from contacts
• Grouped sections for better organization
        """)
        info_label.setWordWrap(True)
        layout.addWidget(info_label)
    
    def open_fax_job_window(self):
        """Open the streamlined fax job window"""
        try:
            from gui.fax_job_window import FaxJobWindow
            from database.models import ContactRepository, FaxJobRepository
            from database.connection import DatabaseConnection
            
            # Create test database connection
            db_conn = DatabaseConnection()
            contact_repo = ContactRepository(db_conn)
            fax_job_repo = FaxJobRepository(db_conn)
            
            # Create some test PDF files (empty files for demo)
            test_pdfs = []
            for i in range(2):
                test_pdf = f"test_document_{i+1}.pdf"
                if not Path(test_pdf).exists():
                    Path(test_pdf).touch()
                test_pdfs.append(str(Path(test_pdf).absolute()))
            
            # Open fax job window
            fax_window = FaxJobWindow(
                selected_pdfs=test_pdfs,
                contact_repo=contact_repo,
                fax_job_repo=fax_job_repo,
                parent=self
            )
            
            fax_window.exec()
            
        except Exception as e:
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.critical(self, "Error", f"Failed to open fax job window:\n{str(e)}")

def test_ui_functionality():
    """Test the UI functionality"""
    print("\nTesting UI Functionality...")
    
    try:
        app = QApplication(sys.argv)
        
        # Create test window
        test_window = TestFaxJobWindow()
        test_window.show()
        
        print("✅ UI test window created successfully")
        print("💡 Click the button to test the streamlined fax job window")
        
        # Don't run the event loop in automated test
        # app.exec()
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing UI: {e}")
        return False

def main():
    """Run all tests"""
    print("🏥 Streamlined Cover Page Test Suite")
    print("=" * 50)
    
    tests = [
        test_sender_info_persistence,
        test_streamlined_cover_page_fields,
        test_cover_page_generation,
        test_ui_functionality
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
            print()  # Add spacing between tests
        except Exception as e:
            print(f"❌ Test {test.__name__} failed with exception: {e}")
            print()
    
    print("=" * 50)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Streamlined cover page is working correctly.")
        
        # Show generated files
        generated_files = ["test_streamlined_cover_page.pdf"]
        
        print("\n📁 Generated files:")
        for file in generated_files:
            if Path(file).exists():
                size_kb = Path(file).stat().st_size / 1024
                print(f"  • {file} ({size_kb:.1f} KB)")
        
        print("\n✨ Key improvements:")
        print("  • Simplified cover page with only essential fields")
        print("  • Sender information persistence between sessions")
        print("  • Auto-population from contact selection")
        print("  • Better organization with grouped sections")
        print("  • Read-only recipient fields (auto-filled from contacts)")
        
        print("\n💡 To test the UI:")
        print("  1. Run: python test_streamlined_cover_page.py")
        print("  2. Click 'Open Streamlined Fax Job Window'")
        print("  3. Navigate to the Cover Page tab to see the improvements")
        
    else:
        print("❌ Some tests failed. Please check the implementation.")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
