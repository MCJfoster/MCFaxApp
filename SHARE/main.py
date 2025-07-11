"""
MCFax Application - Main Entry Point
MultiTech FaxFinder FF240.R1 Fax Management Client
"""

import sys
import os
import logging
from pathlib import Path
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt

# Handle both development and PyInstaller environments
if getattr(sys, 'frozen', False):
    # Running from PyInstaller executable
    application_path = os.path.dirname(sys.executable)
    # PyInstaller bundles everything in _internal, so we need to add that to path
    sys.path.insert(0, os.path.join(application_path, '_internal'))
else:
    # Running from source - add src directory to path
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from gui.main_window import MainWindow
from core.settings_portable import get_settings

def setup_logging():
    """Setup application logging"""
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_dir / "mcfax.log"),
            logging.StreamHandler(sys.stdout)
        ]
    )

def main():
    """Main application entry point"""
    # Setup logging
    setup_logging()
    logger = logging.getLogger(__name__)
    logger.info("Starting MCFax Application")
    
    # Create QApplication
    app = QApplication(sys.argv)
    app.setApplicationName("MCFax")
    app.setApplicationVersion("1.0.0")
    app.setOrganizationName("MCFax Solutions")
    
    # Set application style
    app.setStyle('Fusion')
    
    try:
        # Create and show main window
        main_window = MainWindow()
        main_window.show()
        
        logger.info("MCFax Application started successfully")
        
        # Start event loop
        sys.exit(app.exec())
        
    except Exception as e:
        logger.error(f"Failed to start application: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
