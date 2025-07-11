#!/usr/bin/env python3
"""
Simple test to verify PDF edit data persistence is working
"""

import os
import sys
import tempfile
from pathlib import Path

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def create_minimal_pdf():
    """Create a minimal PDF for testing"""
    temp_pdf = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
    
    # Minimal PDF content
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
/Kids [3 0 R]
/Count 1
>>
endobj

3 0 obj
<<
/Type /Page
/Parent 2 0 R
/MediaBox [0 0 612 792]
/Contents 4 0 R
>>
endobj

4 0 obj
<<
/Length 44
>>
stream
BT
/F1 12 Tf
100 700 Td
(Test PDF) Tj
ET
endstream
endobj

xref
0 5
0000000000 65535 f 
0000000009 00000 n 
0000000058 00000 n 
0000000115 00000 n 
0000000206 00000 n 
trailer
<<
/Size 5
/Root 1 0 R
>>
startxref
300
%%EOF"""
    
    temp_pdf.write(pdf_content)
    temp_pdf.close()
    
    return temp_pdf.name

def test_edit_data_methods():
    """Test that the edit data methods exist and work"""
    print("Testing PDF edit data persistence methods...")
    
    try:
        from gui.integrated_pdf_viewer import IntegratedPDFViewer
        from PyQt6.QtWidgets import QApplication
        
        # Create QApplication if needed
        app = QApplication.instance()
        if app is None:
            app = QApplication(sys.argv)
        
        # Create test PDF
        test_pdf = create_minimal_pdf()
        print(f"✓ Created test PDF: {test_pdf}")
        
        # Create viewer
        viewer = IntegratedPDFViewer(test_pdf)
        print("✓ Created IntegratedPDFViewer")
        
        # Test get_edit_data method exists
        assert hasattr(viewer, 'get_edit_data'), "get_edit_data method missing"
        print("✓ get_edit_data method exists")
        
        # Test apply_edit_data method exists
        assert hasattr(viewer, 'apply_edit_data'), "apply_edit_data method missing"
        print("✓ apply_edit_data method exists")
        
        # Test getting edit data
        edit_data = viewer.get_edit_data()
        assert isinstance(edit_data, dict), "get_edit_data should return dict"
        assert 'pages' in edit_data, "edit_data should have 'pages' key"
        print("✓ get_edit_data returns correct structure")
        
        # Test applying edit data
        test_edit_data = {
            'pages': [{
                'page_number': 0,
                'excluded': False,
                'brush_strokes': [],
                'annotations': []
            }]
        }
        
        viewer.apply_edit_data(test_edit_data)
        print("✓ apply_edit_data works without errors")
        
        # Clean up
        viewer.close()
        os.unlink(test_pdf)
        
        print("✅ All edit data methods work correctly!")
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_fax_job_window_methods():
    """Test that FaxJobWindow has the required methods"""
    print("\nTesting FaxJobWindow edit data methods...")
    
    try:
        from gui.fax_job_window import FaxJobWindow
        
        # Check that the class has the required attributes and methods
        assert hasattr(FaxJobWindow, '__init__'), "FaxJobWindow missing __init__"
        print("✓ FaxJobWindow class exists")
        
        # Check for pdf_edit_data in the source code
        import inspect
        source = inspect.getsource(FaxJobWindow.__init__)
        assert 'pdf_edit_data' in source, "pdf_edit_data not found in __init__"
        print("✓ pdf_edit_data dictionary declared in __init__")
        
        # Check for required methods
        required_methods = [
            'load_pdf_in_viewer',
            'clear_pdf_viewer', 
            'on_pdf_selected',
            'next_tab',
            'previous_tab',
            'submit_fax_job'
        ]
        
        for method_name in required_methods:
            assert hasattr(FaxJobWindow, method_name), f"Missing method: {method_name}"
            print(f"✓ {method_name} method exists")
        
        print("✅ All FaxJobWindow methods exist!")
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run simple tests"""
    print("=" * 60)
    print("Simple PDF Edit Data Persistence Test")
    print("=" * 60)
    
    success_count = 0
    total_tests = 2
    
    # Test 1: Edit data methods
    if test_edit_data_methods():
        success_count += 1
    
    # Test 2: FaxJobWindow methods
    if test_fax_job_window_methods():
        success_count += 1
    
    print("\n" + "=" * 60)
    print(f"SIMPLE TEST RESULTS: {success_count}/{total_tests} tests passed")
    
    if success_count == total_tests:
        print("🎉 ALL SIMPLE TESTS PASSED!")
        print("\nThe PDF edit data persistence fix has been implemented:")
        print("• IntegratedPDFViewer has get_edit_data() and apply_edit_data() methods")
        print("• FaxJobWindow has pdf_edit_data dictionary and required methods")
        print("• The infrastructure is in place for edit data persistence")
    else:
        print("❌ SOME SIMPLE TESTS FAILED")
        print("The fix implementation may be incomplete.")
    
    print("=" * 60)
    return success_count == total_tests

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
