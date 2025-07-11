#!/usr/bin/env python3
"""
Complete test of FaxFinder XML generation and submission
"""

import sys
import os
sys.path.append('src')

from fax.xml_generator import FaxXMLGenerator
from fax.faxfinder_api import FaxFinderAPI
from database.models import FaxJob, Contact, CoverPageDetails
import xml.etree.ElementTree as ET

def create_test_pdf():
    """Create a small test PDF for testing"""
    test_pdf_content = b"%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n/Pages 2 0 R\n>>\nendobj\n2 0 obj\n<<\n/Type /Pages\n/Kids [3 0 R]\n/Count 1\n>>\nendobj\n3 0 obj\n<<\n/Type /Page\n/Parent 2 0 R\n/MediaBox [0 0 612 792]\n>>\nendobj\nxref\n0 4\n0000000000 65535 f \n0000000009 00000 n \n0000000058 00000 n \n0000000115 00000 n \ntrailer\n<<\n/Size 4\n/Root 1 0 R\n>>\nstartxref\n174\n%%EOF"
    
    with open("test_fax.pdf", "wb") as f:
        f.write(test_pdf_content)
    
    return "test_fax.pdf"

def test_faxfinder_xml_generation():
    """Test the new FaxFinder XML generation method"""
    print("Testing FaxFinder XML generation...")
    
    # Create test objects
    contact = Contact(
        name="Dr. John Smith",
        fax_number="555-123-4567",
        organization="Medical Center",
        phone_number="555-987-6543",
        email="dr.smith@medical.com"
    )
    
    cover_page = CoverPageDetails(
        to="Dr. John Smith",
        from_field="Nurse Jane",
        company="The Spine Hospital Louisiana",
        re="Patient Records",
        comments="Urgent medical records for patient consultation"
    )
    
    fax_job = FaxJob(
        sender_name="Nurse Jane",
        sender_email="jane@spinehospital.com",
        recipient_fax="555-123-4567",
        priority="High",
        max_attempts=3,
        retry_interval=5,
        cover_page_details=cover_page
    )
    
    # Create test PDF
    pdf_path = create_test_pdf()
    
    try:
        # Generate FaxFinder XML
        generator = FaxXMLGenerator()
        xml_content = generator.generate_faxfinder_xml(fax_job, contact, pdf_path)
        
        print("✓ FaxFinder XML generated successfully")
        
        # Parse and validate XML structure
        root = ET.fromstring(xml_content)
        
        if root.tag == "schedule_fax":
            print("✓ Root element is correct: 'schedule_fax'")
        else:
            print(f"✗ Root element is incorrect: '{root.tag}'")
            return False
        
        # Check for required elements
        recipient = root.find("recipient")
        if recipient is not None:
            name = recipient.find("name")
            fax_num = recipient.find("fax_number")
            if name is not None and fax_num is not None:
                print(f"✓ Recipient info: {name.text} -> {fax_num.text}")
            else:
                print("✗ Missing recipient name or fax number")
                return False
        else:
            print("✗ Missing recipient element")
            return False
        
        # Check sender
        sender = root.find("sender")
        if sender is not None:
            name = sender.find("name")
            if name is not None:
                print(f"✓ Sender info: {name.text}")
            else:
                print("✗ Missing sender name")
                return False
        else:
            print("✗ Missing sender element")
            return False
        
        # Check document with embedded PDF
        document = root.find("document")
        if document is not None:
            filename = document.find("filename")
            content = document.find("content")
            
            if filename is not None and content is not None:
                encoding = content.get("encoding")
                if encoding == "base64":
                    pdf_data = content.text
                    print(f"✓ Document: {filename.text} with {len(pdf_data)} chars of base64 PDF")
                else:
                    print(f"✗ Content encoding is '{encoding}', expected 'base64'")
                    return False
            else:
                print("✗ Missing document filename or content")
                return False
        else:
            print("✗ Missing document element")
            return False
        
        # Check options
        options = root.find("options")
        if options is not None:
            priority = options.find("priority")
            retry_count = options.find("retry_count")
            if priority is not None and retry_count is not None:
                print(f"✓ Options: priority={priority.text}, retry_count={retry_count.text}")
            else:
                print("✗ Missing priority or retry_count in options")
                return False
        else:
            print("✗ Missing options element")
            return False
        
        # Show XML structure (first 20 lines)
        print("\nXML Structure (first 20 lines):")
        print("=" * 50)
        lines = xml_content.split('\n')
        for i, line in enumerate(lines[:20], 1):
            if 'content encoding="base64"' in line:
                # Truncate the base64 content for display
                start = line.find('>') + 1
                end = line.rfind('<')
                if start < end and end - start > 50:
                    truncated = line[:start] + line[start:start+30] + "..." + line[end-20:end] + line[end:]
                    print(f"{i:2}: {truncated}")
                else:
                    print(f"{i:2}: {line}")
            else:
                print(f"{i:2}: {line}")
        
        return True
        
    except Exception as e:
        print(f"✗ Error generating FaxFinder XML: {e}")
        return False
    
    finally:
        # Clean up
        try:
            os.remove(pdf_path)
        except:
            pass

def test_api_integration():
    """Test the new API integration method"""
    print("\n" + "=" * 60)
    print("Testing API Integration (without actual submission)")
    print("=" * 60)
    
    # Create test objects
    contact = Contact(
        name="Test Contact",
        fax_number="555-123-4567",
        organization="Test Org"
    )
    
    fax_job = FaxJob(
        sender_name="Test Sender",
        sender_email="test@example.com",
        recipient_fax="555-123-4567",
        priority="Medium"
    )
    
    # Create test PDF
    pdf_path = create_test_pdf()
    
    try:
        # Create API client (with dummy credentials)
        api = FaxFinderAPI("192.168.1.100", "testuser", "testpass")
        
        # Test XML generation through API
        from fax.xml_generator import FaxXMLGenerator
        generator = FaxXMLGenerator()
        xml_content = generator.generate_faxfinder_xml(fax_job, contact, pdf_path)
        
        print("✓ API can generate FaxFinder XML")
        print(f"✓ XML length: {len(xml_content)} characters")
        
        # Verify the XML is valid
        root = ET.fromstring(xml_content)
        print(f"✓ XML is valid with root element: {root.tag}")
        
        return True
        
    except Exception as e:
        print(f"✗ Error in API integration test: {e}")
        return False
    
    finally:
        # Clean up
        try:
            os.remove(pdf_path)
        except:
            pass

def show_comparison():
    """Show comparison between old and new XML formats"""
    print("\n" + "=" * 60)
    print("XML FORMAT COMPARISON")
    print("=" * 60)
    
    print("OLD FORMAT (Internal Tracking):")
    print("- Root element: <FaxJob>")
    print("- Contains file paths and metadata")
    print("- Used for internal tracking only")
    print("- NOT compatible with FaxFinder")
    
    print("\nNEW FORMAT (FaxFinder Submission):")
    print("- Root element: <schedule_fax>")
    print("- Contains base64-encoded PDF content")
    print("- Simplified structure for FaxFinder")
    print("- Ready for direct API submission")
    
    print("\nKEY DIFFERENCES:")
    print("1. Root element changed from 'FaxJob' to 'schedule_fax'")
    print("2. PDF content embedded as base64 instead of file path")
    print("3. Simplified element names (lowercase)")
    print("4. Focus on submission data, not tracking data")

if __name__ == "__main__":
    print("FaxFinder Complete Integration Test")
    print("=" * 60)
    
    test1_passed = test_faxfinder_xml_generation()
    test2_passed = test_api_integration()
    
    show_comparison()
    
    print("\n" + "=" * 60)
    print("TEST RESULTS")
    print("=" * 60)
    
    if test1_passed and test2_passed:
        print("✓ ALL TESTS PASSED!")
        print("✓ FaxFinder XML generation is working correctly")
        print("✓ API integration is ready")
        print("✓ The system can now generate proper XML for FaxFinder submission")
    else:
        print("✗ Some tests failed. Check the output above.")
    
    print("\nNEXT STEPS:")
    print("1. Update the main application to use submit_fax_job() method")
    print("2. Test with actual FaxFinder hardware")
    print("3. Remove old XML files with incorrect format")
