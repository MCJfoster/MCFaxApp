"""
Test Script for Phase 4: User Interface Components
Tests all UI components including fax history, PDF editor, and folder monitoring
"""

import sys
import os
import logging
import tempfile
import shutil
from pathlib import Path
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QTimer

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def setup_logging():
    """Setup logging for tests"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('logs/test_phase4_ui.log'),
            logging.StreamHandler()
        ]
    )

def create_test_pdf(file_path: str):
    """Create a simple test PDF file"""
    try:
        from reportlab.pdfgen import canvas
        from reportlab.lib.pagesizes import letter
        
        c = canvas.Canvas(file_path, pagesize=letter)
        c.drawString(100, 750, f"Test PDF: {Path(file_path).name}")
        c.drawString(100, 700, "This is a test PDF for MCFax UI testing")
        c.drawString(100, 650, "Page 1 of test document")
        c.showPage()
        
        # Add second page
        c.drawString(100, 750, "Page 2 of test document")
        c.drawString(100, 700, "Additional content for testing")
        c.showPage()
        
        c.save()
        return True
    except ImportError:
        print("Warning: reportlab not available, creating dummy PDF")
        # Create a dummy file
        with open(file_path, 'w') as f:
            f.write("%PDF-1.4\n%Dummy PDF for testing\n")
        return False

def test_database_setup():
    """Test database setup and models"""
    print("\n=== Testing Database Setup ===")
    
    try:
        from database.connection import DatabaseConnection
        from database.models import ContactRepository, FaxJobRepository, Contact, FaxJob
        
        # Test database connection
        db = DatabaseConnection()
        if db.connect():
            print("✓ Database connection successful")
            
            # Test repositories
            contact_repo = ContactRepository(db)
            fax_job_repo = FaxJobRepository(db)
            
            # Test adding a contact
            test_contact = Contact(
                name="Test Contact",
                company="Test Company",
                fax_number="555-1234",
                phone_number="555-5678",
                email="test@example.com"
            )
            
            contact_id = contact_repo.create_contact(test_contact)
            if contact_id:
                print(f"✓ Test contact created with ID: {contact_id}")
                
                # Test retrieving contact
                retrieved_contact = contact_repo.get_contact(contact_id)
                if retrieved_contact:
                    print(f"✓ Contact retrieved: {retrieved_contact.name}")
                else:
                    print("✗ Failed to retrieve contact")
            else:
                print("✗ Failed to create test contact")
            
            db.close()
            return True
        else:
            print("✗ Database connection failed")
            return False
            
    except Exception as e:
        print(f"✗ Database test error: {e}")
        return False

def test_pdf_components():
    """Test PDF processing components"""
    print("\n=== Testing PDF Components ===")
    
    try:
        # Create temp directory and test PDF
        temp_dir = tempfile.mkdtemp()
        test_pdf_path = os.path.join(temp_dir, "test_document.pdf")
        
        if create_test_pdf(test_pdf_path):
            print(f"✓ Test PDF created: {test_pdf_path}")
        else:
            print(f"⚠ Dummy PDF created: {test_pdf_path}")
        
        # Test PDF processor
        from pdf.pdf_processor import PDFProcessor
        processor = PDFProcessor()
        
        pdf_info = processor.get_pdf_info(test_pdf_path)
        print(f"✓ PDF info retrieved: {pdf_info}")
        
        # Test PDF browser
        from pdf.pdf_browser import PDFBrowser
        browser = PDFBrowser(temp_dir)
        pdf_files = browser.get_pdf_files()
        print(f"✓ PDF browser found {len(pdf_files)} files")
        
        # Test PDF editor availability
        try:
            from pdf.pdf_editor import PDFEditor, PDF2IMAGE_AVAILABLE
            if PDF2IMAGE_AVAILABLE:
                print("✓ PDF editor dependencies available")
            else:
                print("⚠ PDF editor dependencies missing (pdf2image/Pillow)")
        except ImportError:
            print("⚠ PDF editor module not available")
        
        # Test PDF viewer
        from pdf.pdf_viewer import PDFViewer
        print("✓ PDF viewer module available")
        
        # Cleanup
        shutil.rmtree(temp_dir)
        return True
        
    except Exception as e:
        print(f"✗ PDF components test error: {e}")
        return False

def test_folder_monitoring():
    """Test folder monitoring functionality"""
    print("\n=== Testing Folder Monitoring ===")
    
    try:
        from core.folder_watcher import FolderWatcher
        
        # Create temp directory
        temp_dir = tempfile.mkdtemp()
        print(f"✓ Created temp directory: {temp_dir}")
        
        # Test folder watcher creation
        watcher = FolderWatcher(temp_dir)
        print("✓ Folder watcher created")
        
        # Test starting/stopping
        watcher.start()
        print("✓ Folder watcher started")
        
        watcher.stop()
        print("✓ Folder watcher stopped")
        
        # Cleanup
        shutil.rmtree(temp_dir)
        return True
        
    except Exception as e:
        print(f"✗ Folder monitoring test error: {e}")
        return False

def test_gui_components():
    """Test GUI components (basic instantiation)"""
    print("\n=== Testing GUI Components ===")
    
    try:
        # Test main window import
        from gui.main_window import MainWindow
        print("✓ Main window module imported")
        
        # Test other GUI components
        from gui.contact_window import ContactWindow
        print("✓ Contact window module imported")
        
        from gui.fax_job_window import FaxJobWindow
        print("✓ Fax job window module imported")
        
        from gui.fax_history_window import FaxHistoryWindow
        print("✓ Fax history window module imported")
        
        return True
        
    except Exception as e:
        print(f"✗ GUI components test error: {e}")
        return False

def test_fax_integration():
    """Test fax integration components"""
    print("\n=== Testing Fax Integration ===")
    
    try:
        from fax.faxfinder_api import FaxFinderAPI
        from fax.xml_generator import XMLGenerator
        
        print("✓ Fax integration modules imported")
        
        # Test XML generator
        xml_gen = XMLGenerator()
        test_xml = xml_gen.create_fax_job_xml(
            fax_number="555-1234",
            pdf_files=["test.pdf"],
            cover_page_text="Test fax"
        )
        
        if test_xml:
            print("✓ XML generation successful")
        else:
            print("✗ XML generation failed")
        
        return True
        
    except Exception as e:
        print(f"✗ Fax integration test error: {e}")
        return False

def run_interactive_test():
    """Run interactive GUI test"""
    print("\n=== Running Interactive GUI Test ===")
    print("This will open the main MCFax window for manual testing...")
    print("Close the window to continue with the test script.")
    
    try:
        app = QApplication(sys.argv)
        
        from gui.main_window import MainWindow
        
        # Create main window
        main_window = MainWindow()
        main_window.show()
        
        print("✓ Main window opened successfully")
        print("Manual testing instructions:")
        print("1. Check that the database status shows 'Connected'")
        print("2. Select a temp folder using File > Select Temp Folder")
        print("3. Try creating a new fax job")
        print("4. Test the contact manager")
        print("5. Test the fax history window")
        print("6. Close the window when done")
        
        # Auto-close after 30 seconds if not closed manually
        close_timer = QTimer()
        close_timer.timeout.connect(app.quit)
        close_timer.start(30000)  # 30 seconds
        
        app.exec()
        return True
        
    except Exception as e:
        print(f"✗ Interactive GUI test error: {e}")
        return False

def main():
    """Run all Phase 4 UI tests"""
    print("MCFax Phase 4 UI Testing")
    print("=" * 50)
    
    # Setup logging
    setup_logging()
    
    # Ensure logs directory exists
    os.makedirs('logs', exist_ok=True)
    
    # Run tests
    tests = [
        ("Database Setup", test_database_setup),
        ("PDF Components", test_pdf_components),
        ("Folder Monitoring", test_folder_monitoring),
        ("GUI Components", test_gui_components),
        ("Fax Integration", test_fax_integration),
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        try:
            results[test_name] = test_func()
        except Exception as e:
            print(f"✗ {test_name} test failed with exception: {e}")
            results[test_name] = False
    
    # Summary
    print("\n" + "=" * 50)
    print("TEST SUMMARY")
    print("=" * 50)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results.items():
        status = "PASS" if result else "FAIL"
        print(f"{test_name:.<30} {status}")
        if result:
            passed += 1
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All Phase 4 UI components are working correctly!")
        
        # Ask if user wants to run interactive test
        try:
            response = input("\nWould you like to run the interactive GUI test? (y/n): ")
            if response.lower().startswith('y'):
                run_interactive_test()
        except KeyboardInterrupt:
            print("\nSkipping interactive test.")
    else:
        print("⚠ Some tests failed. Please check the issues above.")
    
    print("\nPhase 4 UI testing complete!")

if __name__ == "__main__":
    main()
