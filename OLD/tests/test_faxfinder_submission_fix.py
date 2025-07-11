"""
Test script to verify FaxFinder submission fix
Tests that the XML generation includes base64 PDF content for FaxFinder
"""

import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from fax.xml_generator import FaxXMLGenerator
from fax.faxfinder_api import FaxFinderAPI
from database.models import FaxJob, Contact, CoverPageDetails

def create_test_pdf():
    """Create a small test PDF file"""
    test_pdf_path = "test_fax_document.pdf"
    
    # Create a minimal PDF content (this is a very basic PDF structure)
    pdf_content = b"""%PDF-1.4
1 0 obj
<<
/Type /Catalog
/Pages 2 0 R
>>
endobj

2 0 obj
<<
/Type /Pages
/Kids [3 0 R]
/Count 1
>>
endobj

3 0 obj
<<
/Type /Page
/Parent 2 0 R
/MediaBox [0 0 612 792]
/Contents 4 0 R
>>
endobj

4 0 obj
<<
/Length 44
>>
stream
BT
/F1 12 Tf
100 700 Td
(Test Fax Document) Tj
ET
endstream
endobj

xref
0 5
0000000000 65535 f 
0000000009 00000 n 
0000000058 00000 n 
0000000115 00000 n 
0000000206 00000 n 
trailer
<<
/Size 5
/Root 1 0 R
>>
startxref
300
%%EOF"""
    
    with open(test_pdf_path, 'wb') as f:
        f.write(pdf_content)
    
    return test_pdf_path

def test_faxfinder_xml_generation():
    """Test that FaxFinder XML generation includes base64 PDF content"""
    print("Testing FaxFinder XML generation fix...")
    
    # Create test PDF
    test_pdf_path = create_test_pdf()
    print(f"Created test PDF: {test_pdf_path}")
    
    try:
        # Create test objects
        fax_job = FaxJob(
            sender_name="Test Sender",
            sender_email="test@example.com",
            recipient_fax="555-123-4567",
            priority="Medium",
            max_attempts=3,
            retry_interval=5
        )
        
        # Add cover page details
        fax_job.cover_page_details = CoverPageDetails(
            to="Test Recipient",
            from_field="Test Sender",
            company="Test Company",
            re="Test Subject",
            comments="Test comments"
        )
        
        contact = Contact(
            name="Test Recipient",
            fax_number="555-123-4567",
            organization="Test Organization",
            phone_number="555-987-6543",
            email="test@recipient.com"
        )
        
        # Test XML generation
        print("\n1. Testing generate_faxfinder_xml method...")
        generator = FaxXMLGenerator()
        
        xml_content = generator.generate_faxfinder_xml(
            fax_job=fax_job,
            contact=contact,
            pdf_file_path=test_pdf_path
        )
        
        if xml_content:
            print(f"   ✅ XML generated successfully, length: {len(xml_content)} characters")
            
            # Check for base64 content
            if 'encoding="base64"' in xml_content:
                print("   ✅ Base64 encoding attribute found")
            else:
                print("   ❌ Base64 encoding attribute NOT found")
            
            if '<content encoding="base64">' in xml_content:
                print("   ✅ Base64 content element found")
                
                # Extract and validate base64 content
                start_marker = '<content encoding="base64">'
                end_marker = '</content>'
                start_pos = xml_content.find(start_marker) + len(start_marker)
                end_pos = xml_content.find(end_marker, start_pos)
                
                if start_pos > len(start_marker) - 1 and end_pos > start_pos:
                    base64_content = xml_content[start_pos:end_pos].strip()
                    print(f"   ✅ Base64 content extracted: {len(base64_content)} characters")
                    
                    # Verify it's valid base64
                    try:
                        import base64
                        decoded = base64.b64decode(base64_content)
                        print(f"   ✅ Base64 content is valid, decoded to {len(decoded)} bytes")
                        
                        # Check if decoded content starts with PDF header
                        if decoded.startswith(b'%PDF'):
                            print("   ✅ Decoded content is a valid PDF")
                        else:
                            print("   ❌ Decoded content is not a valid PDF")
                            
                    except Exception as e:
                        print(f"   ❌ Base64 content is invalid: {e}")
                else:
                    print("   ❌ Could not extract base64 content")
            else:
                print("   ❌ Base64 content element NOT found")
            
            # Save debug XML
            debug_xml_path = "debug_faxfinder_submission.xml"
            with open(debug_xml_path, 'w', encoding='utf-8') as f:
                f.write(xml_content)
            print(f"   📄 Debug XML saved to: {debug_xml_path}")
            
        else:
            print("   ❌ Failed to generate XML")
        
        # Test 2: Compare with local storage XML (should NOT have base64)
        print("\n2. Comparing with local storage XML...")
        
        local_xml_path = "test_local_storage.xml"
        local_success = generator.generate_fax_xml(
            fax_job=fax_job,
            contact=contact,
            pdf_file_path=test_pdf_path,
            output_path=local_xml_path
        )
        
        if local_success and os.path.exists(local_xml_path):
            with open(local_xml_path, 'r', encoding='utf-8') as f:
                local_xml_content = f.read()
            
            print(f"   ✅ Local XML generated: {len(local_xml_content)} characters")
            
            if 'encoding="base64"' in local_xml_content:
                print("   ❌ Local XML contains base64 (should not)")
            else:
                print("   ✅ Local XML does not contain base64 (correct)")
            
            # Clean up
            os.remove(local_xml_path)
        else:
            print("   ❌ Failed to generate local XML")
        
        # Test 3: Test FaxFinder API submission (dry run)
        print("\n3. Testing FaxFinder API submission structure...")
        
        # Create API instance (won't actually connect)
        api = FaxFinderAPI("192.168.1.100", "test", "test")
        
        # Test the XML generation that would be used in submission
        try:
            # This tests the same method that submit_fax_job uses
            test_xml = generator.generate_faxfinder_xml(fax_job, contact, test_pdf_path)
            
            if test_xml and len(test_xml) > 1000:  # Should be substantial with base64
                print("   ✅ FaxFinder submission XML structure looks correct")
                
                # Check XML structure
                required_elements = [
                    '<schedule_fax>',
                    '<JobID>',
                    '<Sender>',
                    '<Recipient>',
                    '<FaxNumber>',
                    '<Document>',
                    '<content encoding="base64">',
                    '</schedule_fax>'
                ]
                
                missing_elements = []
                for element in required_elements:
                    if element not in test_xml:
                        missing_elements.append(element)
                
                if not missing_elements:
                    print("   ✅ All required XML elements present")
                else:
                    print(f"   ❌ Missing XML elements: {missing_elements}")
                    
            else:
                print("   ❌ FaxFinder submission XML is too small or empty")
                
        except Exception as e:
            print(f"   ❌ Error testing FaxFinder submission: {e}")
        
    finally:
        # Clean up test PDF
        if os.path.exists(test_pdf_path):
            os.remove(test_pdf_path)
            print(f"\nCleaned up test PDF: {test_pdf_path}")
    
    print("\nFaxFinder submission test completed!")

if __name__ == "__main__":
    test_faxfinder_xml_generation()
