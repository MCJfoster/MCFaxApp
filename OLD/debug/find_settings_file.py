"""
Script to find and display the MCFax settings file location
"""

import sys
import os
from pathlib import Path

# Add the src directory to the path so we can import the settings module
sys.path.insert(0, 'src')

try:
    from core.settings import get_settings
    
    # Get the settings instance
    settings = get_settings()
    
    # Get the settings file path
    settings_file_path = settings.get_settings_file_path()
    
    print("MCFax Settings File Location:")
    print("=" * 50)
    print(f"Path: {settings_file_path}")
    print()
    
    # Check if the file exists
    if os.path.exists(settings_file_path):
        print("✅ Settings file EXISTS")
        
        # Show file size
        file_size = os.path.getsize(settings_file_path)
        print(f"File size: {file_size} bytes")
        
        # Show current FaxFinder settings
        print("\nCurrent FaxFinder Settings:")
        print("-" * 30)
        faxfinder_settings = settings.get_faxfinder_settings()
        for key, value in faxfinder_settings.items():
            if key == 'password' and value:
                print(f"{key}: {'*' * len(value)}")  # Hide password
            else:
                print(f"{key}: {value}")
        
        print("\nTo edit the settings file:")
        print(f"1. Open: {settings_file_path}")
        print("2. Edit the 'faxfinder' section")
        print("3. Save the file")
        print("4. Restart the application")
        
    else:
        print("❌ Settings file does NOT exist yet")
        print("The file will be created when you first run the application")
        
        # Show what the directory should be
        settings_dir = Path(settings_file_path).parent
        print(f"\nSettings directory: {settings_dir}")
        
        if settings_dir.exists():
            print("✅ Settings directory exists")
        else:
            print("❌ Settings directory does not exist")
            print("It will be created automatically when needed")
    
    print("\nExample FaxFinder configuration:")
    print("-" * 35)
    print('"faxfinder": {')
    print('  "host": "192.168.1.100",')
    print('  "username": "admin",')
    print('  "password": "your_password",')
    print('  "use_https": false,')
    print('  "auto_submit": false')
    print('}')
    
except Exception as e:
    print(f"Error finding settings file: {e}")
    print("\nFallback method - checking standard Windows locations:")
    
    # Try standard Windows paths
    possible_paths = [
        os.path.expandvars(r"%APPDATA%\MCFax\settings.json"),
        os.path.expandvars(r"%LOCALAPPDATA%\MCFax\settings.json"),
        os.path.join(os.getcwd(), "settings.json"),
        os.path.join(os.getcwd(), "config", "settings.json")
    ]
    
    print("\nChecking possible locations:")
    for path in possible_paths:
        if os.path.exists(path):
            print(f"✅ FOUND: {path}")
        else:
            print(f"❌ Not found: {path}")
