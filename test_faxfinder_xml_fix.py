"""
Test script to verify the FaxFinder XML format fix
"""

import sys
import os
sys.path.append('src')

from database.models import FaxJob, Contact, CoverPageDetails
from fax.xml_generator import FaxXMLGenerator
from datetime import datetime

def test_faxfinder_xml_generation():
    """Test the corrected FaxFinder XML generation"""
    
    # Create test data
    fax_job = FaxJob(
        fax_id=123,
        sender_name="Suzy Sneder",
        sender_email="suzy@spinehospital.com",
        priority="Medium",
        max_attempts=3,
        retry_interval=5
    )
    
    # Create cover page details
    cover_page = CoverPageDetails(
        to="Test Contact",
        from_field="Suzy Sneder",
        company="The Spine Hospital Louisiana",
        subject="Medical Records Transmission",
        comments="Urgent medical records for patient consultation"
    )
    fax_job.cover_page_details = cover_page
    
    # Create test contact
    contact = Contact(
        name="Test Contact",
        fax_number="555-123-4567",
        organization="Test Medical Center",
        phone_number="555-987-6543",
        email="test@medcenter.com"
    )
    
    # Use an existing PDF file for testing
    pdf_path = "temp_final_preview.pdf"
    
    if not os.path.exists(pdf_path):
        print(f"Error: Test PDF file not found: {pdf_path}")
        return False
    
    try:
        # Generate the corrected XML
        generator = FaxXMLGenerator()
        xml_content = generator.generate_faxfinder_xml(fax_job, contact, pdf_path)
        
        # Save the corrected XML for inspection
        output_file = "corrected_faxfinder_xml.xml"
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(xml_content)
        
        print("✓ Successfully generated corrected FaxFinder XML")
        print(f"✓ XML saved to: {output_file}")
        print(f"✓ XML length: {len(xml_content)} characters")
        
        # Check for key elements (NOTE: No cover_page section - we use our own cover page)
        checks = [
            ('<schedule_fax>', 'Root element'),
            ('<sender>', 'Sender section'),
            ('<n>', 'Sender name element'),
            ('<recipient>', 'Recipient section'),
            ('<fax_number>', 'Recipient fax number'),
            ('<priority>3</priority>', 'Priority as number'),
            ('<max_tries>', 'Max tries element'),
            ('<try_interval>', 'Try interval element'),
            ('<attachment>', 'Attachment section'),
            ('<location>inline</location>', 'Inline location'),
            ('<content_type>application/pdf</content_type>', 'PDF content type'),
            ('<content_transfer_encoding>base64</content_transfer_encoding>', 'Base64 encoding'),
            ('<content>', 'Base64 content')
        ]
        
        print("\n=== XML Format Validation ===")
        all_passed = True
        for check_text, description in checks:
            if check_text in xml_content:
                print(f"✓ {description}")
            else:
                print(f"✗ {description} - MISSING")
                all_passed = False
        
        # Check base64 content length
        if '<content>' in xml_content and '</content>' in xml_content:
            start = xml_content.find('<content>') + len('<content>')
            end = xml_content.find('</content>')
            base64_content = xml_content[start:end].strip()
            if len(base64_content) > 1000:  # Should be substantial for a real PDF
                print(f"✓ Base64 content length: {len(base64_content)} characters")
            else:
                print(f"⚠ Base64 content seems short: {len(base64_content)} characters")
        
        if all_passed:
            print("\n🎉 All format checks PASSED! The XML should now work with FaxFinder.")
        else:
            print("\n❌ Some format checks FAILED. Review the XML structure.")
        
        return all_passed
        
    except Exception as e:
        print(f"❌ Error generating XML: {e}")
        return False

if __name__ == "__main__":
    print("Testing FaxFinder XML Format Fix...")
    print("=" * 50)
    
    success = test_faxfinder_xml_generation()
    
    if success:
        print("\n✅ Test completed successfully!")
        print("The FaxFinder XML format has been corrected.")
    else:
        print("\n❌ Test failed!")
        print("There may be issues with the XML format correction.")
