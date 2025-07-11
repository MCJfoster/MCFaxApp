"""
Test script for the Settings Window functionality
"""

import sys
import os
import logging
from pathlib import Path
from PyQt6.QtWidgets import QApplication, QMessageBox

# Add the src directory to the path
sys.path.insert(0, 'src')

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def test_settings_window():
    """Test the settings window functionality"""
    app = QApplication(sys.argv)
    
    try:
        # Import after setting up the path
        from gui.settings_window import SettingsWindow
        from core.settings import get_settings
        
        print("Testing Settings Window...")
        
        # Get settings instance
        settings = get_settings()
        print(f"Settings file location: {settings.get_settings_file_path()}")
        
        # Check if settings file exists
        settings_file = Path(settings.get_settings_file_path())
        if settings_file.exists():
            print("✅ Settings file exists")
            print(f"File size: {settings_file.stat().st_size} bytes")
        else:
            print("❌ Settings file does not exist")
        
        # Test FaxFinder settings
        faxfinder_settings = settings.get_faxfinder_settings()
        print("\nCurrent FaxFinder Settings:")
        for key, value in faxfinder_settings.items():
            if key == 'password' and value:
                print(f"  {key}: {'*' * len(value)}")
            else:
                print(f"  {key}: {value}")
        
        # Create and show settings window
        print("\nOpening Settings Window...")
        settings_window = SettingsWindow()
        
        # Show information about the window
        print(f"Window title: {settings_window.windowTitle()}")
        print(f"Window size: {settings_window.size().width()}x{settings_window.size().height()}")
        print(f"Number of tabs: {settings_window.tab_widget.count()}")
        
        for i in range(settings_window.tab_widget.count()):
            tab_text = settings_window.tab_widget.tabText(i)
            print(f"  Tab {i}: {tab_text}")
        
        # Show the window
        settings_window.show()
        
        # Show success message
        QMessageBox.information(
            settings_window,
            "Settings Test",
            "Settings window opened successfully!\n\n"
            "Features to test:\n"
            "• FaxFinder connection settings\n"
            "• Test connection button\n"
            "• General application settings\n"
            "• Sender information\n"
            "• Save/Cancel functionality\n\n"
            "The settings file will be created automatically\n"
            f"at: {settings.get_settings_file_path()}"
        )
        
        # Run the application
        sys.exit(app.exec())
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("Make sure all required modules are available")
        return False
        
    except Exception as e:
        print(f"❌ Error testing settings window: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_settings_window()
