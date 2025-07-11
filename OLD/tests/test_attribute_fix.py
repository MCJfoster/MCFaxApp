"""
Test script to verify the AttributeError fix in FaxJobWindow
"""

import sys
import os
sys.path.append('src')

from PyQt6.QtWidgets import QApplication
from gui.fax_job_window import FaxJobWindow
from database.models import ContactRepository, FaxJobRepository
from database.connection import DatabaseConnection

def test_fax_job_window_attributes():
    """Test that all required attributes exist in FaxJobWindow"""
    
    app = QApplication(sys.argv)
    
    try:
        # Create database connection
        db = DatabaseConnection()
        db.connect()
        
        # Create repositories
        contact_repo = ContactRepository(db)
        fax_job_repo = FaxJobRepository(db)
        
        # Create FaxJobWindow with test data
        selected_pdfs = ["test.pdf"]  # Mock PDF file
        window = FaxJobWindow(selected_pdfs, contact_repo, fax_job_repo)
        
        # Test that all required attributes exist
        required_attributes = [
            'cover_preview_text',
            'cover_preview_label', 
            'sender_name_edit',
            'sender_email_edit',
            'from_name_edit',
            'from_email_edit'
        ]
        
        missing_attributes = []
        for attr in required_attributes:
            if not hasattr(window, attr):
                missing_attributes.append(attr)
        
        if missing_attributes:
            print(f"❌ FAILED: Missing attributes: {missing_attributes}")
            return False
        else:
            print("✅ SUCCESS: All required attributes exist")
            
        # Test that aliases work correctly
        if window.sender_name_edit is not window.from_name_edit:
            print("❌ FAILED: sender_name_edit alias not working")
            return False
            
        if window.sender_email_edit is not window.from_email_edit:
            print("❌ FAILED: sender_email_edit alias not working")
            return False
            
        print("✅ SUCCESS: Attribute aliases working correctly")
        
        # Test that the update_cover_preview method can be called without error
        try:
            window.update_cover_preview()
            print("✅ SUCCESS: update_cover_preview method works")
        except AttributeError as e:
            print(f"❌ FAILED: update_cover_preview still has AttributeError: {e}")
            return False
        except Exception as e:
            print(f"⚠️  WARNING: update_cover_preview has other error (expected): {e}")
            # This is expected since we don't have real data
        
        # Test that the update_cover_visual_preview method can be called
        try:
            window.update_cover_visual_preview()
            print("✅ SUCCESS: update_cover_visual_preview method works")
        except AttributeError as e:
            print(f"❌ FAILED: update_cover_visual_preview has AttributeError: {e}")
            return False
        except Exception as e:
            print(f"⚠️  WARNING: update_cover_visual_preview has other error (expected): {e}")
            # This is expected since we don't have real data
        
        return True
        
    except Exception as e:
        print(f"❌ FAILED: Error creating FaxJobWindow: {e}")
        return False
    finally:
        app.quit()

if __name__ == "__main__":
    print("Testing FaxJobWindow AttributeError fix...")
    success = test_fax_job_window_attributes()
    
    if success:
        print("\n🎉 All tests passed! The AttributeError should be fixed.")
    else:
        print("\n💥 Some tests failed. The AttributeError may still exist.")
    
    sys.exit(0 if success else 1)
