"""
PDF Editor Module
Provides MS Paint-style redaction and simple annotation capabilities
"""

import os
import io
import json
import logging
from typing import List, Dict, Any, Tuple, Optional
from pathlib import Path
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QScrollArea, QLabel,
    QPushButton, QSlider, QSpinBox, QCheckBox, QGroupBox,
    QButtonGroup, QToolButton, QColorDialog, QMessageBox,
    QSizePolicy, QFrame
)
from PyQt6.QtCore import Qt, QPoint, QRect, pyqtSignal, QSize
from PyQt6.QtGui import (
    QPainter, QPen, QBrush, QColor, QPixmap, QFont,
    QMouseEvent, QPaintEvent, QIcon
)

try:
    import fitz  # PyMuPDF
    from PIL import Image, ImageDraw
    PYMUPDF_AVAILABLE = True
except ImportError:
    PYMUPDF_AVAILABLE = False

class DrawingCanvas(QLabel):
    """Canvas widget for drawing redactions and annotations on PDF pages"""
    
    def __init__(self, page_image: QPixmap, page_number: int):
        super().__init__()
        self.page_image = page_image
        self.page_number = page_number
        self.logger = logging.getLogger(__name__)
        
        # Drawing state
        self.drawing = False
        self.brush_size = 10
        self.brush_color = QColor(0, 0, 0)  # Black for redaction
        self.current_tool = "redaction"  # redaction, text, rectangle
        
        # Drawing data
        self.brush_strokes = []  # List of stroke paths
        self.annotations = []    # List of text/shape annotations
        self.excluded = False    # Whether this page is excluded
        
        # Undo/redo
        self.history = []
        self.history_index = -1
        
        # Setup canvas
        self.setPixmap(page_image)
        self.setMinimumSize(page_image.size())
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Enable mouse tracking
        self.setMouseTracking(True)
        
        # Create overlay for drawing
        self.overlay = QPixmap(page_image.size())
        self.overlay.fill(Qt.GlobalColor.transparent)
        
        self.update_display()
    
    def set_brush_size(self, size: int):
        """Set brush size for redaction"""
        self.brush_size = size
    
    def set_brush_color(self, color: QColor):
        """Set brush color"""
        self.brush_color = color
    
    def set_tool(self, tool: str):
        """Set current drawing tool"""
        self.current_tool = tool
    
    def set_excluded(self, excluded: bool):
        """Set whether this page is excluded from final PDF"""
        self.excluded = excluded
        self.update_display()
    
    def mousePressEvent(self, event: QMouseEvent):
        """Handle mouse press events"""
        if event.button() == Qt.MouseButton.LeftButton:
            if self.current_tool == "redaction":
                self.drawing = True
                self.current_stroke = [event.position().toPoint()]
                self.save_state()
    
    def mouseMoveEvent(self, event: QMouseEvent):
        """Handle mouse move events"""
        if self.drawing and self.current_tool == "redaction":
            self.current_stroke.append(event.position().toPoint())
            self.draw_current_stroke()
    
    def mouseReleaseEvent(self, event: QMouseEvent):
        """Handle mouse release events"""
        if event.button() == Qt.MouseButton.LeftButton and self.drawing:
            self.drawing = False
            if hasattr(self, 'current_stroke') and len(self.current_stroke) > 1:
                # Save the completed stroke
                stroke_data = {
                    'type': 'redaction',
                    'points': [(p.x(), p.y()) for p in self.current_stroke],
                    'brush_size': self.brush_size,
                    'color': self.brush_color.name()
                }
                self.brush_strokes.append(stroke_data)
                self.redraw_overlay()
    
    def draw_current_stroke(self):
        """Draw the current stroke being drawn"""
        if not hasattr(self, 'current_stroke') or len(self.current_stroke) < 2:
            return
        
        # Create temporary pixmap for current stroke
        temp_overlay = self.overlay.copy()
        painter = QPainter(temp_overlay)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Set up pen for redaction
        pen = QPen(self.brush_color, self.brush_size, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin)
        painter.setPen(pen)
        
        # Draw the stroke
        for i in range(1, len(self.current_stroke)):
            painter.drawLine(self.current_stroke[i-1], self.current_stroke[i])
        
        painter.end()
        
        # Update display
        self.update_display_with_overlay(temp_overlay)
    
    def redraw_overlay(self):
        """Redraw the entire overlay from saved data"""
        self.overlay.fill(Qt.GlobalColor.transparent)
        painter = QPainter(self.overlay)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Draw all brush strokes
        for stroke in self.brush_strokes:
            if stroke['type'] == 'redaction':
                color = QColor(stroke['color'])
                pen = QPen(color, stroke['brush_size'], Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin)
                painter.setPen(pen)
                
                points = [QPoint(x, y) for x, y in stroke['points']]
                for i in range(1, len(points)):
                    painter.drawLine(points[i-1], points[i])
        
        # Draw annotations
        for annotation in self.annotations:
            if annotation['type'] == 'text':
                painter.setPen(QPen(QColor(annotation['color']), 2))
                painter.setFont(QFont(annotation.get('font', 'Arial'), annotation.get('size', 12)))
                painter.drawText(QPoint(annotation['x'], annotation['y']), annotation['text'])
            elif annotation['type'] == 'rectangle':
                painter.setPen(QPen(QColor(annotation['color']), 2))
                painter.drawRect(QRect(annotation['x'], annotation['y'], annotation['width'], annotation['height']))
        
        painter.end()
        self.update_display()
    
    def update_display(self):
        """Update the display with current overlay"""
        self.update_display_with_overlay(self.overlay)
    
    def update_display_with_overlay(self, overlay: QPixmap):
        """Update display with specified overlay"""
        # Combine original image with overlay
        combined = self.page_image.copy()
        painter = QPainter(combined)
        
        # Add exclusion overlay if page is excluded
        if self.excluded:
            painter.fillRect(combined.rect(), QColor(255, 0, 0, 100))  # Semi-transparent red
            painter.setPen(QPen(QColor(255, 0, 0), 3))
            painter.setFont(QFont("Arial", 24, QFont.Weight.Bold))
            painter.drawText(combined.rect(), Qt.AlignmentFlag.AlignCenter, "EXCLUDED")
        
        # Add drawing overlay
        painter.drawPixmap(0, 0, overlay)
        painter.end()
        
        self.setPixmap(combined)
    
    def save_state(self):
        """Save current state for undo functionality"""
        state = {
            'brush_strokes': self.brush_strokes.copy(),
            'annotations': self.annotations.copy(),
            'excluded': self.excluded
        }
        
        # Remove any states after current index (for redo)
        self.history = self.history[:self.history_index + 1]
        self.history.append(state)
        self.history_index += 1
        
        # Limit history size
        if len(self.history) > 50:
            self.history.pop(0)
            self.history_index -= 1
    
    def undo(self):
        """Undo last action"""
        if self.history_index > 0:
            self.history_index -= 1
            state = self.history[self.history_index]
            self.restore_state(state)
    
    def redo(self):
        """Redo last undone action"""
        if self.history_index < len(self.history) - 1:
            self.history_index += 1
            state = self.history[self.history_index]
            self.restore_state(state)
    
    def restore_state(self, state: Dict[str, Any]):
        """Restore canvas to a saved state"""
        self.brush_strokes = state['brush_strokes'].copy()
        self.annotations = state['annotations'].copy()
        self.excluded = state['excluded']
        self.redraw_overlay()
    
    def clear_all(self):
        """Clear all drawings and annotations"""
        self.save_state()
        self.brush_strokes.clear()
        self.annotations.clear()
        self.redraw_overlay()
    
    def add_text_annotation(self, x: int, y: int, text: str, color: str = "#0000FF", font: str = "Arial", size: int = 12):
        """Add a text annotation"""
        self.save_state()
        annotation = {
            'type': 'text',
            'x': x,
            'y': y,
            'text': text,
            'color': color,
            'font': font,
            'size': size
        }
        self.annotations.append(annotation)
        self.redraw_overlay()
    
    def add_rectangle_annotation(self, x: int, y: int, width: int, height: int, color: str = "#0000FF"):
        """Add a rectangle annotation"""
        self.save_state()
        annotation = {
            'type': 'rectangle',
            'x': x,
            'y': y,
            'width': width,
            'height': height,
            'color': color
        }
        self.annotations.append(annotation)
        self.redraw_overlay()
    
    def get_edit_data(self) -> Dict[str, Any]:
        """Get all edit data for this page"""
        return {
            'page_number': self.page_number,
            'brush_strokes': self.brush_strokes,
            'annotations': self.annotations,
            'excluded': self.excluded
        }
    
    def load_edit_data(self, data: Dict[str, Any]):
        """Load edit data for this page"""
        self.brush_strokes = data.get('brush_strokes', [])
        self.annotations = data.get('annotations', [])
        self.excluded = data.get('excluded', False)
        self.redraw_overlay()

class PDFEditor(QWidget):
    """Main PDF editor widget with tools and page navigation"""
    
    pages_changed = pyqtSignal()  # Emitted when page exclusions change
    
    def __init__(self, pdf_path: str, parent=None):
        super().__init__(parent)
        self.pdf_path = pdf_path
        self.logger = logging.getLogger(__name__)
        
        # Check dependencies
        if not PYMUPDF_AVAILABLE:
            raise ImportError("PyMuPDF is required for PDF editing. Please install it with: pip install PyMuPDF")
        
        # Data
        self.pages = []  # List of DrawingCanvas widgets
        self.current_page = 0
        self.page_images = []  # Original page images
        
        # Setup UI
        self.setup_ui()
        self.load_pdf()
    
    def setup_ui(self):
        """Setup the user interface"""
        layout = QVBoxLayout(self)
        
        # Toolbar
        toolbar = self.create_toolbar()
        layout.addWidget(toolbar)
        
        # Main content area
        content_layout = QHBoxLayout()
        
        # Left panel - Tools
        tools_panel = self.create_tools_panel()
        content_layout.addWidget(tools_panel)
        
        # Center - PDF viewer
        viewer_panel = self.create_viewer_panel()
        content_layout.addWidget(viewer_panel, 1)  # Give it more space
        
        layout.addLayout(content_layout)
        
        # Navigation
        nav_panel = self.create_navigation_panel()
        layout.addWidget(nav_panel)
    
    def create_toolbar(self):
        """Create the main toolbar"""
        toolbar = QFrame()
        toolbar.setFrameStyle(QFrame.Shape.StyledPanel)
        layout = QHBoxLayout(toolbar)
        
        # File operations
        save_btn = QPushButton("Save Edits")
        save_btn.clicked.connect(self.save_edits)
        layout.addWidget(save_btn)
        
        load_btn = QPushButton("Load Edits")
        load_btn.clicked.connect(self.load_edits)
        layout.addWidget(load_btn)
        
        layout.addWidget(QFrame())  # Separator
        
        # Undo/Redo
        undo_btn = QPushButton("Undo")
        undo_btn.setShortcut("Ctrl+Z")
        undo_btn.clicked.connect(self.undo)
        layout.addWidget(undo_btn)
        
        redo_btn = QPushButton("Redo")
        redo_btn.setShortcut("Ctrl+Y")
        redo_btn.clicked.connect(self.redo)
        layout.addWidget(redo_btn)
        
        layout.addWidget(QFrame())  # Separator
        
        # Clear all
        clear_btn = QPushButton("Clear Page")
        clear_btn.clicked.connect(self.clear_current_page)
        layout.addWidget(clear_btn)
        
        layout.addStretch()
        
        return toolbar
    
    def create_tools_panel(self):
        """Create the tools panel"""
        panel = QGroupBox("Tools")
        layout = QVBoxLayout(panel)
        
        # Tool selection
        tool_group = QGroupBox("Drawing Tool")
        tool_layout = QVBoxLayout(tool_group)
        
        self.tool_buttons = QButtonGroup()
        
        redaction_btn = QPushButton("Redaction Brush")
        redaction_btn.setCheckable(True)
        redaction_btn.setChecked(True)
        redaction_btn.clicked.connect(lambda: self.set_tool("redaction"))
        self.tool_buttons.addButton(redaction_btn, 0)
        tool_layout.addWidget(redaction_btn)
        
        text_btn = QPushButton("Text Annotation")
        text_btn.setCheckable(True)
        text_btn.clicked.connect(lambda: self.set_tool("text"))
        self.tool_buttons.addButton(text_btn, 1)
        tool_layout.addWidget(text_btn)
        
        rect_btn = QPushButton("Rectangle")
        rect_btn.setCheckable(True)
        rect_btn.clicked.connect(lambda: self.set_tool("rectangle"))
        self.tool_buttons.addButton(rect_btn, 2)
        tool_layout.addWidget(rect_btn)
        
        layout.addWidget(tool_group)
        
        # Brush settings
        brush_group = QGroupBox("Brush Settings")
        brush_layout = QVBoxLayout(brush_group)
        
        # Brush size
        brush_layout.addWidget(QLabel("Brush Size:"))
        self.brush_size_slider = QSlider(Qt.Orientation.Horizontal)
        self.brush_size_slider.setRange(1, 50)
        self.brush_size_slider.setValue(10)
        self.brush_size_slider.valueChanged.connect(self.update_brush_size)
        brush_layout.addWidget(self.brush_size_slider)
        
        self.brush_size_label = QLabel("10 px")
        brush_layout.addWidget(self.brush_size_label)
        
        # Color selection
        self.color_btn = QPushButton("Black")
        self.color_btn.setStyleSheet("QPushButton { background-color: black; color: white; }")
        self.color_btn.clicked.connect(self.choose_color)
        brush_layout.addWidget(self.color_btn)
        
        layout.addWidget(brush_group)
        
        # Page settings
        page_group = QGroupBox("Page Settings")
        page_layout = QVBoxLayout(page_group)
        
        self.exclude_checkbox = QCheckBox("Exclude this page")
        self.exclude_checkbox.toggled.connect(self.toggle_page_exclusion)
        page_layout.addWidget(self.exclude_checkbox)
        
        layout.addWidget(page_group)
        
        layout.addStretch()
        
        return panel
    
    def create_viewer_panel(self):
        """Create the PDF viewer panel"""
        panel = QGroupBox("PDF Viewer")
        layout = QVBoxLayout(panel)
        
        # Scroll area for PDF page
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.scroll_area)
        
        return panel
    
    def create_navigation_panel(self):
        """Create the navigation panel"""
        panel = QFrame()
        panel.setFrameStyle(QFrame.Shape.StyledPanel)
        layout = QHBoxLayout(panel)
        
        # Previous page
        prev_btn = QPushButton("◀ Previous")
        prev_btn.clicked.connect(self.previous_page)
        layout.addWidget(prev_btn)
        
        # Page info
        self.page_label = QLabel("Page 1 of 1")
        self.page_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.page_label)
        
        # Next page
        next_btn = QPushButton("Next ▶")
        next_btn.clicked.connect(self.next_page)
        layout.addWidget(next_btn)
        
        layout.addStretch()
        
        # Page exclusion summary
        self.exclusion_label = QLabel("0 pages excluded")
        layout.addWidget(self.exclusion_label)
        
        return panel
    
    def load_pdf(self):
        """Load PDF and convert pages to images using PyMuPDF"""
        try:
            self.logger.info(f"Loading PDF: {self.pdf_path}")
            
            # Check if file exists
            if not os.path.exists(self.pdf_path):
                raise FileNotFoundError(f"PDF file not found: {self.pdf_path}")
            
            # Open PDF with PyMuPDF
            pdf_document = fitz.open(self.pdf_path)
            
            self.page_images = []
            self.pages = []
            
            for page_num in range(len(pdf_document)):
                # Get page
                page = pdf_document[page_num]
                
                # Render page to image (150 DPI)
                mat = fitz.Matrix(150/72, 150/72)  # 150 DPI scaling
                pix = page.get_pixmap(matrix=mat)
                
                # Convert to PIL Image
                img_data = pix.tobytes("png")
                pil_image = Image.open(io.BytesIO(img_data))
                
                # Convert PIL image to QPixmap
                temp_path = f"temp_page_{page_num}.png"
                pil_image.save(temp_path, "PNG")
                
                pixmap = QPixmap(temp_path)
                self.page_images.append(pixmap)
                
                # Create drawing canvas
                canvas = DrawingCanvas(pixmap, page_num)
                self.pages.append(canvas)
                
                # Clean up temp file
                os.remove(temp_path)
            
            # Close PDF document
            pdf_document.close()
            
            # Show first page
            if self.pages:
                self.show_page(0)
            
            self.logger.info(f"Loaded {len(self.pages)} pages")
            
        except Exception as e:
            self.logger.error(f"Error loading PDF: {e}")
            raise Exception(f"Failed to load PDF: {str(e)}")
    
    def show_page(self, page_num: int):
        """Show specified page"""
        if 0 <= page_num < len(self.pages):
            self.current_page = page_num
            canvas = self.pages[page_num]
            
            # Update scroll area
            self.scroll_area.setWidget(canvas)
            
            # Update UI
            self.page_label.setText(f"Page {page_num + 1} of {len(self.pages)}")
            self.exclude_checkbox.setChecked(canvas.excluded)
            
            # Update tool settings
            canvas.set_brush_size(self.brush_size_slider.value())
            canvas.set_tool(self.get_current_tool())
            
            self.update_exclusion_summary()
    
    def previous_page(self):
        """Go to previous page"""
        if self.current_page > 0:
            self.show_page(self.current_page - 1)
    
    def next_page(self):
        """Go to next page"""
        if self.current_page < len(self.pages) - 1:
            self.show_page(self.current_page + 1)
    
    def set_tool(self, tool: str):
        """Set current drawing tool"""
        if self.pages:
            self.pages[self.current_page].set_tool(tool)
    
    def get_current_tool(self) -> str:
        """Get current tool name"""
        checked_id = self.tool_buttons.checkedId()
        tools = ["redaction", "text", "rectangle"]
        return tools[checked_id] if 0 <= checked_id < len(tools) else "redaction"
    
    def update_brush_size(self, size: int):
        """Update brush size"""
        self.brush_size_label.setText(f"{size} px")
        if self.pages:
            self.pages[self.current_page].set_brush_size(size)
    
    def choose_color(self):
        """Open color chooser dialog"""
        color = QColorDialog.getColor(QColor(0, 0, 0), self, "Choose Color")
        if color.isValid():
            self.color_btn.setText(color.name())
            self.color_btn.setStyleSheet(f"QPushButton {{ background-color: {color.name()}; color: white; }}")
            if self.pages:
                self.pages[self.current_page].set_brush_color(color)
    
    def toggle_page_exclusion(self, excluded: bool):
        """Toggle page exclusion"""
        if self.pages:
            self.pages[self.current_page].set_excluded(excluded)
            self.update_exclusion_summary()
            self.pages_changed.emit()
    
    def update_exclusion_summary(self):
        """Update exclusion summary label"""
        excluded_count = sum(1 for page in self.pages if page.excluded)
        self.exclusion_label.setText(f"{excluded_count} pages excluded")
    
    def undo(self):
        """Undo last action on current page"""
        if self.pages:
            self.pages[self.current_page].undo()
    
    def redo(self):
        """Redo last action on current page"""
        if self.pages:
            self.pages[self.current_page].redo()
    
    def clear_current_page(self):
        """Clear all edits on current page"""
        if self.pages:
            reply = QMessageBox.question(
                self,
                "Clear Page",
                "Are you sure you want to clear all edits on this page?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.Yes:
                self.pages[self.current_page].clear_all()
    
    def get_all_edits(self) -> Dict[str, Any]:
        """Get all edits for all pages"""
        return {
            'pdf_path': self.pdf_path,
            'pages': [page.get_edit_data() for page in self.pages]
        }
    
    def get_excluded_pages(self) -> List[int]:
        """Get list of excluded page numbers (0-based)"""
        return [i for i, page in enumerate(self.pages) if page.excluded]
    
    def save_edits(self):
        """Save edits to file"""
        from PyQt6.QtWidgets import QFileDialog
        
        filename = f"{Path(self.pdf_path).stem}_edits.json"
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save PDF Edits",
            filename,
            "JSON Files (*.json);;All Files (*)"
        )
        
        if file_path:
            try:
                edits = self.get_all_edits()
                with open(file_path, 'w') as f:
                    json.dump(edits, f, indent=2)
                
                QMessageBox.information(self, "Saved", f"Edits saved to:\n{file_path}")
                
            except Exception as e:
                self.logger.error(f"Error saving edits: {e}")
                QMessageBox.critical(self, "Error", f"Failed to save edits:\n{str(e)}")
    
    def load_edits(self):
        """Load edits from file"""
        from PyQt6.QtWidgets import QFileDialog
        
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Load PDF Edits",
            "",
            "JSON Files (*.json);;All Files (*)"
        )
        
        if file_path:
            try:
                with open(file_path, 'r') as f:
                    edits = json.load(f)
                
                # Load edits for each page
                for page_data in edits.get('pages', []):
                    page_num = page_data.get('page_number', 0)
                    if 0 <= page_num < len(self.pages):
                        self.pages[page_num].load_edit_data(page_data)
                
                # Refresh current page
                self.show_page(self.current_page)
                
                QMessageBox.information(self, "Loaded", f"Edits loaded from:\n{file_path}")
                
            except Exception as e:
                self.logger.error(f"Error loading edits: {e}")
                QMessageBox.critical(self, "Error", f"Failed to load edits:\n{str(e)}")
