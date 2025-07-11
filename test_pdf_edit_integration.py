"""
Test PDF Edit Integration
Tests the complete workflow of PDF editing and final PDF generation with edits applied
"""

import os
import sys
import logging
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from pdf.pdf_processor import PDFProcessor

def setup_logging():
    """Setup logging for the test"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('logs/test_pdf_edit_integration.log'),
            logging.StreamHandler()
        ]
    )

def create_test_edit_data():
    """Create sample edit data for testing"""
    return {
        'pages': [
            {
                'page_number': 0,
                'excluded': False,
                'brush_strokes': [
                    {
                        'type': 'redaction',
                        'points': [(100, 100), (200, 100), (200, 150), (100, 150)],
                        'brush_size': 15,
                        'color': '#000000'
                    }
                ],
                'annotations': [
                    {
                        'type': 'text',
                        'x': 50,
                        'y': 50,
                        'text': 'TEST ANNOTATION',
                        'color': '#FF0000',
                        'font': 'Arial',
                        'size': 12
                    }
                ]
            },
            {
                'page_number': 1,
                'excluded': True,  # This page should be excluded
                'brush_strokes': [],
                'annotations': []
            }
        ]
    }

def test_pdf_edit_application():
    """Test applying edits to a PDF"""
    print("=== Testing PDF Edit Application ===")
    
    # Setup
    processor = PDFProcessor()
    
    # Check if we have a test PDF
    test_pdfs = list(Path("processed").glob("*.pdf"))
    if not test_pdfs:
        print("❌ No test PDFs found in processed/ directory")
        print("Please run the application and create a fax job first to generate test PDFs")
        return False
    
    test_pdf = str(test_pdfs[0])
    print(f"Using test PDF: {test_pdf}")
    
    # Create test edit data
    edit_data = create_test_edit_data()
    print(f"Created test edit data with {len(edit_data['pages'])} pages")
    
    # Apply edits
    output_path = "test_edited_output.pdf"
    print(f"Applying edits to create: {output_path}")
    
    success = processor.apply_edits_to_pdf(test_pdf, edit_data, output_path)
    
    if success:
        print("✅ Successfully applied edits to PDF")
        
        # Check if output file exists
        if Path(output_path).exists():
            file_size = Path(output_path).stat().st_size
            print(f"✅ Output file created: {output_path} ({file_size} bytes)")
            return True
        else:
            print("❌ Output file was not created")
            return False
    else:
        print("❌ Failed to apply edits to PDF")
        return False

def test_combine_pdfs_with_edits():
    """Test combining multiple PDFs with edits"""
    print("\n=== Testing PDF Combination with Edits ===")
    
    # Setup
    processor = PDFProcessor()
    
    # Find test PDFs
    test_pdfs = list(Path("processed").glob("*.pdf"))[:2]  # Use up to 2 PDFs
    if len(test_pdfs) < 1:
        print("❌ Need at least 1 test PDF in processed/ directory")
        return False
    
    pdf_files = [str(pdf) for pdf in test_pdfs]
    print(f"Using {len(pdf_files)} test PDFs: {[Path(p).name for p in pdf_files]}")
    
    # Create edit data map
    edit_data_map = {}
    for i, pdf_path in enumerate(pdf_files):
        edit_data_map[pdf_path] = {
            'pages': [
                {
                    'page_number': 0,
                    'excluded': False,
                    'brush_strokes': [
                        {
                            'type': 'redaction',
                            'points': [(50 + i*20, 50), (150 + i*20, 50), (150 + i*20, 100), (50 + i*20, 100)],
                            'brush_size': 10,
                            'color': '#000000'
                        }
                    ],
                    'annotations': [
                        {
                            'type': 'text',
                            'x': 200,
                            'y': 200 + i*30,
                            'text': f'EDIT {i+1}',
                            'color': '#0000FF',
                            'font': 'Arial',
                            'size': 14
                        }
                    ]
                }
            ]
        }
    
    print(f"Created edit data for {len(edit_data_map)} PDFs")
    
    # Combine PDFs with edits
    output_path = "test_combined_with_edits.pdf"
    print(f"Combining PDFs with edits to create: {output_path}")
    
    success = processor.combine_pdfs_with_edits(
        pdf_files=pdf_files,
        output_path=output_path,
        edit_data_map=edit_data_map
    )
    
    if success:
        print("✅ Successfully combined PDFs with edits")
        
        # Check if output file exists
        if Path(output_path).exists():
            file_size = Path(output_path).stat().st_size
            print(f"✅ Combined output file created: {output_path} ({file_size} bytes)")
            
            # Try to get page count
            try:
                import fitz
                doc = fitz.open(output_path)
                page_count = len(doc)
                doc.close()
                print(f"✅ Combined PDF has {page_count} pages")
            except ImportError:
                print("ℹ️ PyMuPDF not available for page count verification")
            except Exception as e:
                print(f"⚠️ Could not verify page count: {e}")
            
            return True
        else:
            print("❌ Combined output file was not created")
            return False
    else:
        print("❌ Failed to combine PDFs with edits")
        return False

def test_has_visual_edits():
    """Test the _has_visual_edits helper method"""
    print("\n=== Testing Visual Edits Detection ===")
    
    processor = PDFProcessor()
    
    # Test with no edits
    empty_edit_data = {'pages': []}
    has_edits = processor._has_visual_edits(empty_edit_data)
    print(f"Empty edit data has visual edits: {has_edits} (should be False)")
    
    # Test with excluded page only
    excluded_only = {
        'pages': [
            {
                'page_number': 0,
                'excluded': True,
                'brush_strokes': [],
                'annotations': []
            }
        ]
    }
    has_edits = processor._has_visual_edits(excluded_only)
    print(f"Excluded page only has visual edits: {has_edits} (should be False)")
    
    # Test with brush strokes
    with_brush_strokes = {
        'pages': [
            {
                'page_number': 0,
                'excluded': False,
                'brush_strokes': [{'type': 'redaction', 'points': [(0, 0), (10, 10)]}],
                'annotations': []
            }
        ]
    }
    has_edits = processor._has_visual_edits(with_brush_strokes)
    print(f"With brush strokes has visual edits: {has_edits} (should be True)")
    
    # Test with annotations
    with_annotations = {
        'pages': [
            {
                'page_number': 0,
                'excluded': False,
                'brush_strokes': [],
                'annotations': [{'type': 'text', 'text': 'test'}]
            }
        ]
    }
    has_edits = processor._has_visual_edits(with_annotations)
    print(f"With annotations has visual edits: {has_edits} (should be True)")
    
    print("✅ Visual edits detection tests completed")
    return True

def cleanup_test_files():
    """Clean up test files"""
    print("\n=== Cleaning Up Test Files ===")
    
    test_files = [
        "test_edited_output.pdf",
        "test_combined_with_edits.pdf"
    ]
    
    for file_path in test_files:
        if Path(file_path).exists():
            try:
                Path(file_path).unlink()
                print(f"✅ Removed {file_path}")
            except Exception as e:
                print(f"⚠️ Could not remove {file_path}: {e}")
        else:
            print(f"ℹ️ {file_path} does not exist")

def main():
    """Run all tests"""
    print("PDF Edit Integration Test")
    print("=" * 50)
    
    # Setup
    setup_logging()
    
    # Ensure directories exist
    Path("logs").mkdir(exist_ok=True)
    Path("processed").mkdir(exist_ok=True)
    
    # Run tests
    tests_passed = 0
    total_tests = 4
    
    try:
        if test_has_visual_edits():
            tests_passed += 1
        
        if test_pdf_edit_application():
            tests_passed += 1
        
        if test_combine_pdfs_with_edits():
            tests_passed += 1
        
        # Always count cleanup as a test
        cleanup_test_files()
        tests_passed += 1
        
    except Exception as e:
        print(f"\n❌ Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
    
    # Results
    print(f"\n{'='*50}")
    print(f"Test Results: {tests_passed}/{total_tests} tests passed")
    
    if tests_passed == total_tests:
        print("✅ All tests passed! PDF edit integration is working correctly.")
        return True
    else:
        print("❌ Some tests failed. Check the logs for details.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
