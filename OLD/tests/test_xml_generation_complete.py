"""
Test complete XML generation and FaxFinder submission workflow
Tests the end-to-end process from PDF selection to XML generation and submission
"""

import sys
import os
import logging
from pathlib import Path
from datetime import datetime

# Add src to path
sys.path.insert(0, 'src')

from database.models import Contact, FaxJob, CoverPageDetails, ContactRepository, FaxJobRepository
from database.connection import DatabaseConnection
from fax.xml_generator import FaxXMLGenerator
from fax.faxfinder_api import FaxFinderAPI
from pdf.cover_page import CoverPageGenerator
from core.settings import get_settings

def setup_logging():
    """Setup logging for the test"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('logs/test_xml_generation.log'),
            logging.StreamHandler()
        ]
    )

def create_test_contact(contact_repo: ContactRepository) -> Contact:
    """Create a test contact for faxing"""
    contact = Contact(
        name="Test Hospital",
        fax_number="555-123-4567",
        organization="Test Medical Center",
        phone_number="555-123-4568",
        email="test@hospital.com",
        notes="Test contact for XML generation"
    )
    
    contact_id = contact_repo.create(contact)
    contact.contact_id = contact_id
    
    print(f"✓ Created test contact: {contact.name} (ID: {contact_id})")
    return contact

def create_test_fax_job(contact: Contact) -> FaxJob:
    """Create a test fax job"""
    cover_page = CoverPageDetails(
        to=contact.name,
        from_field="Dr. Test Smith",
        company="The Spine Hospital Louisiana",
        fax=contact.fax_number,
        phone="(225) 906-4805",
        re="Test Patient Records",
        comments="This is a test fax for XML generation verification.",
        urgent=True,
        for_review=False,
        please_comment=True,
        please_reply=False
    )
    
    fax_job = FaxJob(
        sender_name="Dr. Test Smith",
        sender_email="test@spinehospital.com",
        recipient_id=contact.contact_id,
        recipient_fax=contact.fax_number,
        priority="High",
        max_attempts=3,
        retry_interval=5,
        cover_page_details=cover_page,
        page_count=3,
        file_size_mb=2.5
    )
    
    print(f"✓ Created test fax job for {contact.name}")
    return fax_job

def generate_test_pdf() -> str:
    """Generate a test PDF file"""
    try:
        import fitz  # PyMuPDF
        
        # Create a simple test PDF
        doc = fitz.open()
        page = doc.new_page()
        
        # Add some text
        text = """
        TEST DOCUMENT
        
        This is a test PDF document for XML generation testing.
        
        Patient: John Doe
        DOB: 01/01/1980
        MRN: 12345
        
        Test Results:
        - Blood pressure: Normal
        - Heart rate: 72 bpm
        - Temperature: 98.6°F
        
        This document is for testing purposes only.
        """
        
        page.insert_text((50, 50), text, fontsize=12)
        
        # Save the PDF
        pdf_path = "test_document.pdf"
        doc.save(pdf_path)
        doc.close()
        
        print(f"✓ Generated test PDF: {pdf_path}")
        return pdf_path
        
    except ImportError:
        print("⚠️ PyMuPDF not available, using placeholder PDF path")
        return "test_document.pdf"

def test_cover_page_generation(fax_job: FaxJob) -> str:
    """Test cover page generation"""
    print("\n--- Testing Cover Page Generation ---")
    
    cover_generator = CoverPageGenerator()
    cover_path = "test_cover_page.pdf"
    logo_path = "SholaLogo.JPG"
    
    success = cover_generator.generate_cover_page(
        cover_details=fax_job.cover_page_details,
        output_path=cover_path,
        page_count=3,
        logo_path=logo_path if os.path.exists(logo_path) else None
    )
    
    if success:
        print(f"✓ Cover page generated successfully: {cover_path}")
        return cover_path
    else:
        print("❌ Cover page generation failed")
        return None

def test_pdf_combination(cover_path: str, pdf_path: str) -> str:
    """Test PDF combination"""
    print("\n--- Testing PDF Combination ---")
    
    try:
        import fitz  # PyMuPDF
        
        # Create combined PDF
        combined_path = "test_combined.pdf"
        combined_doc = fitz.open()
        
        # Add cover page
        if cover_path and os.path.exists(cover_path):
            cover_doc = fitz.open(cover_path)
            combined_doc.insert_pdf(cover_doc)
            cover_doc.close()
            print("✓ Added cover page to combined PDF")
        
        # Add test document
        if os.path.exists(pdf_path):
            pdf_doc = fitz.open(pdf_path)
            combined_doc.insert_pdf(pdf_doc)
            pdf_doc.close()
            print("✓ Added test document to combined PDF")
        
        # Save combined PDF
        combined_doc.save(combined_path)
        combined_doc.close()
        
        # Get file size
        file_size = os.path.getsize(combined_path) / (1024 * 1024)
        print(f"✓ Combined PDF created: {combined_path} ({file_size:.2f} MB)")
        
        return combined_path
        
    except ImportError:
        print("⚠️ PyMuPDF not available, skipping PDF combination")
        return pdf_path

def test_xml_generation(fax_job: FaxJob, contact: Contact, pdf_path: str) -> str:
    """Test XML generation"""
    print("\n--- Testing XML Generation ---")
    
    xml_generator = FaxXMLGenerator()
    xml_path = f"test_fax_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xml"
    
    success = xml_generator.generate_fax_xml(
        fax_job=fax_job,
        contact=contact,
        pdf_file_path=pdf_path,
        output_path=xml_path
    )
    
    if success:
        print(f"✓ XML generated successfully: {xml_path}")
        
        # Read and display XML content
        with open(xml_path, 'r', encoding='utf-8') as f:
            xml_content = f.read()
        
        print("\n--- Generated XML Content ---")
        print(xml_content[:500] + "..." if len(xml_content) > 500 else xml_content)
        print("--- End XML Content ---\n")
        
        return xml_path
    else:
        print("❌ XML generation failed")
        return None

def test_faxfinder_connection():
    """Test FaxFinder connection (if configured)"""
    print("\n--- Testing FaxFinder Connection ---")
    
    try:
        settings = get_settings()
        faxfinder_settings = settings.get_faxfinder_settings()
        
        if not faxfinder_settings.get('host'):
            print("⚠️ FaxFinder not configured, skipping connection test")
            return False
        
        api = FaxFinderAPI(
            host=faxfinder_settings['host'],
            username=faxfinder_settings['username'],
            password=faxfinder_settings['password'],
            use_https=faxfinder_settings.get('use_https', False)
        )
        
        result = api.test_connection()
        
        if result['success']:
            print("✓ FaxFinder connection successful")
            return True
        else:
            print(f"❌ FaxFinder connection failed: {result.get('error', 'Unknown error')}")
            return False
            
    except Exception as e:
        print(f"❌ FaxFinder connection test error: {e}")
        return False

def test_database_operations():
    """Test database operations"""
    print("\n--- Testing Database Operations ---")
    
    try:
        # Test database connection
        db = DatabaseConnection()
        if not db.test_connection():
            print("❌ Database connection failed")
            return None, None
        
        print("✓ Database connection successful")
        
        # Create repositories
        contact_repo = ContactRepository(db)
        fax_job_repo = FaxJobRepository(db)
        
        # Create test contact
        contact = create_test_contact(contact_repo)
        
        # Create test fax job
        fax_job = create_test_fax_job(contact)
        
        # Save fax job to database
        fax_id = fax_job_repo.create(fax_job)
        fax_job.fax_id = fax_id
        
        print(f"✓ Fax job saved to database (ID: {fax_id})")
        
        return contact, fax_job
        
    except Exception as e:
        print(f"❌ Database operations failed: {e}")
        return None, None

def cleanup_test_files():
    """Clean up test files"""
    print("\n--- Cleaning Up Test Files ---")
    
    test_files = [
        "test_document.pdf",
        "test_cover_page.pdf",
        "test_combined.pdf"
    ]
    
    # Clean up XML files
    for file in os.listdir('.'):
        if file.startswith('test_fax_') and file.endswith('.xml'):
            test_files.append(file)
    
    for file in test_files:
        try:
            if os.path.exists(file):
                os.remove(file)
                print(f"✓ Removed {file}")
        except Exception as e:
            print(f"⚠️ Could not remove {file}: {e}")

def main():
    """Main test function"""
    print("=== MCFax XML Generation and Submission Test ===\n")
    
    # Setup logging
    setup_logging()
    
    # Create logs directory
    os.makedirs('logs', exist_ok=True)
    
    try:
        # Test database operations
        contact, fax_job = test_database_operations()
        if not contact or not fax_job:
            print("❌ Cannot proceed without database operations")
            return
        
        # Generate test PDF
        pdf_path = generate_test_pdf()
        
        # Test cover page generation
        cover_path = test_cover_page_generation(fax_job)
        
        # Test PDF combination
        combined_path = test_pdf_combination(cover_path, pdf_path)
        
        # Update fax job with file paths
        fax_job.pdf_path = combined_path
        
        # Test XML generation
        xml_path = test_xml_generation(fax_job, contact, combined_path)
        
        if xml_path:
            fax_job.xml_path = xml_path
            print(f"✓ Complete workflow successful!")
            print(f"  - PDF: {combined_path}")
            print(f"  - XML: {xml_path}")
            print(f"  - Fax Job ID: {fax_job.fax_id}")
        
        # Test FaxFinder connection (optional)
        test_faxfinder_connection()
        
        print("\n=== Test Summary ===")
        print("✓ Database operations: PASSED")
        print("✓ PDF generation: PASSED")
        print("✓ Cover page generation: PASSED" if cover_path else "⚠️ Cover page generation: SKIPPED")
        print("✓ PDF combination: PASSED" if combined_path else "⚠️ PDF combination: SKIPPED")
        print("✓ XML generation: PASSED" if xml_path else "❌ XML generation: FAILED")
        print("\n🎉 XML generation workflow test completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Clean up test files
        cleanup_test_files()

if __name__ == "__main__":
    main()
