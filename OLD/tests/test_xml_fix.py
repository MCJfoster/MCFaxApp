#!/usr/bin/env python3
"""
Test script to verify XML generation fix for FaxFinder
"""

import sys
import os
sys.path.append('src')

from fax.xml_generator import FaxXMLGenerator
from database.models import FaxJob, Contact, CoverPageDetails
import xml.etree.ElementTree as ET

def test_xml_generation():
    """Test that XML is generated with correct root element"""
    print("Testing XML generation fix...")
    
    # Create test objects
    contact = Contact(
        name="Test Contact",
        fax_number="555-123-4567",
        organization="Test Org"
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
        recipient_fax="555-123-4567",
        priority="Medium",
        cover_page_details=cover_page
    )
    
    # Generate XML
    generator = FaxXMLGenerator()
    output_path = "test_schedule_fax.xml"
    
    # Create a dummy PDF path for testing
    pdf_path = "test.pdf"
    
    success = generator.generate_fax_xml(fax_job, contact, pdf_path, output_path)
    
    if success:
        print(f"✓ XML generated successfully: {output_path}")
        
        # Parse and check root element
        try:
            tree = ET.parse(output_path)
            root = tree.getroot()
            
            print(f"Root element: {root.tag}")
            
            if root.tag == "schedule_fax":
                print("✓ Root element is correct: 'schedule_fax'")
                
                # Show first few lines of XML
                with open(output_path, 'r') as f:
                    lines = f.readlines()[:10]
                    print("\nFirst 10 lines of generated XML:")
                    for i, line in enumerate(lines, 1):
                        print(f"{i:2}: {line.rstrip()}")
                
                return True
            else:
                print(f"✗ Root element is incorrect: '{root.tag}' (expected 'schedule_fax')")
                return False
                
        except Exception as e:
            print(f"✗ Error parsing XML: {e}")
            return False
    else:
        print("✗ Failed to generate XML")
        return False

def test_simple_xml():
    """Test simple XML generation"""
    print("\nTesting simple XML generation...")
    
    generator = FaxXMLGenerator()
    output_path = "test_simple_schedule_fax.xml"
    
    success = generator.generate_simple_xml(
        recipient_fax="555-123-4567",
        sender_name="Test Sender",
        pdf_file_path="test.pdf",
        output_path=output_path,
        subject="Test Subject"
    )
    
    if success:
        print(f"✓ Simple XML generated successfully: {output_path}")
        
        # Check root element
        try:
            tree = ET.parse(output_path)
            root = tree.getroot()
            
            if root.tag == "schedule_fax":
                print("✓ Simple XML root element is correct: 'schedule_fax'")
                return True
            else:
                print(f"✗ Simple XML root element is incorrect: '{root.tag}'")
                return False
                
        except Exception as e:
            print(f"✗ Error parsing simple XML: {e}")
            return False
    else:
        print("✗ Failed to generate simple XML")
        return False

if __name__ == "__main__":
    print("XML Generation Fix Test")
    print("=" * 50)
    
    test1_passed = test_xml_generation()
    test2_passed = test_simple_xml()
    
    print("\n" + "=" * 50)
    if test1_passed and test2_passed:
        print("✓ All tests passed! XML generation should now work with FaxFinder.")
    else:
        print("✗ Some tests failed. Check the output above.")
    
    # Clean up test files
    for file in ["test_schedule_fax.xml", "test_simple_schedule_fax.xml"]:
        try:
            os.remove(file)
            print(f"Cleaned up: {file}")
        except:
            pass
