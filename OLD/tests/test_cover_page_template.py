"""
Test script for the enhanced cover page template
Demonstrates the new hospital template with checkboxes
"""

import os
import sys
from datetime import datetime
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from database.models import CoverPageDetails
from pdf.cover_page import CoverPageGenerator

def test_hospital_cover_page():
    """Test the hospital cover page template"""
    print("Testing Hospital Cover Page Template...")
    
    # Create sample cover page details
    cover_details = CoverPageDetails(
        to="Dr. John Smith",
        from_field="Dr. Sarah Johnson",
        company="The Spine Hospital Louisiana",
        fax="(555) 123-4567",
        phone="(225) 906-4805",
        date=datetime.now().strftime("%m/%d/%Y"),
        re="Patient Consultation Report",
        cc="Medical Records",
        comments="Please review the attached patient consultation report and provide feedback.",
        msg="This fax contains confidential medical information. Please handle accordingly.",
        urgent=True,
        for_review=True,
        please_comment=False,
        please_reply=True
    )
    
    # Generate cover page
    generator = CoverPageGenerator()
    output_path = "test_hospital_cover_page.pdf"
    
    print(f"Generating cover page: {output_path}")
    success = generator.generate_cover_page(
        cover_details=cover_details,
        output_path=output_path,
        page_count=3,  # 3 pages plus cover page = 4 total
        logo_path=None  # No logo for this test
    )
    
    if success:
        print(f"✅ Cover page generated successfully: {output_path}")
        print(f"📄 File size: {Path(output_path).stat().st_size / 1024:.1f} KB")
    else:
        print("❌ Failed to generate cover page")
        return False
    
    # Test text preview
    print("\n" + "="*60)
    print("TEXT PREVIEW:")
    print("="*60)
    preview = generator.preview_cover_page(cover_details, page_count=3)
    print(preview)
    
    return success

def test_simple_cover_page():
    """Test the simple cover page utility function"""
    print("\nTesting Simple Cover Page Function...")
    
    from pdf.cover_page import create_simple_cover_page
    
    try:
        output_path = create_simple_cover_page(
            to="Test Recipient",
            from_name="Test Sender",
            subject="Test Subject",
            pages=2,
            output_path="test_simple_cover_page.pdf"
        )
        
        print(f"✅ Simple cover page generated: {output_path}")
        print(f"📄 File size: {Path(output_path).stat().st_size / 1024:.1f} KB")
        return True
        
    except Exception as e:
        print(f"❌ Error generating simple cover page: {e}")
        return False

def test_cover_page_validation():
    """Test cover page validation"""
    print("\nTesting Cover Page Validation...")
    
    generator = CoverPageGenerator()
    
    # Test valid details
    valid_details = CoverPageDetails(
        to="Valid Recipient",
        from_field="Valid Sender",
        date="12/30/2024"
    )
    
    errors = generator.validate_cover_details(valid_details)
    if not errors:
        print("✅ Valid details passed validation")
    else:
        print(f"❌ Unexpected validation errors: {errors}")
        return False
    
    # Test invalid details
    invalid_details = CoverPageDetails(
        date="invalid-date"
    )
    
    errors = generator.validate_cover_details(invalid_details)
    if errors:
        print(f"✅ Invalid details caught validation errors: {errors}")
    else:
        print("❌ Invalid details should have failed validation")
        return False
    
    return True

def test_checkbox_functionality():
    """Test checkbox functionality specifically"""
    print("\nTesting Checkbox Functionality...")
    
    # Test all checkboxes checked
    all_checked = CoverPageDetails(
        to="Test Recipient",
        from_field="Test Sender",
        urgent=True,
        for_review=True,
        please_comment=True,
        please_reply=True
    )
    
    generator = CoverPageGenerator()
    preview = generator.preview_cover_page(all_checked)
    
    # Check that all checkboxes show as checked in preview
    if "[X] Urgent" in preview and "[X] For Review" in preview and \
       "[X] Please Comment" in preview and "[X] Please Reply" in preview:
        print("✅ All checkboxes correctly shown as checked")
    else:
        print("❌ Checkbox display issue in preview")
        return False
    
    # Test no checkboxes checked
    none_checked = CoverPageDetails(
        to="Test Recipient",
        from_field="Test Sender",
        urgent=False,
        for_review=False,
        please_comment=False,
        please_reply=False
    )
    
    preview = generator.preview_cover_page(none_checked)
    
    # Check that all checkboxes show as unchecked in preview
    if "[ ] Urgent" in preview and "[ ] For Review" in preview and \
       "[ ] Please Comment" in preview and "[ ] Please Reply" in preview:
        print("✅ All checkboxes correctly shown as unchecked")
    else:
        print("❌ Checkbox display issue in preview")
        return False
    
    return True

def main():
    """Run all tests"""
    print("🏥 Hospital Cover Page Template Test Suite")
    print("=" * 50)
    
    tests = [
        test_hospital_cover_page,
        test_simple_cover_page,
        test_cover_page_validation,
        test_checkbox_functionality
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
            print()  # Add spacing between tests
        except Exception as e:
            print(f"❌ Test {test.__name__} failed with exception: {e}")
            print()
    
    print("=" * 50)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Cover page template is working correctly.")
        
        # Show generated files
        generated_files = [
            "test_hospital_cover_page.pdf",
            "test_simple_cover_page.pdf"
        ]
        
        print("\n📁 Generated files:")
        for file in generated_files:
            if Path(file).exists():
                size_kb = Path(file).stat().st_size / 1024
                print(f"  • {file} ({size_kb:.1f} KB)")
        
        print("\n💡 You can open these PDF files to see the cover page templates!")
        
    else:
        print("❌ Some tests failed. Please check the implementation.")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
