#!/usr/bin/env python3
"""
Test script to understand the correct FaxFinder XML format
"""

import sys
import os
import base64
sys.path.append('src')

from fax.faxfinder_api import FaxFinderAPI
import xml.etree.ElementTree as ET

def create_test_pdf():
    """Create a small test PDF for testing"""
    test_pdf_content = b"%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n/Pages 2 0 R\n>>\nendobj\n2 0 obj\n<<\n/Type /Pages\n/Kids [3 0 R]\n/Count 1\n>>\nendobj\n3 0 obj\n<<\n/Type /Page\n/Parent 2 0 R\n/MediaBox [0 0 612 792]\n>>\nendobj\nxref\n0 4\n0000000000 65535 f \n0000000009 00000 n \n0000000058 00000 n \n0000000115 00000 n \ntrailer\n<<\n/Size 4\n/Root 1 0 R\n>>\nstartxref\n174\n%%EOF"
    
    with open("test_small.pdf", "wb") as f:
        f.write(test_pdf_content)
    
    return "test_small.pdf"

def test_xml_insertion():
    """Test how the FaxFinder API inserts PDF into XML"""
    print("Testing FaxFinder XML insertion...")
    
    # Create test PDF
    pdf_path = create_test_pdf()
    
    # Create a simple XML structure that might work with FaxFinder
    test_xml = '''<?xml version="1.0" encoding="utf-8"?>
<schedule_fax>
    <recipient>
        <name>Test Contact</name>
        <fax_number>555-123-4567</fax_number>
    </recipient>
    <sender>
        <name>Test Sender</name>
    </sender>
    <document>
        <filename>test.pdf</filename>
    </document>
</schedule_fax>'''
    
    # Test the API's PDF insertion method
    api = FaxFinderAPI("dummy", "dummy", "dummy")
    
    # Read PDF and encode
    with open(pdf_path, 'rb') as f:
        pdf_base64 = base64.b64encode(f.read()).decode('utf-8')
    
    print(f"PDF base64 length: {len(pdf_base64)} characters")
    print(f"PDF base64 preview: {pdf_base64[:50]}...")
    
    # Test XML insertion
    xml_with_pdf = api._insert_pdf_into_xml(test_xml, pdf_base64)
    
    print("\nXML with PDF inserted:")
    print("=" * 50)
    
    # Pretty print the XML
    try:
        root = ET.fromstring(xml_with_pdf)
        ET.indent(root, space="  ", level=0)
        pretty_xml = ET.tostring(root, encoding='unicode')
        
        # Show first part of XML (truncate PDF data for readability)
        lines = pretty_xml.split('\n')
        for i, line in enumerate(lines):
            if 'PDFData' in line and len(line) > 100:
                # Truncate long PDF data lines
                pdf_start = line.find('>') + 1
                pdf_end = line.rfind('<')
                if pdf_start < pdf_end and pdf_end - pdf_start > 50:
                    truncated = line[:pdf_start] + line[pdf_start:pdf_start+30] + "..." + line[pdf_end-20:pdf_end] + line[pdf_end:]
                    print(f"{i+1:2}: {truncated}")
                else:
                    print(f"{i+1:2}: {line}")
            else:
                print(f"{i+1:2}: {line}")
    except Exception as e:
        print(f"Error parsing XML: {e}")
        print("Raw XML:")
        print(xml_with_pdf[:500] + "..." if len(xml_with_pdf) > 500 else xml_with_pdf)
    
    # Clean up
    try:
        os.remove(pdf_path)
    except:
        pass
    
    return xml_with_pdf

def suggest_correct_format():
    """Suggest what the correct FaxFinder XML format might be"""
    print("\n" + "=" * 60)
    print("SUGGESTED CORRECT FAXFINDER XML FORMAT:")
    print("=" * 60)
    
    suggested_xml = '''<?xml version="1.0" encoding="utf-8"?>
<schedule_fax>
    <recipient>
        <name>John Doe</name>
        <fax_number>555-123-4567</fax_number>
    </recipient>
    <sender>
        <name>Jane Smith</name>
        <company>Test Company</company>
    </sender>
    <document>
        <filename>document.pdf</filename>
        <content encoding="base64">JVBERi0xLjQKMSAwIG9iago8PAovVHlwZSAvQ2F0YWxvZwovUGFnZXMgMiAwIFIKPj4KZW5kb2JqCjIgMCBvYmoKPDwKL1R5cGUgL1BhZ2VzCi9LaWRzIFszIDAgUl0KL0NvdW50IDEKPD4KZW5kb2JqCjMgMCBvYmoKPDwKL1R5cGUgL1BhZ2UKL1BhcmVudCAyIDAgUgovTWVkaWFCb3ggWzAgMCA2MTIgNzkyXQo+PgplbmRvYmoKeHJlZgowIDQKMDAwMDAwMDAwMCA2NTUzNSBmIAowMDAwMDAwMDA5IDAwMDAwIG4gCjAwMDAwMDAwNTggMDAwMDAgbiAKMDAwMDAwMDExNSAwMDAwMCBuIAp0cmFpbGVyCjw8Ci9TaXplIDQKL1Jvb3QgMSAwIFIKPj4Kc3RhcnR4cmVmCjE3NAolJUVPRg==</content>
    </document>
    <options>
        <priority>normal</priority>
        <retry_count>3</retry_count>
    </options>
</schedule_fax>'''
    
    print(suggested_xml)
    
    print("\nKEY POINTS:")
    print("1. Root element should be 'schedule_fax'")
    print("2. PDF content should be base64 encoded in <content> element")
    print("3. Structure should match FaxFinder's expected schema")
    print("4. The current XML we generate is for internal tracking only")
    print("5. For FaxFinder submission, we need a different XML format")

if __name__ == "__main__":
    print("FaxFinder XML Format Test")
    print("=" * 50)
    
    test_xml_insertion()
    suggest_correct_format()
