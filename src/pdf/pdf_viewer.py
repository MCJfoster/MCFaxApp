"""
PDF Viewer Module
Enhanced PDF viewing with editing capabilities for the MCFax application
"""

import os
import logging
from pathlib import Path
from typing import List, Optional, Dict, Any
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QScrollArea, QMessageBox, QGroupBox, QSlider, QSpinBox,
    QTabWidget, QDialog, QDialogButtonBox
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QPixmap, QFont

try:
    from .pdf_editor import PDFEditor, PYMUPDF_AVAILABLE
    EDITOR_AVAILABLE = True
except ImportError:
    EDITOR_AVAILABLE = False
    PYMUPDF_AVAILABLE = False

class PDFViewerDialog(QDialog):
    """Dialog for viewing and editing PDFs"""
    
    edits_applied = pyqtSignal(dict)  # Signal emitted when edits are applied
    
    def __init__(self, pdf_path: str, parent=None):
        super().__init__(parent)
        self.pdf_path = pdf_path
        self.logger = logging.getLogger(__name__)
        
        self.setWindowTitle(f"PDF Viewer - {Path(pdf_path).name}")
        self.setGeometry(100, 100, 1400, 900)
        
        # Data
        self.excluded_pages = []
        self.edit_data = {}
        
        self.setup_ui()
    
    def setup_ui(self):
        """Setup the user interface"""
        layout = QVBoxLayout(self)
        
        # Check if editing is available
        if not EDITOR_AVAILABLE or not PYMUPDF_AVAILABLE:
            # Show simple viewer
            self.create_simple_viewer()
        else:
            # Show full editor
            self.create_editor_interface()
        
        # Button box
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.accept_changes)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
    
    def create_simple_viewer(self):
        """Create simple PDF viewer when editor is not available"""
        layout = self.layout()
        
        # Info message
        info_label = QLabel(
            "PDF Editor Dependencies Missing\n\n"
            "To enable PDF editing and viewing, please install:\n"
            "• PyMuPDF (required for PDF processing)\n"
            "• Pillow ✓ (installed)\n\n"
            "Install with:\n"
            "pip install PyMuPDF\n\n"
            "PyMuPDF provides complete PDF functionality\n"
            "without requiring external binaries!\n\n"
            f"Current PDF: {Path(self.pdf_path).name}"
        )
        info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        info_label.setStyleSheet("""
            QLabel {
                border: 2px dashed #ccc;
                padding: 40px;
                font-size: 14px;
                color: #666;
                background-color: #f9f9f9;
            }
        """)
        layout.addWidget(info_label)
        
        # Basic info
        try:
            from pdf.pdf_processor import PDFProcessor
            processor = PDFProcessor()
            pdf_info = processor.get_pdf_info(self.pdf_path)
            
            info_text = f"PDF Information:\n"
            info_text += f"File: {pdf_info.get('file_name', 'Unknown')}\n"
            info_text += f"Pages: {pdf_info.get('page_count', 'Unknown')}\n"
            info_text += f"Size: {pdf_info.get('size_mb', 'Unknown')} MB\n"
            
            info_detail = QLabel(info_text)
            info_detail.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(info_detail)
            
        except Exception as e:
            self.logger.error(f"Error getting PDF info: {e}")
    
    def create_editor_interface(self):
        """Create full PDF editor interface"""
        layout = self.layout()
        
        try:
            # Create PDF editor
            self.pdf_editor = PDFEditor(self.pdf_path, self)
            self.pdf_editor.pages_changed.connect(self.on_pages_changed)
            layout.addWidget(self.pdf_editor)
            
        except Exception as e:
            self.logger.error(f"Error creating PDF editor: {e}")
            # Fall back to simple viewer
            error_label = QLabel(f"Error loading PDF editor:\n{str(e)}")
            error_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            error_label.setStyleSheet("QLabel { color: red; padding: 20px; }")
            layout.addWidget(error_label)
    
    def on_pages_changed(self):
        """Handle page changes from editor"""
        if hasattr(self, 'pdf_editor'):
            self.excluded_pages = self.pdf_editor.get_excluded_pages()
    
    def accept_changes(self):
        """Accept changes and emit signal"""
        if hasattr(self, 'pdf_editor'):
            # Get all edit data
            self.edit_data = self.pdf_editor.get_all_edits()
            self.excluded_pages = self.pdf_editor.get_excluded_pages()
            
            # Emit signal with edit data
            self.edits_applied.emit({
                'excluded_pages': self.excluded_pages,
                'edit_data': self.edit_data
            })
        
        self.accept()
    
    def get_excluded_pages(self) -> List[int]:
        """Get list of excluded page numbers"""
        return self.excluded_pages
    
    def get_edit_data(self) -> Dict[str, Any]:
        """Get all edit data"""
        return self.edit_data

class PDFViewer(QWidget):
    """
    Enhanced PDF viewer widget with editing capabilities
    """
    
    pdf_edited = pyqtSignal(dict)  # Signal emitted when PDF is edited
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.logger = logging.getLogger(__name__)
        self.current_pdf = None
        self.excluded_pages = []
        self.edit_data = {}
        self.setup_ui()
    
    def setup_ui(self):
        """Setup the viewer UI"""
        layout = QVBoxLayout(self)
        
        # Header
        header = QGroupBox("PDF Viewer")
        header_layout = QVBoxLayout(header)
        
        # File info
        self.file_label = QLabel("No PDF loaded")
        self.file_label.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        header_layout.addWidget(self.file_label)
        
        # Status info
        self.status_label = QLabel("Ready")
        self.status_label.setStyleSheet("QLabel { color: #666; }")
        header_layout.addWidget(self.status_label)
        
        layout.addWidget(header)
        
        # Main content area
        content = QGroupBox("Preview")
        content_layout = QVBoxLayout(content)
        
        # Preview area
        self.preview_area = QLabel("No PDF loaded")
        self.preview_area.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview_area.setMinimumHeight(200)
        self.preview_area.setStyleSheet("""
            QLabel {
                border: 2px dashed #ccc;
                padding: 20px;
                font-size: 14px;
                color: #666;
                background-color: #f9f9f9;
            }
        """)
        content_layout.addWidget(self.preview_area)
        
        # Action buttons
        button_layout = QHBoxLayout()
        
        self.view_edit_btn = QPushButton("View & Edit PDF")
        self.view_edit_btn.setEnabled(False)
        self.view_edit_btn.clicked.connect(self.open_editor)
        self.view_edit_btn.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: none;
                padding: 8px 16px;
                font-weight: bold;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
            QPushButton:disabled {
                background-color: #cccccc;
                color: #666666;
            }
        """)
        button_layout.addWidget(self.view_edit_btn)
        
        self.clear_edits_btn = QPushButton("Clear Edits")
        self.clear_edits_btn.setEnabled(False)
        self.clear_edits_btn.clicked.connect(self.clear_edits)
        button_layout.addWidget(self.clear_edits_btn)
        
        button_layout.addStretch()
        
        content_layout.addLayout(button_layout)
        layout.addWidget(content)
        
        # Edit summary
        self.summary_group = QGroupBox("Edit Summary")
        summary_layout = QVBoxLayout(self.summary_group)
        
        self.summary_label = QLabel("No edits applied")
        self.summary_label.setStyleSheet("QLabel { color: #666; }")
        summary_layout.addWidget(self.summary_label)
        
        layout.addWidget(self.summary_group)
        self.summary_group.setVisible(False)
    
    def load_pdf(self, pdf_path: str):
        """Load a PDF file for viewing"""
        try:
            self.current_pdf = pdf_path
            file_name = Path(pdf_path).name
            
            # Update UI
            self.file_label.setText(f"File: {file_name}")
            
            # Get PDF info
            try:
                from pdf.pdf_processor import PDFProcessor
                processor = PDFProcessor()
                pdf_info = processor.get_pdf_info(pdf_path)
                
                pages = pdf_info.get('page_count', 'Unknown')
                size = pdf_info.get('size_mb', 'Unknown')
                
                self.preview_area.setText(
                    f"PDF Loaded: {file_name}\n\n"
                    f"Pages: {pages}\n"
                    f"Size: {size} MB\n\n"
                    f"Click 'View & Edit PDF' to open the editor"
                )
                
                self.status_label.setText(f"Loaded • {pages} pages • {size} MB")
                
            except Exception as e:
                self.logger.error(f"Error getting PDF info: {e}")
                self.preview_area.setText(f"PDF Loaded: {file_name}\n\nClick 'View & Edit PDF' to open")
                self.status_label.setText("Loaded")
            
            # Enable editing button
            self.view_edit_btn.setEnabled(True)
            
            # Clear previous edits
            self.clear_edits()
            
        except Exception as e:
            self.logger.error(f"Error loading PDF: {e}")
            QMessageBox.critical(self, "Error", f"Failed to load PDF: {str(e)}")
    
    def open_editor(self):
        """Open the PDF editor dialog"""
        if not self.current_pdf:
            return
        
        try:
            # Create and show editor dialog
            editor_dialog = PDFViewerDialog(self.current_pdf, self)
            editor_dialog.edits_applied.connect(self.on_edits_applied)
            
            if editor_dialog.exec() == QDialog.DialogCode.Accepted:
                self.logger.info("PDF editor closed with changes accepted")
            else:
                self.logger.info("PDF editor closed without changes")
                
        except Exception as e:
            self.logger.error(f"Error opening PDF editor: {e}")
            QMessageBox.critical(self, "Error", f"Failed to open PDF editor: {str(e)}")
    
    def on_edits_applied(self, edit_info: Dict[str, Any]):
        """Handle edits applied from editor"""
        self.excluded_pages = edit_info.get('excluded_pages', [])
        self.edit_data = edit_info.get('edit_data', {})
        
        # Update UI
        self.update_edit_summary()
        self.clear_edits_btn.setEnabled(True)
        
        # Emit signal
        self.pdf_edited.emit(edit_info)
    
    def update_edit_summary(self):
        """Update the edit summary display"""
        if not self.excluded_pages and not self.edit_data:
            self.summary_group.setVisible(False)
            return
        
        summary_parts = []
        
        if self.excluded_pages:
            excluded_count = len(self.excluded_pages)
            summary_parts.append(f"• {excluded_count} page(s) excluded")
        
        if self.edit_data and 'pages' in self.edit_data:
            edited_pages = 0
            for page_data in self.edit_data['pages']:
                if (page_data.get('brush_strokes') or 
                    page_data.get('annotations')):
                    edited_pages += 1
            
            if edited_pages > 0:
                summary_parts.append(f"• {edited_pages} page(s) have edits")
        
        if summary_parts:
            self.summary_label.setText("\n".join(summary_parts))
            self.summary_group.setVisible(True)
        else:
            self.summary_group.setVisible(False)
    
    def clear_edits(self):
        """Clear all edits"""
        self.excluded_pages = []
        self.edit_data = {}
        self.summary_group.setVisible(False)
        self.clear_edits_btn.setEnabled(False)
        
        # Update status
        if self.current_pdf:
            file_name = Path(self.current_pdf).name
            self.preview_area.setText(
                f"PDF Loaded: {file_name}\n\n"
                f"Click 'View & Edit PDF' to open the editor\n\n"
                f"All edits have been cleared"
            )
    
    def clear(self):
        """Clear the viewer"""
        self.current_pdf = None
        self.excluded_pages = []
        self.edit_data = {}
        
        self.file_label.setText("No PDF loaded")
        self.status_label.setText("Ready")
        self.preview_area.setText("No PDF loaded")
        self.view_edit_btn.setEnabled(False)
        self.clear_edits_btn.setEnabled(False)
        self.summary_group.setVisible(False)
    
    def get_excluded_pages(self) -> List[int]:
        """Get list of excluded page numbers (0-based)"""
        return self.excluded_pages.copy()
    
    def get_edit_data(self) -> Dict[str, Any]:
        """Get all edit data"""
        return self.edit_data.copy()
    
    def has_edits(self) -> bool:
        """Check if there are any edits applied"""
        return bool(self.excluded_pages or self.edit_data)

# Utility function for standalone PDF viewing
def view_pdf(pdf_path: str, parent=None) -> Dict[str, Any]:
    """
    Open a PDF in the viewer dialog and return edit results
    
    Args:
        pdf_path: Path to PDF file
        parent: Parent widget
        
    Returns:
        dict: Edit results with 'excluded_pages' and 'edit_data' keys
    """
    dialog = PDFViewerDialog(pdf_path, parent)
    
    if dialog.exec() == QDialog.DialogCode.Accepted:
        return {
            'excluded_pages': dialog.get_excluded_pages(),
            'edit_data': dialog.get_edit_data()
        }
    else:
        return {
            'excluded_pages': [],
            'edit_data': {}
        }
