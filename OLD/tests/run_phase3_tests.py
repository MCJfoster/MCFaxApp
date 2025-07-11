"""
Comprehensive Test Runner for Phase 3: FaxFinder Integration
Runs all tests for XML generation, PDF processing, and API integration
"""

import os
import sys
import subprocess
from pathlib import Path
from datetime import datetime

def run_test_script(script_name: str, description: str) -> bool:
    """
    Run a test script and return success status
    
    Args:
        script_name: Name of the test script
        description: Description of the test
        
    Returns:
        bool: True if test passed, False otherwise
    """
    print(f"\n{'='*80}")
    print(f"RUNNING: {description}")
    print(f"Script: {script_name}")
    print('='*80)
    
    try:
        # Run the test script
        result = subprocess.run([sys.executable, script_name], 
                              capture_output=True, 
                              text=True, 
                              timeout=300)  # 5 minute timeout
        
        # Print output
        if result.stdout:
            print("STDOUT:")
            print(result.stdout)
        
        if result.stderr:
            print("STDERR:")
            print(result.stderr)
        
        # Check result
        if result.returncode == 0:
            print(f"✓ {description} - PASSED")
            return True
        else:
            print(f"✗ {description} - FAILED (exit code: {result.returncode})")
            return False
            
    except subprocess.TimeoutExpired:
        print(f"✗ {description} - TIMEOUT (exceeded 5 minutes)")
        return False
    except Exception as e:
        print(f"✗ {description} - ERROR: {e}")
        return False

def check_dependencies():
    """Check if all required dependencies are available"""
    print("CHECKING DEPENDENCIES")
    print("="*80)
    
    required_packages = [
        'reportlab',
        'PyPDF2', 
        'requests',
        'pyodbc'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
            print(f"✓ {package}")
        except ImportError:
            print(f"✗ {package} - MISSING")
            missing_packages.append(package)
    
    if missing_packages:
        print(f"\nMissing packages: {', '.join(missing_packages)}")
        print("Install with: pip install " + " ".join(missing_packages))
        return False
    
    print("\n✓ All dependencies available")
    return True

def create_test_summary(results: list):
    """Create a comprehensive test summary"""
    print("\n" + "="*80)
    print("PHASE 3 TESTING SUMMARY")
    print("="*80)
    print(f"Test completed at: {datetime.now()}")
    print()
    
    passed_tests = []
    failed_tests = []
    
    for test_name, success in results:
        if success:
            passed_tests.append(test_name)
            print(f"✓ {test_name}")
        else:
            failed_tests.append(test_name)
            print(f"✗ {test_name}")
    
    print(f"\nResults: {len(passed_tests)}/{len(results)} tests passed")
    
    if failed_tests:
        print(f"\nFailed tests:")
        for test in failed_tests:
            print(f"  - {test}")
        print(f"\n⚠️  Please review and fix the {len(failed_tests)} failed test(s)")
    else:
        print(f"\n🎉 All Phase 3 tests passed! Ready for production integration.")
    
    # Create detailed report
    report_path = "test_files/phase3_test_report.txt"
    os.makedirs("test_files", exist_ok=True)
    
    with open(report_path, 'w') as f:
        f.write("Phase 3 Testing Report\n")
        f.write("="*50 + "\n")
        f.write(f"Test Date: {datetime.now()}\n")
        f.write(f"Total Tests: {len(results)}\n")
        f.write(f"Passed: {len(passed_tests)}\n")
        f.write(f"Failed: {len(failed_tests)}\n\n")
        
        f.write("Test Results:\n")
        f.write("-" * 20 + "\n")
        for test_name, success in results:
            status = "PASSED" if success else "FAILED"
            f.write(f"{test_name}: {status}\n")
        
        if failed_tests:
            f.write(f"\nFailed Tests:\n")
            f.write("-" * 15 + "\n")
            for test in failed_tests:
                f.write(f"- {test}\n")
    
    print(f"\nDetailed report saved to: {report_path}")

def main():
    """Main test runner"""
    print("PHASE 3 INTEGRATION TESTING")
    print("="*80)
    print("Testing XML generation, PDF processing, and API integration")
    print(f"Started at: {datetime.now()}")
    print()
    
    # Check dependencies first
    if not check_dependencies():
        print("\n❌ Cannot proceed - missing dependencies")
        return False
    
    # Define test scripts and descriptions
    tests = [
        ("test_database.py", "Database Integration Tests"),
        ("test_folder_monitor.py", "Folder Monitoring Tests"),
        ("test_pdf_processing.py", "PDF Processing Tests"),
        ("test_fax_integration.py", "Fax Integration Tests")
    ]
    
    results = []
    
    # Run each test
    for script, description in tests:
        if os.path.exists(script):
            success = run_test_script(script, description)
            results.append((description, success))
        else:
            print(f"\n⚠️  Test script not found: {script}")
            results.append((description, False))
    
    # Create summary
    create_test_summary(results)
    
    # Return overall success
    return all(success for _, success in results)

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
