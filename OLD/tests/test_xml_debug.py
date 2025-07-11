#!/usr/bin/env python3
"""
Debug script to test XML generation and see exactly what's being sent to FaxFinder
"""

import sys
import os
sys.path.append('src')

from database.models import FaxJob, Contact, CoverPageDetails
from fax.xml_generator import FaxXMLGenerator
from fax.faxfinder_api import FaxFinderAPI

def test_xml_generation():
    """Test XML generation and show exactly what's created"""
    
    # Create test objects
    contact = Contact(
        name="Test Contact",
        fax_number="555-123-4567",
        organization="Test Organization"
    )
    
    cover_page = CoverPageDetails(
        to="Test Contact",
        from_field="Test Sender",
        company="Test Company",
        re="Test Subject"
    )
    
    fax_job = FaxJob(
        sender_name="Test Sender",
        sender_email="test@example.com",
        priority="Medium",
        max_attempts=3,
        retry_interval=5,
        cover_page_details=cover_page
    )
    
    # Test PDF path (use any existing PDF)
    pdf_path = "processed/fax_job_20250707_112921.pdf"
    if not os.path.exists(pdf_path):
        print(f"ERROR: Test PDF not found: {pdf_path}")
        return
    
    print("=== TESTING XML GENERATION ===")
    
    # Generate XML
    generator = FaxXMLGenerator()
    try:
        xml_content = generator.generate_faxfinder_xml(fax_job, contact, pdf_path)
        
        print(f"XML Length: {len(xml_content)} characters")
        print("\n=== FIRST 2000 CHARACTERS OF XML ===")
        print(xml_content[:2000])
        print("\n=== LAST 500 CHARACTERS OF XML ===")
        print(xml_content[-500:])
        
        # Check for base64 content
        if '<content encoding="base64">' in xml_content:
            start_pos = xml_content.find('<content encoding="base64">') + len('<content encoding="base64">')
            end_pos = xml_content.find('</content>', start_pos)
            if start_pos > 27 and end_pos > start_pos:
                base64_content = xml_content[start_pos:end_pos].strip()
                print(f"\n=== BASE64 CONTENT FOUND ===")
                print(f"Base64 length: {len(base64_content)} characters")
                print(f"First 100 chars: {base64_content[:100]}")
                print(f"Last 100 chars: {base64_content[-100:]}")
            else:
                print("\n=== BASE64 MARKERS FOUND BUT NO CONTENT ===")
        else:
            print("\n=== NO BASE64 CONTENT MARKERS FOUND ===")
        
        # Save XML to file for inspection
        with open("debug_generated.xml", "w", encoding="utf-8") as f:
            f.write(xml_content)
        print(f"\n=== XML SAVED TO: debug_generated.xml ===")
        
        # Test what would be sent to FaxFinder
        print("\n=== TESTING FAXFINDER API CALL (DRY RUN) ===")
        
        # Create API client (won't actually send)
        api = FaxFinderAPI("10.70.1.13", "test", "test")
        
        # Show what would be sent
        print(f"URL: {api.base_url}{api.endpoints['send_fax']}")
        print(f"Content-Type: application/xml")
        print(f"XML size: {len(xml_content)} bytes")
        
        # Check root element
        if xml_content.strip().startswith('<?xml'):
            first_element_start = xml_content.find('<', xml_content.find('?>') + 2)
            first_element_end = xml_content.find('>', first_element_start)
            if first_element_start > 0 and first_element_end > first_element_start:
                root_element = xml_content[first_element_start:first_element_end + 1]
                print(f"Root element: {root_element}")
        
    except Exception as e:
        print(f"ERROR generating XML: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_xml_generation()
