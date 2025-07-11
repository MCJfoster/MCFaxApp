#!/usr/bin/env python3
"""
Test script to verify the XML generation fixes
Tests that the corrected XML uses proper element names and excludes email addresses
"""

import sys
import os
from pathlib import Path

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from fax.xml_generator import FaxXMLGenerator
from database.models import FaxJob, Contact, CoverPageDetails

def test_xml_generation():
    """Test the corrected XML generation"""
    print("Testing XML generation fixes...")
    
    # Create test data
    fax_job = FaxJob(
        sender_name="Test Sender",
        sender_email="sender@test.com",
        priority="Medium",
        max_attempts=3,
        retry_interval=5
    )
    
    contact = Contact(
        name="Test Recipient",
        fax_number="555-123-4567",
        organization="Test Organization",
        email="recipient@test.com"
    )
    
    # Create a dummy PDF file for testing
    test_pdf_path = "test_document.pdf"
    with open(test_pdf_path, 'wb') as f:
        f.write(b"Dummy PDF content for testing")
    
    try:
        # Test XML generation
        generator = FaxXMLGenerator()
        xml_content = generator.generate_faxfinder_xml(fax_job, contact, test_pdf_path)
        
        print("Generated XML content:")
        print("=" * 50)
        print(xml_content)
        print("=" * 50)
        
        # Verify fixes
        print("\nVerifying fixes:")
        
        # Check for correct element names
        if '<name>' in xml_content and '</name>' in xml_content:
            print("✓ PASS: Uses <name> elements instead of <n>")
        else:
            print("✗ FAIL: Still using <n> elements")
            
        # Check that email addresses are NOT included
        if 'email_address' not in xml_content:
            print("✓ PASS: Email addresses removed from FaxFinder XML")
        else:
            print("✗ FAIL: Email addresses still present in XML")
            
        # Check for sender name
        if '<sender>' in xml_content and 'Test Sender' in xml_content:
            print("✓ PASS: Sender information included correctly")
        else:
            print("✗ FAIL: Sender information missing or incorrect")
            
        # Check for recipient name and fax
        if '<recipient>' in xml_content and 'Test Recipient' in xml_content and '555-123-4567' in xml_content:
            print("✓ PASS: Recipient information included correctly")
        else:
            print("✗ FAIL: Recipient information missing or incorrect")
            
        # Check for attachment name
        if '<attachment>' in xml_content and 'test_document.pdf' in xml_content:
            print("✓ PASS: Attachment name included correctly")
        else:
            print("✗ FAIL: Attachment name missing or incorrect")
            
        # Check for base64 content
        if 'base64' in xml_content and '<content>' in xml_content:
            print("✓ PASS: Base64 content included")
        else:
            print("✗ FAIL: Base64 content missing")
            
        print("\nTest completed successfully!")
        
    except Exception as e:
        print(f"✗ ERROR: {e}")
        return False
        
    finally:
        # Clean up test file
        if os.path.exists(test_pdf_path):
            os.remove(test_pdf_path)
    
    return True

if __name__ == "__main__":
    test_xml_generation()
