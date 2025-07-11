"""
Test script for PDF processing components
Tests PDF combining, page exclusion, cover page generation, and size validation
"""

import os
import sys
import logging
from pathlib import Path
from datetime import datetime

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from pdf.pdf_processor import PDFProcessor, quick_combine_pdfs, get_total_pages, validate_pdf_files
from pdf.pdf_browser import PDFBrowser, PDFInfo
from pdf.cover_page import CoverPageGenerator, create_simple_cover_page
from database.models import CoverPageDetails

def setup_logging():
    """Setup logging for tests"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

def create_test_pdfs():
    """Create multiple test PDFs for testing"""
    from reportlab.lib.pagesizes import letter
    from reportlab.platypus import SimpleDocTemplate, Paragraph, PageBreak
    from reportlab.lib.styles import getSampleStyleSheet
    
    os.makedirs("test_files", exist_ok=True)
    styles = getSampleStyleSheet()
    
    # Create PDF 1 (3 pages)
    pdf1_path = "test_files/document1.pdf"
    doc1 = SimpleDocTemplate(pdf1_path, pagesize=letter)
    story1 = []
    story1.append(Paragraph("Document 1 - Page 1", styles['Title']))
    story1.append(Paragraph("This is the first page of document 1.", styles['Normal']))
    story1.append(PageBreak())
    story1.append(Paragraph("Document 1 - Page 2", styles['Title']))
    story1.append(Paragraph("This is the second page of document 1.", styles['Normal']))
    story1.append(PageBreak())
    story1.append(Paragraph("Document 1 - Page 3", styles['Title']))
    story1.append(Paragraph("This is the third page of document 1.", styles['Normal']))
    doc1.build(story1)
    
    # Create PDF 2 (2 pages)
    pdf2_path = "test_files/document2.pdf"
    doc2 = SimpleDocTemplate(pdf2_path, pagesize=letter)
    story2 = []
    story2.append(Paragraph("Document 2 - Page 1", styles['Title']))
    story2.append(Paragraph("This is the first page of document 2.", styles['Normal']))
    story2.append(PageBreak())
    story2.append(Paragraph("Document 2 - Page 2", styles['Title']))
    story2.append(Paragraph("This is the second page of document 2.", styles['Normal']))
    doc2.build(story2)
    
    # Create PDF 3 (1 page)
    pdf3_path = "test_files/document3.pdf"
    doc3 = SimpleDocTemplate(pdf3_path, pagesize=letter)
    story3 = []
    story3.append(Paragraph("Document 3 - Single Page", styles['Title']))
    story3.append(Paragraph("This is a single page document.", styles['Normal']))
    doc3.build(story3)
    
    return [pdf1_path, pdf2_path, pdf3_path]

def test_pdf_info():
    """Test PDF information extraction"""
    print("\n" + "="*60)
    print("TESTING PDF INFO EXTRACTION")
    print("="*60)
    
    pdf_paths = create_test_pdfs()
    
    for pdf_path in pdf_paths:
        pdf_info = PDFInfo(pdf_path)
        print(f"\nPDF: {pdf_info.name}")
        print(f"  Valid: {pdf_info.is_valid}")
        print(f"  Size: {pdf_info.size_mb:.2f} MB")
        print(f"  Pages: {pdf_info.page_count}")
        print(f"  Created: {pdf_info.created_time}")
        if pdf_info.error_message:
            print(f"  Error: {pdf_info.error_message}")
    
    return True

def test_pdf_browser():
    """Test PDF browser functionality"""
    print("\n" + "="*60)
    print("TESTING PDF BROWSER")
    print("="*60)
    
    # Create test PDFs
    create_test_pdfs()
    
    # Test PDF browser
    browser = PDFBrowser("test_files")
    pdf_files = browser.get_pdf_files()
    
    print(f"Found {len(pdf_files)} PDF files:")
    for pdf_info in pdf_files:
        print(f"  {pdf_info}")
    
    # Test folder stats
    stats = browser.get_folder_stats()
    print(f"\nFolder Statistics:")
    print(f"  Total files: {stats['total_files']}")
    print(f"  Valid files: {stats['valid_files']}")
    print(f"  Invalid files: {stats['invalid_files']}")
    print(f"  Total size: {stats['total_size_mb']} MB")
    print(f"  Total pages: {stats['total_pages']}")
    
    # Test search
    search_results = browser.search_pdfs("document1")
    print(f"\nSearch results for 'document1': {len(search_results)} files")
    
    return len(pdf_files) > 0

def test_pdf_combining():
    """Test PDF combining functionality"""
    print("\n" + "="*60)
    print("TESTING PDF COMBINING")
    print("="*60)
    
    pdf_paths = create_test_pdfs()
    processor = PDFProcessor()
    
    # Test basic combining
    output_path = "test_files/combined_basic.pdf"
    success = processor.combine_pdfs(pdf_paths, output_path)
    
    if success:
        print(f"✓ Successfully combined PDFs: {output_path}")
        
        # Check combined PDF info
        combined_info = processor.get_pdf_info(output_path)
        print(f"  Combined PDF pages: {combined_info['page_count']}")
        print(f"  Combined PDF size: {combined_info['size_mb']} MB")
    else:
        print("✗ Failed to combine PDFs")
        return False
    
    # Test combining with page exclusions
    excluded_pages = {
        pdf_paths[0]: [1],  # Exclude page 2 from document1 (0-based)
        pdf_paths[1]: [0]   # Exclude page 1 from document2 (0-based)
    }
    
    output_path_excluded = "test_files/combined_excluded.pdf"
    success = processor.combine_pdfs(pdf_paths, output_path_excluded, excluded_pages)
    
    if success:
        print(f"✓ Successfully combined PDFs with exclusions: {output_path_excluded}")
        
        # Check excluded PDF info
        excluded_info = processor.get_pdf_info(output_path_excluded)
        print(f"  Excluded PDF pages: {excluded_info['page_count']}")
        print(f"  Expected pages: {3-1 + 2-1 + 1} = 4")  # Original pages minus excluded
    else:
        print("✗ Failed to combine PDFs with exclusions")
        return False
    
    return True

def test_pdf_validation():
    """Test PDF validation functionality"""
    print("\n" + "="*60)
    print("TESTING PDF VALIDATION")
    print("="*60)
    
    pdf_paths = create_test_pdfs()
    processor = PDFProcessor()
    
    # Test validation without exclusions
    result = processor.validate_pdf_combination(pdf_paths)
    print(f"Validation without exclusions:")
    print(f"  Valid: {result['is_valid']}")
    print(f"  Total size: {result['total_size_mb']} MB")
    print(f"  Total pages: {result['total_pages']}")
    print(f"  File count: {result['file_count']}")
    
    if result['errors']:
        print(f"  Errors: {result['errors']}")
    if result['warnings']:
        print(f"  Warnings: {result['warnings']}")
    
    # Test validation with exclusions
    excluded_pages = {pdf_paths[0]: [0, 1]}  # Exclude first 2 pages
    result_excluded = processor.validate_pdf_combination(pdf_paths, excluded_pages)
    print(f"\nValidation with exclusions:")
    print(f"  Valid: {result_excluded['is_valid']}")
    print(f"  Total pages: {result_excluded['total_pages']}")
    
    # Test size limit validation
    result_size = processor.validate_pdf_combination(pdf_paths, max_size_mb=0.001)  # Very small limit
    print(f"\nValidation with small size limit:")
    print(f"  Valid: {result_size['is_valid']}")
    if result_size['errors']:
        print(f"  Errors: {result_size['errors']}")
    
    return True

def test_cover_page_integration():
    """Test cover page generation and integration"""
    print("\n" + "="*60)
    print("TESTING COVER PAGE INTEGRATION")
    print("="*60)
    
    # Create cover page
    cover_details = CoverPageDetails(
        to="Test Recipient",
        attn="Document Processing",
        from_field="Test Sender",
        company="Test Company",
        fax="+15551234567",
        phone="+15559876543",
        date=datetime.now().strftime("%m/%d/%Y"),
        subject="Test Document Transmission",
        re="Test Reference",
        cc="test@example.com",
        comments="This is a test cover page for PDF integration testing.",
        msg="Please review the attached documents."
    )
    
    generator = CoverPageGenerator()
    cover_path = "test_files/test_cover.pdf"
    
    success = generator.generate_cover_page(cover_details, cover_path, page_count=3)
    
    if success:
        print(f"✓ Generated cover page: {cover_path}")
        
        # Test adding cover page to content
        pdf_paths = create_test_pdfs()
        processor = PDFProcessor()
        
        # First combine content PDFs
        content_path = "test_files/content_combined.pdf"
        processor.combine_pdfs(pdf_paths, content_path)
        
        # Add cover page
        final_path = "test_files/final_with_cover.pdf"
        success = processor.add_cover_page(cover_path, content_path, final_path)
        
        if success:
            print(f"✓ Added cover page to content: {final_path}")
            
            # Check final PDF
            final_info = processor.get_pdf_info(final_path)
            print(f"  Final PDF pages: {final_info['page_count']}")
            print(f"  Final PDF size: {final_info['size_mb']} MB")
            
            return True
        else:
            print("✗ Failed to add cover page")
            return False
    else:
        print("✗ Failed to generate cover page")
        return False

def test_utility_functions():
    """Test utility functions"""
    print("\n" + "="*60)
    print("TESTING UTILITY FUNCTIONS")
    print("="*60)
    
    pdf_paths = create_test_pdfs()
    
    # Test quick combine
    quick_output = "test_files/quick_combined.pdf"
    success = quick_combine_pdfs(pdf_paths, quick_output)
    print(f"Quick combine: {'SUCCESS' if success else 'FAILED'}")
    
    # Test total pages
    total_pages = get_total_pages(pdf_paths)
    print(f"Total pages across all PDFs: {total_pages}")
    
    # Test validation utility
    validation = validate_pdf_files(pdf_paths)
    print(f"Validation utility: {'VALID' if validation['is_valid'] else 'INVALID'}")
    
    # Test simple cover page creation
    simple_cover = create_simple_cover_page(
        to="Simple Recipient",
        from_name="Simple Sender",
        subject="Simple Test",
        pages=5,
        output_path="test_files/simple_cover.pdf"
    )
    print(f"Simple cover page created: {simple_cover}")
    
    return True

def test_error_scenarios():
    """Test error handling scenarios"""
    print("\n" + "="*60)
    print("TESTING ERROR SCENARIOS")
    print("="*60)
    
    processor = PDFProcessor()
    
    # Test with non-existent files
    print("Testing with non-existent files...")
    success = processor.combine_pdfs(["non_existent.pdf"], "test_files/error_test.pdf")
    print(f"  Non-existent file handling: {'FAILED as expected' if not success else 'UNEXPECTED SUCCESS'}")
    
    # Test with empty file list
    print("Testing with empty file list...")
    success = processor.combine_pdfs([], "test_files/empty_test.pdf")
    print(f"  Empty file list handling: {'FAILED as expected' if not success else 'UNEXPECTED SUCCESS'}")
    
    # Test PDF info with non-existent file
    print("Testing PDF info with non-existent file...")
    info = processor.get_pdf_info("non_existent.pdf")
    print(f"  Error handling: {'CORRECT' if 'error' in info else 'INCORRECT'}")
    
    # Test validation with invalid exclusions
    pdf_paths = create_test_pdfs()
    excluded_pages = {pdf_paths[0]: [0, 1, 2, 3, 4]}  # Exclude more pages than exist
    result = processor.validate_pdf_combination(pdf_paths, excluded_pages)
    print(f"Invalid exclusions handling: {'HANDLED' if result['warnings'] else 'NOT HANDLED'}")
    
    return True

def run_all_tests():
    """Run all PDF processing tests"""
    print("PDF PROCESSING TESTING")
    print("="*60)
    print(f"Test started at: {datetime.now()}")
    
    setup_logging()
    
    # Create test directory
    os.makedirs("test_files", exist_ok=True)
    
    tests = [
        ("PDF Info Extraction", test_pdf_info),
        ("PDF Browser", test_pdf_browser),
        ("PDF Combining", test_pdf_combining),
        ("PDF Validation", test_pdf_validation),
        ("Cover Page Integration", test_cover_page_integration),
        ("Utility Functions", test_utility_functions),
        ("Error Scenarios", test_error_scenarios)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, "PASSED" if result else "FAILED"))
        except Exception as e:
            print(f"✗ {test_name} failed with error: {e}")
            results.append((test_name, f"ERROR: {e}"))
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    for test_name, result in results:
        status_symbol = "✓" if result == "PASSED" else "✗"
        print(f"{status_symbol} {test_name}: {result}")
    
    passed_count = sum(1 for _, result in results if result == "PASSED")
    total_count = len(results)
    
    print(f"\nOverall: {passed_count}/{total_count} tests passed")
    print(f"Test completed at: {datetime.now()}")
    
    if passed_count == total_count:
        print("\n🎉 All PDF processing tests passed!")
    else:
        print(f"\n⚠️  {total_count - passed_count} test(s) failed. Please review and fix issues.")

if __name__ == "__main__":
    run_all_tests()
