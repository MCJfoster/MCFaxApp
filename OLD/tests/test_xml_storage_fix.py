"""
Test script to verify XML storage location fix
"""

import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from fax.xml_generator import FaxXMLGenerator, create_fax_xml
from database.models import FaxJob, Contact, CoverPageDetails

def test_xml_storage_location():
    """Test that XML files are stored in the correct location"""
    print("Testing XML storage location fix...")
    
    # Test 1: Check that xml directory is created relative to current working directory
    print(f"\nCurrent working directory: {Path.cwd()}")
    
    # Test 2: Create a simple XML using utility function
    print("\n1. Testing utility function create_fax_xml...")
    try:
        xml_path = create_fax_xml(
            recipient_fax="555-123-4567",
            sender_name="Test Sender",
            pdf_path="test.pdf"  # Doesn't need to exist for this test
        )
        print(f"   Created XML at: {xml_path}")
        
        # Check if it's in the xml subdirectory
        xml_path_obj = Path(xml_path)
        expected_dir = Path.cwd() / "xml"
        
        if xml_path_obj.parent == expected_dir:
            print("   ✅ XML stored in correct location: ./xml/")
        else:
            print(f"   ❌ XML stored in wrong location. Expected: {expected_dir}, Got: {xml_path_obj.parent}")
        
        # Clean up
        if xml_path_obj.exists():
            xml_path_obj.unlink()
            
    except Exception as e:
        print(f"   ❌ Error testing utility function: {e}")
    
    # Test 3: Test XML generator directly
    print("\n2. Testing FaxXMLGenerator.generate_fax_xml...")
    try:
        generator = FaxXMLGenerator()
        
        # Create test objects
        fax_job = FaxJob(
            sender_name="Test Sender",
            sender_email="test@example.com",
            recipient_fax="555-123-4567",
            priority="Medium"
        )
        
        contact = Contact(
            name="Test Contact",
            fax_number="555-123-4567",
            organization="Test Org"
        )
        
        # Test with just filename (should go to xml directory)
        xml_filename = "test_fax_job.xml"
        success = generator.generate_fax_xml(
            fax_job=fax_job,
            contact=contact,
            pdf_file_path="test.pdf",  # Doesn't need to exist
            output_path=xml_filename
        )
        
        if success:
            expected_path = Path.cwd() / "xml" / xml_filename
            if expected_path.exists():
                print(f"   ✅ XML generated at correct location: {expected_path}")
                # Clean up
                expected_path.unlink()
            else:
                print(f"   ❌ XML not found at expected location: {expected_path}")
        else:
            print("   ❌ Failed to generate XML")
            
    except Exception as e:
        print(f"   ❌ Error testing XML generator: {e}")
    
    # Test 4: Check that xml directory exists
    xml_dir = Path.cwd() / "xml"
    if xml_dir.exists() and xml_dir.is_dir():
        print(f"\n3. ✅ XML directory exists: {xml_dir}")
        
        # List existing XML files
        xml_files = list(xml_dir.glob("*.xml"))
        print(f"   Found {len(xml_files)} existing XML files:")
        for xml_file in xml_files[:5]:  # Show first 5
            print(f"     - {xml_file.name}")
        if len(xml_files) > 5:
            print(f"     ... and {len(xml_files) - 5} more")
    else:
        print(f"\n3. ❌ XML directory does not exist: {xml_dir}")
    
    print("\nXML storage location test completed!")

if __name__ == "__main__":
    test_xml_storage_location()
