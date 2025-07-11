"""
Simple script to check if XML files are being created
"""

import os
import glob
from datetime import datetime

def check_xml_files():
    """Check for XML files in the xml directory"""
    print("=== Checking for XML Files ===\n")
    
    # Check if xml directory exists
    if not os.path.exists('xml'):
        print("❌ xml/ directory does not exist")
        return
    
    print("✓ xml/ directory exists")
    
    # List all XML files
    xml_files = glob.glob('xml/*.xml')
    
    if not xml_files:
        print("❌ No XML files found in xml/ directory")
        return
    
    print(f"✓ Found {len(xml_files)} XML file(s):")
    
    for xml_file in xml_files:
        try:
            # Get file info
            stat = os.stat(xml_file)
            size = stat.st_size
            modified = datetime.fromtimestamp(stat.st_mtime)
            
            print(f"  📄 {xml_file}")
            print(f"     Size: {size} bytes")
            print(f"     Modified: {modified}")
            
            # Read and display first few lines
            with open(xml_file, 'r', encoding='utf-8') as f:
                content = f.read()
                lines = content.split('\n')
                print(f"     Content preview (first 5 lines):")
                for i, line in enumerate(lines[:5]):
                    print(f"       {i+1}: {line}")
                print(f"     Total lines: {len(lines)}")
                print()
                
        except Exception as e:
            print(f"     ❌ Error reading file: {e}")
    
    # Check the most recent XML file
    if xml_files:
        latest_file = max(xml_files, key=os.path.getmtime)
        print(f"📋 Most recent XML file: {latest_file}")
        
        try:
            with open(latest_file, 'r', encoding='utf-8') as f:
                content = f.read()
                print(f"📄 Full content of {latest_file}:")
                print("=" * 50)
                print(content)
                print("=" * 50)
        except Exception as e:
            print(f"❌ Error reading latest file: {e}")

if __name__ == "__main__":
    check_xml_files()
