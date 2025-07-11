# MCFax Python Source Code - Sharing Package

## Overview
This package contains all the Python source code files that `main.py` uses in the MCFax application. The files have been organized and consolidated for easy sharing and review.

## What's Included
This sharing package contains **26 Python files** from the MCFax application, organized into **6 files**:

### File Structure:
```
SHARE/
├── main.py                 # Main application entry point (unchanged)
├── gui.txt                 # All GUI module files (8 files)
├── core.txt                # All Core module files (4 files)
├── database.txt            # All Database module files (4 files)
├── pdf.txt                 # All PDF module files (6 files)
├── fax.txt                 # All Fax module files (3 files)
└── SHARE_README.md         # This documentation file
```

## How to Read the Consolidated Files

Each `.txt` file contains multiple Python source files from a specific module, formatted with clear delimiters:

### File Format:
```
# --- START OF FILE: filename.py ---

[Complete Python source code for that file]

# --- END OF FILE: filename.py ---


# --- START OF FILE: another_file.py ---

[Complete Python source code for the next file]

# --- END OF FILE: another_file.py ---
```

### Example:
```
# --- START OF FILE: main_window.py ---

"""
Main Window for MCFax Application
Provides the primary interface for fax management
"""

import os
import logging
from pathlib import Path
# ... rest of the Python code ...

# --- END OF FILE: main_window.py ---


# --- START OF FILE: fax_job_window.py ---

"""
Fax Job Window for creating and managing fax jobs
"""

import os
import logging
# ... rest of the Python code ...

# --- END OF FILE: fax_job_window.py ---
```

## Module Breakdown

### 1. main.py
- **Original location:** Root directory
- **Description:** Application entry point that initializes the PyQt6 GUI application
- **Dependencies:** Imports from gui.main_window and core.settings_portable

### 2. gui.txt (8 files)
- **Original location:** `src/gui/` directory
- **Files included:**
  - `main_window.py` - Main application window
  - `fax_job_window.py` - Fax job creation and management
  - `contact_window.py` - Contact management interface
  - `fax_history_window.py` - Fax history viewing
  - `settings_window.py` - Application settings
  - `integrated_pdf_viewer.py` - PDF viewing component
  - `progress_button.py` - Custom progress button widget
  - `__init__.py` - Module initialization

### 3. core.txt (4 files)
- **Original location:** `src/core/` directory
- **Files included:**
  - `settings_portable.py` - Portable settings management
  - `folder_watcher.py` - File system monitoring
  - `settings.py` - Legacy settings management
  - `__init__.py` - Module initialization

### 4. database.txt (4 files)
- **Original location:** `src/database/` directory
- **Files included:**
  - `connection.py` - Database connection management
  - `models.py` - Data models and repositories
  - `schema.py` - Database schema management
  - `__init__.py` - Module initialization

### 5. pdf.txt (6 files)
- **Original location:** `src/pdf/` directory
- **Files included:**
  - `pdf_browser.py` - PDF file browsing and listing
  - `pdf_viewer.py` - PDF viewing functionality
  - `pdf_editor.py` - PDF editing capabilities
  - `pdf_processor.py` - PDF processing operations
  - `cover_page.py` - Cover page generation
  - `__init__.py` - Module initialization

### 6. fax.txt (3 files)
- **Original location:** `src/fax/` directory
- **Files included:**
  - `xml_generator.py` - XML generation for fax jobs
  - `faxfinder_api.py` - FaxFinder API integration
  - `__init__.py` - Module initialization

## How to Extract Individual Files

If you need to extract individual Python files from the consolidated `.txt` files:

1. **Open the relevant `.txt` file** in any text editor
2. **Find the file you need** using the delimiter comments
3. **Copy everything between** the `START OF FILE` and `END OF FILE` markers
4. **Save as a new `.py` file** with the original filename

### Example Extraction:
To extract `main_window.py` from `gui.txt`:
1. Open `gui.txt`
2. Find: `# --- START OF FILE: main_window.py ---`
3. Copy all content until: `# --- END OF FILE: main_window.py ---`
4. Save as `main_window.py`

## Original Project Structure

The files were originally organized in this modular structure:
```
MCFaxApp/
├── main.py
└── src/
    ├── gui/          → consolidated into gui.txt
    ├── core/         → consolidated into core.txt
    ├── database/     → consolidated into database.txt
    ├── pdf/          → consolidated into pdf.txt
    └── fax/          → consolidated into fax.txt
```

## Technology Stack
- **Framework:** PyQt6 (GUI application)
- **Database:** SQLite with ODBC connectivity
- **PDF Processing:** PyPDF2, pdfplumber, reportlab
- **API Integration:** FaxFinder REST API
- **File Monitoring:** Watchdog library

## Notes for Developers
- All 26 files are complete and unmodified source code
- The consolidation is purely for sharing convenience
- Each file maintains its original content and structure
- Import statements reference the original module structure
- The application follows a clean modular architecture with clear separation of concerns

## Generated By
This sharing package was created using the `toshare.bat` script, which automatically:
- Identified all Python dependencies of `main.py`
- Consolidated files by module
- Applied consistent formatting with clear delimiters
- Preserved all original source code content
