#!/usr/bin/env python3
"""
Capture the exact XML being sent to FaxFinder to debug the blank fax issue
"""

import sys
import os
import logging
sys.path.append('src')

from fax.xml_generator import FaxXMLGenerator
from fax.faxfinder_api import FaxFinderAPI
from database.models import FaxJob, Contact, CoverPageDetails
import xml.etree.ElementTree as ET

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

def create_test_pdf():
    """Create a test PDF with actual content"""
    # Create a more realistic PDF with some content
    test_pdf_content = b"""%PDF-1.4
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
/Resources <<
/Font <<
/F1 5 0 R
>>
>>
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
(Test Fax Content) Tj
ET
endstream
endobj
5 0 obj
<<
/Type /Font
/Subtype /Type1
/BaseFont /Helvetica
>>
endobj
xref
0 6
0000000000 65535 f 
0000000009 00000 n 
0000000058 00000 n 
0000000115 00000 n 
0000000273 00000 n 
0000000367 00000 n 
trailer
<<
/Size 6
/Root 1 0 R
>>
startxref
444
%%EOF"""
    
    with open("test_capture_fax.pdf", "wb") as f:
        f.write(test_pdf_content)
    
    return "test_capture_fax.pdf"

def capture_faxfinder_xml():
    """Capture and save the exact XML that would be sent to FaxFinder"""
    print("=" * 80)
    print("CAPTURING EXACT FAXFINDER XML")
    print("=" * 80)
    
    # Create realistic test objects
    contact = Contact(
        name="Test Contact",
        fax_number="555-123-4567",
        organization="Test Organization",
        phone_number="555-987-6543",
        email="test@example.com"
    )
    
    cover_page = CoverPageDetails(
        to="Test Contact",
        from_field="Suzy Sneder",
        company="The Spine Hospital Louisiana",
        re="Patient Records",
        comments="Test fax with actual content"
    )
    
    fax_job = FaxJob(
        sender_name="Suzy Sneder",
        sender_email="suzy@spinehospital.com",
        recipient_fax="555-123-4567",
        priority="Medium",
        max_attempts=3,
        retry_interval=5,
        cover_page_details=cover_page
    )
    
    # Create test PDF
    pdf_path = create_test_pdf()
    
    try:
        print("1. Generating FaxFinder XML...")
        
        generator = FaxXMLGenerator()
        faxfinder_xml = generator.generate_faxfinder_xml(fax_job, contact, pdf_path)
        
        # Save the exact XML that would be sent
        with open("captured_faxfinder_xml.xml", "w", encoding="utf-8") as f:
            f.write(faxfinder_xml)
        
        print(f"✓ FaxFinder XML saved to: captured_faxfinder_xml.xml")
        print(f"✓ XML length: {len(faxfinder_xml)} characters")
        
        # Parse and analyze
        root = ET.fromstring(faxfinder_xml)
        print(f"✓ Root element: {root.tag}")
        
        # Show structure
        print("\n2. XML Structure Analysis:")
        print("-" * 40)
        
        def print_element_structure(element, indent=0):
            """Recursively print XML structure"""
            spaces = "  " * indent
            if element.text and element.text.strip():
                if len(element.text) > 50:
                    text_preview = element.text[:50] + "..."
                else:
                    text_preview = element.text
                print(f"{spaces}<{element.tag}>{text_preview}</{element.tag}>")
            else:
                print(f"{spaces}<{element.tag}>")
                for child in element:
                    print_element_structure(child, indent + 1)
                print(f"{spaces}</{element.tag}>")
        
        print_element_structure(root)
        
        # Check base64 content specifically
        print("\n3. Base64 Content Verification:")
        print("-" * 40)
        
        document = root.find("document")
        if document is not None:
            content = document.find("content")
            if content is not None and content.get("encoding") == "base64":
                pdf_data = content.text
                print(f"✓ Base64 content found: {len(pdf_data)} characters")
                
                # Verify it decodes properly
                import base64
                try:
                    decoded = base64.b64decode(pdf_data)
                    print(f"✓ Decodes to {len(decoded)} bytes")
                    if decoded.startswith(b'%PDF'):
                        print("✓ Decoded content is valid PDF")
                        
                        # Save decoded PDF for verification
                        with open("decoded_test.pdf", "wb") as f:
                            f.write(decoded)
                        print("✓ Decoded PDF saved as: decoded_test.pdf")
                    else:
                        print("✗ Decoded content is not a valid PDF")
                except Exception as e:
                    print(f"✗ Base64 decode error: {e}")
            else:
                print("✗ No base64 content found!")
        else:
            print("✗ No document element found!")
        
        print("\n4. Comparing with Expected FaxFinder Format:")
        print("-" * 40)
        
        # Check if the XML matches expected FaxFinder format
        expected_elements = [
            "recipient/name",
            "recipient/fax_number", 
            "sender/name",
            "document/filename",
            "document/content[@encoding='base64']"
        ]
        
        for xpath in expected_elements:
            try:
                if xpath.endswith("[@encoding='base64']"):
                    # Special check for base64 content
                    elem = root.find("document/content")
                    if elem is not None and elem.get("encoding") == "base64":
                        print(f"✓ Found: {xpath}")
                    else:
                        print(f"✗ Missing: {xpath}")
                else:
                    elem = root.find(xpath)
                    if elem is not None and elem.text:
                        print(f"✓ Found: {xpath} = '{elem.text}'")
                    else:
                        print(f"✗ Missing: {xpath}")
            except Exception as e:
                print(f"✗ Error checking {xpath}: {e}")
        
        print("\n5. Potential Issues:")
        print("-" * 40)
        
        issues = []
        
        # Check XML structure
        if root.tag != "schedule_fax":
            issues.append(f"Root element is '{root.tag}', FaxFinder might expect 'schedule_fax'")
        
        # Check required elements
        recipient = root.find("recipient")
        if recipient is None:
            issues.append("Missing 'recipient' element")
        else:
            fax_num = recipient.find("fax_number")
            if fax_num is None or not fax_num.text:
                issues.append("Missing or empty recipient fax_number")
        
        sender = root.find("sender")
        if sender is None:
            issues.append("Missing 'sender' element")
        
        document = root.find("document")
        if document is None:
            issues.append("Missing 'document' element")
        else:
            content = document.find("content")
            if content is None:
                issues.append("Missing 'document/content' element")
            elif content.get("encoding") != "base64":
                issues.append("Document content is not base64 encoded")
        
        if issues:
            print("⚠️  Potential issues found:")
            for issue in issues:
                print(f"   - {issue}")
        else:
            print("✅ No obvious issues found with XML structure")
        
        print("\n" + "=" * 80)
        print("SUMMARY")
        print("=" * 80)
        print("The exact XML that would be sent to FaxFinder has been captured.")
        print("Files created:")
        print("  - captured_faxfinder_xml.xml (the actual XML)")
        print("  - decoded_test.pdf (decoded PDF content)")
        print()
        print("If you're still getting blank faxes, the issue is likely:")
        print("1. FaxFinder expects a different XML format/structure")
        print("2. FaxFinder authentication/endpoint configuration")
        print("3. Network connectivity issues")
        print("4. FaxFinder processing the XML but not the embedded PDF correctly")
        
        return True
        
    except Exception as e:
        print(f"✗ Error: {e}")
        return False
    
    finally:
        # Clean up test PDF
        try:
            os.remove(pdf_path)
        except:
            pass

if __name__ == "__main__":
    print("Capturing Exact FaxFinder XML")
    print("This will show you the EXACT XML being sent to FaxFinder")
    print()
    
    success = capture_faxfinder_xml()
    
    if success:
        print("\n🔍 NEXT STEPS:")
        print("1. Review 'captured_faxfinder_xml.xml' - this is what FaxFinder receives")
        print("2. Compare with FaxFinder API documentation")
        print("3. Test with FaxFinder directly to see if it accepts this format")
        print("4. Check FaxFinder logs for any processing errors")
    else:
        print("\n❌ Failed to capture XML")
