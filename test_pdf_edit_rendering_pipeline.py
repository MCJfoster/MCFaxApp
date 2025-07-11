#!/usr/bin/env python3
"""
PDF Edit Rendering Pipeline Diagnostic Test
This test creates a PDF, applies edits using the real pipeline, and generates output for visual verification
"""

import os
import sys
import json
import logging
import tempfile
from pathlib import Path

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def setup_logging():
    """Setup detailed logging for debugging"""
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('test_edit_rendering_debug.log')
        ]
    )
    return logging.getLogger(__name__)

def create_test_pdf():
    """Create a simple test PDF with readable text for edit testing"""
    logger = logging.getLogger(__name__)
    
    try:
        from reportlab.pdfgen import canvas
        from reportlab.lib.pagesizes import letter
        
        # Create test PDF
        test_pdf_path = "test_input.pdf"
        
        c = canvas.Canvas(test_pdf_path, pagesize=letter)
        
        # Page 1 - Text for redaction testing
        c.drawString(100, 750, "PDF Edit Rendering Test - Page 1")
        c.drawString(100, 700, "This text should be REDACTED when processed")
        c.drawString(100, 650, "Normal text that should remain visible")
        c.drawString(100, 600, "Another line for testing redaction accuracy")
        c.showPage()
        
        # Page 2 - Text for highlight testing  
        c.drawString(100, 750, "PDF Edit Rendering Test - Page 2")
        c.drawString(100, 700, "This text should be HIGHLIGHTED when processed")
        c.drawString(100, 650, "Normal text without highlighting")
        c.drawString(100, 600, "Test annotation should appear near here")
        c.showPage()
        
        c.save()
        
        logger.info(f"✓ Created test PDF: {test_pdf_path}")
        return test_pdf_path
        
    except ImportError:
        logger.warning("ReportLab not available, creating minimal PDF manually")
        
        # Fallback: create minimal PDF manually
        test_pdf_path = "test_input.pdf"
        
        pdf_content = b"""%PDF-1.4
1 0 obj
<<
/Type /Catalog
/Pages 2 0 R
>>
endobj

2 0 obj
<<
/Type /Pages
/Kids [3 0 R 5 0 R]
/Count 2
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
/F1 <<
/Type /Font
/Subtype /Type1
/BaseFont /Helvetica
>>
>>
>>
>>
endobj

4 0 obj
<<
/Length 200
>>
stream
BT
/F1 12 Tf
100 750 Td
(PDF Edit Test - Page 1) Tj
0 -50 Td
(This text should be REDACTED) Tj
0 -50 Td
(Normal text that should remain) Tj
ET
endstream
endobj

5 0 obj
<<
/Type /Page
/Parent 2 0 R
/MediaBox [0 0 612 792]
/Contents 6 0 R
/Resources <<
/Font <<
/F1 <<
/Type /Font
/Subtype /Type1
/BaseFont /Helvetica
>>
>>
>>
>>
endobj

6 0 obj
<<
/Length 200
>>
stream
BT
/F1 12 Tf
100 750 Td
(PDF Edit Test - Page 2) Tj
0 -50 Td
(This text should be HIGHLIGHTED) Tj
0 -50 Td
(Test annotation should appear here) Tj
ET
endstream
endobj

xref
0 7
0000000000 65535 f 
0000000009 00000 n 
0000000058 00000 n 
0000000115 00000 n 
0000000300 00000 n 
0000000550 00000 n 
0000000735 00000 n 
trailer
<<
/Size 7
/Root 1 0 R
>>
startxref
985
%%EOF"""
        
        with open(test_pdf_path, 'wb') as f:
            f.write(pdf_content)
        
        logger.info(f"✓ Created minimal test PDF: {test_pdf_path}")
        return test_pdf_path

def create_test_edit_data():
    """Create test edit data in the same format as the UI"""
    logger = logging.getLogger(__name__)
    
    # This should match the format from IntegratedPDFViewer.get_edit_data()
    edit_data = {
        'pages': [
            {
                'page_number': 0,
                'excluded': False,
                'brush_strokes': [
                    {
                        'type': 'redaction',
                        'points': [(200, 700), (350, 700), (350, 715), (200, 715)],  # Rectangle over "REDACTED"
                        'brush_size': 15,
                        'color': '#000000'
                    }
                ],
                'annotations': [
                    {
                        'type': 'text',
                        'x': 400,
                        'y': 650,
                        'text': 'TEST REDACTION ANNOTATION',
                        'color': '#FF0000',
                        'size': 12
                    }
                ]
            },
            {
                'page_number': 1,
                'excluded': False,
                'brush_strokes': [
                    {
                        'type': 'highlight',
                        'points': [(200, 700), (380, 700), (380, 715), (200, 715)],  # Rectangle over "HIGHLIGHTED"
                        'brush_size': 10,
                        'color': '#FFFF00'  # Yellow highlight
                    }
                ],
                'annotations': [
                    {
                        'type': 'text',
                        'x': 400,
                        'y': 600,
                        'text': 'TEST HIGHLIGHT ANNOTATION',
                        'color': '#0000FF',
                        'size': 12
                    }
                ]
            }
        ]
    }
    
    # Save edit data for inspection
    with open('test_edit_data.json', 'w') as f:
        json.dump(edit_data, f, indent=2)
    
    logger.info("✓ Created test edit data")
    logger.info(f"Edit data structure: {json.dumps(edit_data, indent=2)}")
    
    return edit_data

def test_pymupdf_availability():
    """Test if PyMuPDF is available and working"""
    logger = logging.getLogger(__name__)
    
    try:
        import fitz
        logger.info(f"✓ PyMuPDF available - Version: {fitz.version}")
        
        # Test basic functionality
        test_doc = fitz.open()
        test_page = test_doc.new_page()
        test_page.insert_text((100, 100), "Test text")
        test_doc.close()
        
        logger.info("✓ PyMuPDF basic functionality test passed")
        return True
        
    except ImportError:
        logger.error("✗ PyMuPDF not available - this is required for PDF editing")
        return False
    except Exception as e:
        logger.error(f"✗ PyMuPDF test failed: {e}")
        return False

def test_pdf_processor_edit_application():
    """Test the PDFProcessor.apply_edits_to_pdf method directly"""
    logger = logging.getLogger(__name__)
    
    try:
        from pdf.pdf_processor import PDFProcessor
        
        # Create test inputs
        input_pdf = create_test_pdf()
        edit_data = create_test_edit_data()
        output_pdf = "test_edit_rendering_output.pdf"
        
        # Test PyMuPDF first
        if not test_pymupdf_availability():
            logger.error("Cannot proceed without PyMuPDF")
            return False
        
        # Create PDF processor
        processor = PDFProcessor()
        logger.info("✓ Created PDFProcessor instance")
        
        # Apply edits
        logger.info("=== Applying edits to PDF ===")
        logger.info(f"Input PDF: {input_pdf}")
        logger.info(f"Output PDF: {output_pdf}")
        logger.info(f"Edit data: {len(edit_data['pages'])} pages with edits")
        
        success = processor.apply_edits_to_pdf(input_pdf, edit_data, output_pdf)
        
        if success:
            logger.info(f"✓ apply_edits_to_pdf returned success")
            
            # Verify output file exists
            if os.path.exists(output_pdf):
                file_size = os.path.getsize(output_pdf)
                logger.info(f"✓ Output PDF created: {output_pdf} ({file_size} bytes)")
                
                # Compare file sizes
                input_size = os.path.getsize(input_pdf)
                logger.info(f"Input PDF size: {input_size} bytes")
                logger.info(f"Output PDF size: {file_size} bytes")
                
                if file_size > input_size * 0.8:  # Should be similar size or larger
                    logger.info("✓ Output PDF size looks reasonable")
                else:
                    logger.warning("⚠️ Output PDF seems too small - edits may not have been applied")
                
                return True
            else:
                logger.error("✗ Output PDF file was not created")
                return False
        else:
            logger.error("✗ apply_edits_to_pdf returned failure")
            return False
            
    except Exception as e:
        logger.error(f"✗ PDF processor test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_brush_stroke_rendering():
    """Test the brush stroke rendering specifically"""
    logger = logging.getLogger(__name__)
    
    try:
        import fitz
        
        # Create a simple test document
        doc = fitz.open()
        page = doc.new_page()
        
        # Add some text to redact
        page.insert_text((100, 100), "This text will be redacted", fontsize=12)
        
        # Test redaction
        logger.info("=== Testing redaction rendering ===")
        redact_rect = fitz.Rect(100, 90, 250, 110)  # Rectangle over the text
        redact_annot = page.add_redact_annot(redact_rect)
        redact_annot.set_colors(stroke=(0, 0, 0), fill=(0, 0, 0))  # Black
        redact_annot.update()
        
        # Apply redactions
        page.apply_redactions()
        
        # Test highlight
        logger.info("=== Testing highlight rendering ===")
        page.insert_text((100, 150), "This text will be highlighted", fontsize=12)
        highlight_rect = fitz.Rect(100, 140, 280, 160)
        highlight_annot = page.add_highlight_annot(highlight_rect)
        highlight_annot.set_colors(stroke=(1, 1, 0))  # Yellow
        highlight_annot.update()
        
        # Test text annotation
        logger.info("=== Testing text annotation ===")
        text_point = fitz.Point(100, 200)
        text_annot = page.add_text_annot(text_point, "Test annotation")
        text_annot.set_info(content="Test annotation content")
        text_annot.update()
        
        # Save test document
        test_output = "test_brush_stroke_rendering.pdf"
        doc.save(test_output)
        doc.close()
        
        logger.info(f"✓ Brush stroke rendering test saved to: {test_output}")
        
        # Verify file was created
        if os.path.exists(test_output):
            file_size = os.path.getsize(test_output)
            logger.info(f"✓ Test file created: {file_size} bytes")
            return True
        else:
            logger.error("✗ Test file was not created")
            return False
            
    except Exception as e:
        logger.error(f"✗ Brush stroke rendering test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_complete_pipeline():
    """Test the complete pipeline including combine_pdfs_with_edits"""
    logger = logging.getLogger(__name__)
    
    try:
        from pdf.pdf_processor import PDFProcessor
        
        # Create test inputs
        input_pdf = create_test_pdf()
        edit_data = create_test_edit_data()
        
        # Create edit data map (as used in real application)
        edit_data_map = {input_pdf: edit_data}
        
        output_pdf = "test_complete_pipeline_output.pdf"
        
        # Create PDF processor
        processor = PDFProcessor()
        
        # Test the complete pipeline
        logger.info("=== Testing complete pipeline (combine_pdfs_with_edits) ===")
        success = processor.combine_pdfs_with_edits(
            pdf_files=[input_pdf],
            output_path=output_pdf,
            edit_data_map=edit_data_map,
            excluded_pages=None
        )
        
        if success:
            logger.info(f"✓ Complete pipeline test successful")
            
            if os.path.exists(output_pdf):
                file_size = os.path.getsize(output_pdf)
                logger.info(f"✓ Pipeline output PDF created: {output_pdf} ({file_size} bytes)")
                return True
            else:
                logger.error("✗ Pipeline output PDF was not created")
                return False
        else:
            logger.error("✗ Complete pipeline test failed")
            return False
            
    except Exception as e:
        logger.error(f"✗ Complete pipeline test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all diagnostic tests"""
    logger = setup_logging()
    
    print("=" * 80)
    print("PDF Edit Rendering Pipeline Diagnostic Test")
    print("=" * 80)
    
    test_results = {}
    
    # Test 1: PyMuPDF availability
    print("\n1. Testing PyMuPDF availability...")
    test_results['pymupdf'] = test_pymupdf_availability()
    
    # Test 2: Brush stroke rendering
    print("\n2. Testing brush stroke rendering...")
    test_results['brush_strokes'] = test_brush_stroke_rendering()
    
    # Test 3: PDF processor edit application
    print("\n3. Testing PDF processor edit application...")
    test_results['pdf_processor'] = test_pdf_processor_edit_application()
    
    # Test 4: Complete pipeline
    print("\n4. Testing complete pipeline...")
    test_results['complete_pipeline'] = test_complete_pipeline()
    
    # Summary
    print("\n" + "=" * 80)
    print("DIAGNOSTIC TEST RESULTS")
    print("=" * 80)
    
    for test_name, result in test_results.items():
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{test_name:20} : {status}")
    
    # Files created for inspection
    print("\nFILES CREATED FOR INSPECTION:")
    files_to_check = [
        "test_input.pdf",
        "test_edit_data.json", 
        "test_edit_rendering_output.pdf",
        "test_brush_stroke_rendering.pdf",
        "test_complete_pipeline_output.pdf",
        "test_edit_rendering_debug.log"
    ]
    
    for filename in files_to_check:
        if os.path.exists(filename):
            file_size = os.path.getsize(filename)
            print(f"  ✓ {filename} ({file_size} bytes)")
        else:
            print(f"  ✗ {filename} (not created)")
    
    print("\n" + "=" * 80)
    print("VISUAL VERIFICATION INSTRUCTIONS:")
    print("=" * 80)
    print("1. Open 'test_edit_rendering_output.pdf' to check if edits are visible")
    print("2. Look for:")
    print("   - Black redaction box over 'REDACTED' text on page 1")
    print("   - Yellow highlight over 'HIGHLIGHTED' text on page 2") 
    print("   - Red and blue text annotations")
    print("3. Compare with 'test_input.pdf' (original without edits)")
    print("4. Check 'test_edit_rendering_debug.log' for detailed debug info")
    
    # Overall result
    all_passed = all(test_results.values())
    if all_passed:
        print("\n🎉 ALL TESTS PASSED - Edit rendering should be working!")
    else:
        print("\n❌ SOME TESTS FAILED - This explains why edits don't appear in output")
        print("Check the debug log and failed test outputs for details.")
    
    return all_passed

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
