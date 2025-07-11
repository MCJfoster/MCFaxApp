"""
Test script for Phase 3: FaxFinder Integration
Tests XML generation, validation, and prepares for API integration
"""

import os
import sys
import logging
from pathlib import Path
from datetime import datetime

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from database.models import FaxJob, Contact, CoverPageDetails
from fax.xml_generator import FaxXMLGenerator, create_fax_xml, validate_fax_xml
from pdf.cover_page import CoverPageGenerator

def setup_logging():
    """Setup logging for tests"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

def create_test_pdf():
    """Create a simple test PDF for testing"""
    from reportlab.lib.pagesizes import letter
    from reportlab.platypus import SimpleDocTemplate, Paragraph
    from reportlab.lib.styles import getSampleStyleSheet
    
    test_pdf_path = "test_files/test_document.pdf"
    os.makedirs("test_files", exist_ok=True)
    
    doc = SimpleDocTemplate(test_pdf_path, pagesize=letter)
    styles = getSampleStyleSheet()
    
    story = []
    story.append(Paragraph("Test Document for Fax Integration", styles['Title']))
    story.append(Paragraph("This is a test document created for testing the fax integration.", styles['Normal']))
    story.append(Paragraph("Page 1 content goes here.", styles['Normal']))
    
    doc.build(story)
    return test_pdf_path

def test_xml_generation():
    """Test XML generation functionality"""
    print("\n" + "="*60)
    print("TESTING XML GENERATION")
    print("="*60)
    
    # Create test data
    contact = Contact(
        contact_id=1,
        name="John Doe",
        fax_number="+15551234567",
        organization="Test Company",
        phone_number="+15559876543",
        email="john.doe@testcompany.com",
        notes="Test contact for integration testing"
    )
    
    cover_page = CoverPageDetails(
        to="John Doe",
        attn="Accounts Receivable",
        from_field="Jane Smith",
        company="ABC Corporation",
        fax="+15551234567",
        phone="+15559876543",
        date=datetime.now().strftime("%m/%d/%Y"),
        subject="Test Fax Transmission",
        re="Invoice #12345",
        cc="manager@abccorp.com",
        comments="This is a test fax for integration testing.",
        msg="Please process the attached documents at your earliest convenience."
    )
    
    fax_job = FaxJob(
        fax_id=1,
        sender_name="Jane Smith",
        sender_email="jane.smith@abccorp.com",
        recipient_id=1,
        recipient_fax="+15551234567",
        priority="High",
        max_attempts=3,
        retry_interval=5,
        cover_page_details=cover_page
    )
    
    # Create test PDF
    test_pdf_path = create_test_pdf()
    print(f"✓ Created test PDF: {test_pdf_path}")
    
    # Test XML generation
    xml_generator = FaxXMLGenerator()
    xml_output_path = "test_files/test_fax_job.xml"
    
    success = xml_generator.generate_fax_xml(fax_job, contact, test_pdf_path, xml_output_path)
    
    if success:
        print(f"✓ Generated XML file: {xml_output_path}")
        
        # Read and display XML content
        with open(xml_output_path, 'r', encoding='utf-8') as f:
            xml_content = f.read()
        
        print("\nGenerated XML Content:")
        print("-" * 40)
        print(xml_content)
        print("-" * 40)
        
        # Validate XML
        validation_result = xml_generator.validate_xml(xml_output_path)
        print(f"\nXML Validation Result:")
        print(f"  Valid: {validation_result['is_valid']}")
        print(f"  Job ID: {validation_result['job_id']}")
        print(f"  Recipient Fax: {validation_result['recipient_fax']}")
        print(f"  Document Path: {validation_result['document_path']}")
        
        if validation_result['errors']:
            print(f"  Errors: {validation_result['errors']}")
        if validation_result['warnings']:
            print(f"  Warnings: {validation_result['warnings']}")
        
        return True
    else:
        print("✗ Failed to generate XML")
        return False

def test_simple_xml_generation():
    """Test simple XML generation"""
    print("\n" + "="*60)
    print("TESTING SIMPLE XML GENERATION")
    print("="*60)
    
    # Create test PDF
    test_pdf_path = create_test_pdf()
    
    # Test simple XML creation
    xml_path = create_fax_xml(
        recipient_fax="+15551234567",
        sender_name="Test Sender",
        pdf_path=test_pdf_path,
        output_dir="test_files"
    )
    
    print(f"✓ Created simple XML: {xml_path}")
    
    # Validate
    is_valid = validate_fax_xml(xml_path)
    print(f"✓ XML validation: {'PASSED' if is_valid else 'FAILED'}")
    
    # Display content
    with open(xml_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    print("\nSimple XML Content:")
    print("-" * 40)
    print(content)
    print("-" * 40)
    
    return is_valid

def test_cover_page_generation():
    """Test cover page generation"""
    print("\n" + "="*60)
    print("TESTING COVER PAGE GENERATION")
    print("="*60)
    
    cover_details = CoverPageDetails(
        to="John Doe",
        attn="Accounts Receivable",
        from_field="Jane Smith",
        company="ABC Corporation",
        fax="+15551234567",
        phone="+15559876543",
        date=datetime.now().strftime("%m/%d/%Y"),
        subject="Test Fax Transmission",
        re="Invoice #12345",
        cc="manager@abccorp.com",
        comments="This is a test fax for integration testing.",
        msg="Please process the attached documents at your earliest convenience."
    )
    
    generator = CoverPageGenerator()
    cover_pdf_path = "test_files/test_cover_page.pdf"
    
    success = generator.generate_cover_page(cover_details, cover_pdf_path, page_count=2)
    
    if success:
        print(f"✓ Generated cover page: {cover_pdf_path}")
        
        # Generate text preview
        preview = generator.preview_cover_page(cover_details, page_count=2)
        print("\nCover Page Preview:")
        print("-" * 40)
        print(preview)
        print("-" * 40)
        
        return True
    else:
        print("✗ Failed to generate cover page")
        return False

def test_xml_template():
    """Test XML template functionality"""
    print("\n" + "="*60)
    print("TESTING XML TEMPLATE")
    print("="*60)
    
    generator = FaxXMLGenerator()
    template = generator.get_xml_template()
    
    print("XML Template Structure:")
    print("-" * 40)
    print(template)
    print("-" * 40)
    
    return True

def test_error_handling():
    """Test error handling scenarios"""
    print("\n" + "="*60)
    print("TESTING ERROR HANDLING")
    print("="*60)
    
    generator = FaxXMLGenerator()
    
    # Test with non-existent PDF
    print("Testing with non-existent PDF...")
    success = generator.generate_simple_xml(
        "+15551234567", 
        "Test Sender", 
        "non_existent.pdf", 
        "test_files/error_test.xml"
    )
    print(f"  Result: {'FAILED as expected' if not success else 'UNEXPECTED SUCCESS'}")
    
    # Test XML validation with non-existent file
    print("Testing XML validation with non-existent file...")
    result = generator.validate_xml("non_existent.xml")
    print(f"  Valid: {result['is_valid']} (should be False)")
    print(f"  Errors: {result['errors']}")
    
    # Test with invalid XML
    print("Testing with invalid XML...")
    invalid_xml_path = "test_files/invalid.xml"
    with open(invalid_xml_path, 'w') as f:
        f.write("This is not valid XML content")
    
    result = generator.validate_xml(invalid_xml_path)
    print(f"  Valid: {result['is_valid']} (should be False)")
    print(f"  Errors: {result['errors']}")
    
    return True

def prepare_api_integration_test():
    """Prepare for API integration testing"""
    print("\n" + "="*60)
    print("PREPARING FOR API INTEGRATION")
    print("="*60)
    
    print("To test with actual FaxFinder FF240.R1, you will need:")
    print("1. FaxFinder device IP address")
    print("2. Valid credentials (username/password)")
    print("3. Test fax number for sending")
    print("4. Network connectivity to the device")
    print()
    print("API Endpoints to test:")
    print("- POST /ffws/v1/ofax (send fax)")
    print("- GET /ffws/v1/ofax/{fax_entry_url} (check status)")
    print("- GET /ffws/v1/ifax (receive faxes)")
    print()
    print("Sample API test code:")
    print("-" * 40)
    
    api_test_code = '''
import requests
import base64
from requests.auth import HTTPBasicAuth

# Configuration
FAXFINDER_IP = "192.168.1.100"  # Replace with actual IP
USERNAME = "admin"              # Replace with actual username
PASSWORD = "password"           # Replace with actual password

def test_fax_submission(xml_path, pdf_path):
    """Test actual fax submission to FaxFinder"""
    
    # Read XML content
    with open(xml_path, 'r') as f:
        xml_content = f.read()
    
    # Encode PDF in base64
    with open(pdf_path, 'rb') as f:
        pdf_base64 = base64.b64encode(f.read()).decode('utf-8')
    
    # Replace placeholder in XML with actual base64 content
    # (You'll need to modify XML generation to include base64 placeholder)
    
    # Submit to FaxFinder
    url = f"http://{FAXFINDER_IP}/ffws/v1/ofax"
    headers = {'Content-Type': 'application/xml'}
    auth = HTTPBasicAuth(USERNAME, PASSWORD)
    
    try:
        response = requests.post(url, data=xml_content, headers=headers, auth=auth)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        return response.status_code == 200
    except Exception as e:
        print(f"Error: {e}")
        return False

# Uncomment to test with actual device:
# test_fax_submission("test_files/test_fax_job.xml", "test_files/test_document.pdf")
'''
    
    print(api_test_code)
    print("-" * 40)
    
    # Save API test template
    with open("test_files/api_integration_template.py", 'w') as f:
        f.write(api_test_code)
    
    print(f"✓ Saved API integration template: test_files/api_integration_template.py")
    
    return True

def run_all_tests():
    """Run all integration tests"""
    print("FAXFINDER INTEGRATION TESTING")
    print("="*60)
    print(f"Test started at: {datetime.now()}")
    
    setup_logging()
    
    # Create test directory
    os.makedirs("test_files", exist_ok=True)
    
    tests = [
        ("XML Generation", test_xml_generation),
        ("Simple XML Generation", test_simple_xml_generation),
        ("Cover Page Generation", test_cover_page_generation),
        ("XML Template", test_xml_template),
        ("Error Handling", test_error_handling),
        ("API Integration Prep", prepare_api_integration_test)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, "PASSED" if result else "FAILED"))
        except Exception as e:
            print(f"✗ {test_name} failed with error: {e}")
            results.append((test_name, f"ERROR: {e}"))
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    for test_name, result in results:
        status_symbol = "✓" if result == "PASSED" else "✗"
        print(f"{status_symbol} {test_name}: {result}")
    
    passed_count = sum(1 for _, result in results if result == "PASSED")
    total_count = len(results)
    
    print(f"\nOverall: {passed_count}/{total_count} tests passed")
    print(f"Test completed at: {datetime.now()}")
    
    if passed_count == total_count:
        print("\n🎉 All tests passed! Ready for API integration.")
    else:
        print(f"\n⚠️  {total_count - passed_count} test(s) failed. Please review and fix issues.")

if __name__ == "__main__":
    run_all_tests()
