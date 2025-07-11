"""
Integrated PDF Viewer Widget
Displays PDF content directly in the widget with editing capabilities
"""

import logging
from pathlib import Path
from typing import Optional, List, Dict, Any
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QScrollArea
)
from PyQt6.QtCore import Qt, pyqtSignal, QPoint, QRect
from PyQt6.QtGui import (
    QPixmap, QPainter, QColor, QPen, QBrush, QFont,
    QMouseEvent, QPaintEvent
)

try:
    import fitz  # PyMuPDF
    PYMUPDF_AVAILABLE = True
except ImportError:
    PYMUPDF_AVAILABLE = False

class DrawingCanvas(QLabel):
    """Canvas widget for drawing redactions and annotations on PDF pages"""
    
    def __init__(self, page_image: QPixmap, page_number: int, pdf_page_size: tuple = None):
        super().__init__()
        self.page_image = page_image
        self.page_number = page_number
        self.logger = logging.getLogger(__name__)
        
        # Store original PDF page size for coordinate transformation
        self.pdf_page_size = pdf_page_size or (page_image.width(), page_image.height())
        self.current_zoom_level = 1.0  # Track current zoom level
        
        # Drawing state
        self.drawing = False
        self.brush_size = 10
        self.brush_color = QColor(0, 0, 0)  # Black for redaction
        self.current_tool = "redaction"  # redaction, text, rectangle
        
        # Drawing data - coordinates stored in PDF space (not display space)
        self.brush_strokes = []  # List of stroke paths in PDF coordinates
        self.annotations = []    # List of text/shape annotations in PDF coordinates
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
            if self.current_tool in ["redaction", "highlight"]:
                self.drawing = True
                # Convert display coordinates to PDF coordinates
                pdf_point = self.display_to_pdf_coordinates(event.position().toPoint())
                self.current_stroke = [pdf_point]
                self.save_state()
            elif self.current_tool == "text":
                # Handle text placement - convert to PDF coordinates
                pdf_point = self.display_to_pdf_coordinates(event.position().toPoint())
                self.handle_text_placement(pdf_point)
    
    def mouseMoveEvent(self, event: QMouseEvent):
        """Handle mouse move events"""
        if self.drawing and self.current_tool in ["redaction", "highlight"]:
            # Convert display coordinates to PDF coordinates
            pdf_point = self.display_to_pdf_coordinates(event.position().toPoint())
            self.current_stroke.append(pdf_point)
            self.draw_current_stroke()
    
    def mouseReleaseEvent(self, event: QMouseEvent):
        """Handle mouse release events"""
        if event.button() == Qt.MouseButton.LeftButton and self.drawing:
            self.drawing = False
            if hasattr(self, 'current_stroke') and len(self.current_stroke) > 1:
                # Save the completed stroke in PDF coordinates
                stroke_data = {
                    'type': self.current_tool,  # Use current tool (redaction or highlight)
                    'points': [(p.x(), p.y()) if hasattr(p, 'x') else p for p in self.current_stroke],
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
        
        # Set up pen for redaction - scale brush size for current zoom
        display_brush_size = max(1, int(self.brush_size * self.current_zoom_level))
        pen = QPen(self.brush_color, display_brush_size, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin)
        painter.setPen(pen)
        
        # Convert PDF coordinates to display coordinates and draw
        display_points = []
        for point in self.current_stroke:
            if hasattr(point, 'x'):
                display_point = self.pdf_to_display_coordinates(point)
            else:
                # Handle tuple format
                display_point = self.pdf_to_display_coordinates(QPoint(point[0], point[1]))
            display_points.append(display_point)
        
        # Draw the stroke
        for i in range(1, len(display_points)):
            painter.drawLine(display_points[i-1], display_points[i])
        
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
            if stroke['type'] in ['redaction', 'highlight']:
                color = QColor(stroke['color'])
                
                # Scale brush size for current zoom level
                display_brush_size = max(1, int(stroke['brush_size'] * self.current_zoom_level))
                
                # Set different drawing styles for different tools
                if stroke['type'] == 'highlight':
                    # Semi-transparent yellow for highlights
                    color.setAlpha(128)  # 50% transparency
                    pen = QPen(color, display_brush_size, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin)
                else:  # redaction
                    # Solid color for redaction
                    pen = QPen(color, display_brush_size, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin)
                
                painter.setPen(pen)
                
                # Convert PDF coordinates to display coordinates
                display_points = []
                for x, y in stroke['points']:
                    display_point = self.pdf_to_display_coordinates(QPoint(x, y))
                    display_points.append(display_point)
                
                # Draw the stroke
                for i in range(1, len(display_points)):
                    painter.drawLine(display_points[i-1], display_points[i])
        
        # Draw annotations
        for annotation in self.annotations:
            if annotation['type'] == 'text':
                # Convert PDF coordinates to display coordinates
                display_point = self.pdf_to_display_coordinates(QPoint(annotation['x'], annotation['y']))
                display_font_size = max(8, int(annotation.get('size', 12) * self.current_zoom_level))
                
                painter.setPen(QPen(QColor(annotation['color']), 2))
                painter.setFont(QFont(annotation.get('font', 'Arial'), display_font_size))
                painter.drawText(display_point, annotation['text'])
            elif annotation['type'] == 'rectangle':
                # Convert PDF coordinates to display coordinates
                top_left = self.pdf_to_display_coordinates(QPoint(annotation['x'], annotation['y']))
                width = int(annotation['width'] * self.current_zoom_level)
                height = int(annotation['height'] * self.current_zoom_level)
                
                painter.setPen(QPen(QColor(annotation['color']), 2))
                painter.drawRect(QRect(top_left.x(), top_left.y(), width, height))
        
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
    
    def handle_text_placement(self, pdf_position: QPoint):
        """Handle text placement when in text mode"""
        from PyQt6.QtWidgets import QInputDialog
        
        # Get text from user
        text, ok = QInputDialog.getText(self, 'Add Text', 'Enter text to add:')
        if ok and text.strip():
            # Position is already in PDF coordinates
            self.add_text_annotation(pdf_position.x(), pdf_position.y(), text.strip())
    
    def add_text_annotation(self, x: int, y: int, text: str, color: str = "#0000FF", font: str = "Arial", size: int = 12):
        """Add a text annotation - coordinates should be in PDF space"""
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
    
    def display_to_pdf_coordinates(self, display_point: QPoint) -> QPoint:
        """Convert display coordinates to PDF coordinates"""
        # Calculate the scale factor from display to PDF
        display_width = self.page_image.width()
        display_height = self.page_image.height()
        pdf_width, pdf_height = self.pdf_page_size
        
        # Calculate scale factors
        scale_x = pdf_width / display_width if display_width > 0 else 1.0
        scale_y = pdf_height / display_height if display_height > 0 else 1.0
        
        # Convert coordinates
        pdf_x = int(display_point.x() * scale_x)
        pdf_y = int(display_point.y() * scale_y)
        
        return QPoint(pdf_x, pdf_y)
    
    def pdf_to_display_coordinates(self, pdf_point: QPoint) -> QPoint:
        """Convert PDF coordinates to display coordinates"""
        # Calculate the scale factor from PDF to display
        display_width = self.page_image.width()
        display_height = self.page_image.height()
        pdf_width, pdf_height = self.pdf_page_size
        
        # Calculate scale factors
        scale_x = display_width / pdf_width if pdf_width > 0 else 1.0
        scale_y = display_height / pdf_height if pdf_height > 0 else 1.0
        
        # Convert coordinates
        display_x = int(pdf_point.x() * scale_x)
        display_y = int(pdf_point.y() * scale_y)
        
        return QPoint(display_x, display_y)
    
    def set_zoom_level(self, zoom_level: float):
        """Update the zoom level for coordinate transformations"""
        self.current_zoom_level = zoom_level
        # Redraw overlay with new zoom level
        self.redraw_overlay()

class IntegratedPDFViewer(QWidget):
    """
    Integrated PDF viewer widget that displays PDF content directly
    """
    
    page_changed = pyqtSignal(int)  # Emitted when page changes
    zoom_changed = pyqtSignal(float)  # Emitted when zoom changes
    
    def __init__(self, pdf_path: str, parent=None):
        super().__init__(parent)
        self.logger = logging.getLogger(__name__)
        
        self.pdf_path = pdf_path
        self.pdf_document = None
        self.current_page = 0
        self.edit_mode = None
        self.excluded_pages = set()  # Set of excluded page numbers (0-based)
        
        # Load zoom level from settings
        try:
            from core.settings import get_settings
            settings = get_settings()
            self.zoom_level = settings.get("pdf_settings.default_zoom_level", 1.0)
        except Exception as e:
            self.logger.warning(f"Could not load zoom setting: {e}")
            self.zoom_level = 1.0
        
        # Drawing state
        self.brush_size = 10
        self.brush_color = QColor(0, 0, 0)  # Black for redaction
        
        # Page canvases
        self.page_canvases = []  # List of DrawingCanvas widgets
        self.page_images = []    # Original page images
        
        self.setup_ui()
        self.load_pdf()
    
    def setup_ui(self):
        """Setup the viewer UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Create scroll area for PDF content
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Create container widget to hold all canvases
        self.canvas_container = QWidget()
        self.canvas_container_layout = QVBoxLayout(self.canvas_container)
        self.canvas_container_layout.setContentsMargins(0, 0, 0, 0)
        
        # PDF display label for errors
        self.pdf_label = QLabel()
        self.pdf_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.pdf_label.setStyleSheet("""
            QLabel {
                background-color: white;
                border: 1px solid #ccc;
                margin: 10px;
            }
        """)
        self.pdf_label.hide()  # Hidden by default
        self.canvas_container_layout.addWidget(self.pdf_label)
        
        # Set the container as the scroll area widget once
        self.scroll_area.setWidget(self.canvas_container)
        layout.addWidget(self.scroll_area)
    
    def load_pdf(self):
        """Load the PDF file and create drawing canvases"""
        if not PYMUPDF_AVAILABLE:
            self.show_error("PyMuPDF not available. Please install with: pip install PyMuPDF")
            return
        
        try:
            self.pdf_document = fitz.open(self.pdf_path)
            
            self.page_images = []
            self.page_canvases = []
            
            # Load all pages and create canvases
            for page_num in range(len(self.pdf_document)):
                # Get page
                page = self.pdf_document[page_num]
                
                # Render page to image with saved zoom level
                mat = fitz.Matrix(self.zoom_level * 150/72, self.zoom_level * 150/72)  # Apply saved zoom
                pix = page.get_pixmap(matrix=mat)
                
                # Convert to QPixmap
                img_data = pix.tobytes("ppm")
                qpixmap = QPixmap()
                qpixmap.loadFromData(img_data)
                
                self.page_images.append(qpixmap)
                
                # Get original PDF page size (in points)
                pdf_rect = page.rect
                pdf_page_size = (int(pdf_rect.width), int(pdf_rect.height))
                
                # Create drawing canvas with PDF page size
                canvas = DrawingCanvas(qpixmap, page_num, pdf_page_size)
                canvas.set_brush_size(self.brush_size)
                canvas.set_brush_color(self.brush_color)
                canvas.set_tool(self.edit_mode or "redaction")
                canvas.set_zoom_level(self.zoom_level)
                
                # Add canvas to container and hide it initially
                canvas.setParent(self.canvas_container)
                self.canvas_container_layout.addWidget(canvas)
                canvas.hide()
                
                self.page_canvases.append(canvas)
            
            # Show first page
            if self.page_canvases:
                self.show_page(0)
            
            self.logger.info(f"Loaded PDF: {Path(self.pdf_path).name} with {len(self.page_canvases)} pages")
            
        except Exception as e:
            self.logger.error(f"Error loading PDF: {e}")
            self.show_error(f"Failed to load PDF: {str(e)}")
    
    def show_page(self, page_num: int):
        """Show specified page using show/hide instead of setWidget"""
        if 0 <= page_num < len(self.page_canvases):
            # Hide all canvases first
            for canvas in self.page_canvases:
                canvas.hide()
            
            # Hide error label if visible
            self.pdf_label.hide()
            
            # Show the requested canvas
            self.current_page = page_num
            canvas = self.page_canvases[page_num]
            
            # Update canvas settings
            canvas.set_brush_size(self.brush_size)
            canvas.set_brush_color(self.brush_color)
            canvas.set_tool(self.edit_mode or "redaction")
            canvas.set_excluded(page_num in self.excluded_pages)
            
            # Show the canvas
            canvas.show()
            
            # Ensure the canvas is visible in the scroll area
            self.scroll_area.ensureWidgetVisible(canvas)
            
            # Emit page changed signal
            self.page_changed.emit(page_num)
    
    def show_error(self, message: str):
        """Show error message"""
        # Hide all canvases
        for canvas in self.page_canvases:
            canvas.hide()
        
        # Show error in label
        self.pdf_label.setText(f"❌ {message}")
        self.pdf_label.setStyleSheet("""
            QLabel {
                color: red;
                font-size: 14px;
                padding: 20px;
                background-color: #fff5f5;
                border: 1px solid #ffcccc;
            }
        """)
        self.pdf_label.show()
    
    def render_current_page(self):
        """Render the current page"""
        if not self.pdf_document:
            return
        
        try:
            # Get the current page
            page = self.pdf_document[self.current_page]
            
            # Create transformation matrix for zoom
            mat = fitz.Matrix(self.zoom_level, self.zoom_level)
            
            # Render page to pixmap
            pix = page.get_pixmap(matrix=mat)
            
            # Convert to QPixmap
            img_data = pix.tobytes("ppm")
            qpixmap = QPixmap()
            qpixmap.loadFromData(img_data)
            
            # Add exclusion overlay if page is excluded
            if self.current_page in self.excluded_pages:
                painter = QPainter(qpixmap)
                painter.fillRect(qpixmap.rect(), QColor(255, 0, 0, 100))  # Red overlay
                painter.setPen(QColor(255, 255, 255))
                painter.drawText(qpixmap.rect(), Qt.AlignmentFlag.AlignCenter, "EXCLUDED FROM FAX")
                painter.end()
            
            # Display in label
            self.pdf_label.setPixmap(qpixmap)
            self.pdf_label.resize(qpixmap.size())
            
            # Update scroll area
            self.scroll_area.ensureWidgetVisible(self.pdf_label)
            
        except Exception as e:
            self.logger.error(f"Error rendering page: {e}")
            self.show_error(f"Failed to render page: {str(e)}")
    
    def get_page_count(self) -> int:
        """Get total number of pages"""
        if self.pdf_document:
            return len(self.pdf_document)
        return 0
    
    def go_to_page(self, page_number: int):
        """Go to specific page"""
        if not self.page_canvases:
            return
        
        if 0 <= page_number < len(self.page_canvases):
            self.show_page(page_number)
    
    def set_zoom(self, zoom_level: float):
        """Set zoom level and re-render current page"""
        self.zoom_level = zoom_level
        
        # Re-render the current page at the new zoom level
        if self.pdf_document and self.page_canvases:
            try:
                # Get current page
                page_num = self.current_page
                page = self.pdf_document[page_num]
                
                # Create transformation matrix for new zoom
                mat = fitz.Matrix(zoom_level * 150/72, zoom_level * 150/72)  # Base 150 DPI * zoom
                pix = page.get_pixmap(matrix=mat)
                
                # Convert to QPixmap
                img_data = pix.tobytes("ppm")
                qpixmap = QPixmap()
                qpixmap.loadFromData(img_data)
                
                # Update the current canvas with new image
                if 0 <= page_num < len(self.page_canvases):
                    canvas = self.page_canvases[page_num]
                    
                    # Store the old overlay data
                    old_brush_strokes = canvas.brush_strokes.copy()
                    old_annotations = canvas.annotations.copy()
                    old_excluded = canvas.excluded
                    
                    # Update the canvas with new image
                    canvas.page_image = qpixmap
                    canvas.setPixmap(qpixmap)
                    canvas.setMinimumSize(qpixmap.size())
                    
                    # Recreate overlay at new size
                    canvas.overlay = QPixmap(qpixmap.size())
                    canvas.overlay.fill(Qt.GlobalColor.transparent)
                    
                    # Keep brush strokes and annotations in PDF coordinates (no scaling needed)
                    canvas.brush_strokes = old_brush_strokes
                    canvas.annotations = old_annotations
                    canvas.excluded = old_excluded
                    
                    # Update canvas zoom level and redraw
                    canvas.set_zoom_level(zoom_level)
                    
                    # Ensure the canvas is visible in the scroll area
                    self.scroll_area.ensureWidgetVisible(canvas)
                
                # Save zoom level to settings
                try:
                    from core.settings import get_settings
                    settings = get_settings()
                    settings.set("pdf_settings.default_zoom_level", zoom_level)
                    settings.save_settings()
                    self.logger.info(f"Saved zoom level {zoom_level:.2f} to settings")
                except Exception as save_error:
                    self.logger.warning(f"Could not save zoom setting: {save_error}")
                
                self.zoom_changed.emit(zoom_level)
                
            except Exception as e:
                self.logger.error(f"Error setting zoom level: {e}")
    
    def set_edit_mode(self, mode: Optional[str]):
        """Set editing mode"""
        self.edit_mode = mode
        
        # Update current canvas tool
        if self.page_canvases and 0 <= self.current_page < len(self.page_canvases):
            canvas = self.page_canvases[self.current_page]
            canvas.set_tool(mode or "redaction")
        
        # Change cursor based on mode
        if mode == 'redaction':
            self.setCursor(Qt.CursorShape.CrossCursor)
        elif mode == 'highlight':
            self.setCursor(Qt.CursorShape.PointingHandCursor)
        elif mode == 'text':
            self.setCursor(Qt.CursorShape.IBeamCursor)
        else:
            self.setCursor(Qt.CursorShape.ArrowCursor)
    
    def set_brush_size(self, size: int):
        """Set brush size for all canvases"""
        self.brush_size = size
        for canvas in self.page_canvases:
            canvas.set_brush_size(size)
    
    def set_brush_color(self, color: QColor):
        """Set brush color for all canvases"""
        self.brush_color = color
        for canvas in self.page_canvases:
            canvas.set_brush_color(color)
    
    def undo_last_edit(self):
        """Undo the last edit on current page"""
        if self.page_canvases and 0 <= self.current_page < len(self.page_canvases):
            canvas = self.page_canvases[self.current_page]
            canvas.undo()
            self.logger.info(f"Undid last edit on page {self.current_page + 1}")
    
    def toggle_page_exclusion(self):
        """Toggle exclusion of current page"""
        if self.current_page in self.excluded_pages:
            self.excluded_pages.remove(self.current_page)
            self.logger.info(f"Page {self.current_page + 1} included in fax")
        else:
            self.excluded_pages.add(self.current_page)
            self.logger.info(f"Page {self.current_page + 1} excluded from fax")
        
        # Update canvas exclusion state
        if self.page_canvases and 0 <= self.current_page < len(self.page_canvases):
            canvas = self.page_canvases[self.current_page]
            canvas.set_excluded(self.current_page in self.excluded_pages)
    
    def is_page_excluded(self, page_number: int) -> bool:
        """Check if a page is excluded"""
        return page_number in self.excluded_pages
    
    def get_excluded_pages(self) -> list:
        """Get list of excluded page numbers"""
        return sorted(list(self.excluded_pages))
    
    def get_included_page_count(self) -> int:
        """Get count of pages that will be included in fax"""
        if self.pdf_document:
            return len(self.pdf_document) - len(self.excluded_pages)
        return 0
    
    
    def get_edit_data(self) -> Dict[str, Any]:
        """Collect edit data from all page canvases"""
        edit_data = {'pages': []}
        for canvas in self.page_canvases:
            page_data = {
                'page_number': canvas.page_number,
                'excluded': canvas.excluded,
                'brush_strokes': canvas.brush_strokes.copy(),
                'annotations': canvas.annotations.copy()
            }
            edit_data['pages'].append(page_data)
        return edit_data

    def apply_edit_data(self, edit_data: Dict[str, Any]):
        """Apply saved edit data to page canvases"""
        pages_data = edit_data.get('pages', [])
        for page_data in pages_data:
            page_num = page_data.get('page_number', -1)
            if 0 <= page_num < len(self.page_canvases):
                canvas = self.page_canvases[page_num]
                canvas.brush_strokes = page_data.get('brush_strokes', [])
                canvas.annotations = page_data.get('annotations', [])
                canvas.excluded = page_data.get('excluded', False)
                canvas.redraw_overlay()
        # Update excluded_pages set
        self.excluded_pages = {p['page_number'] for p in pages_data if p.get('excluded', False)}

    def save_pdf(self, output_path: Optional[str] = None) -> bool:
        """Save PDF with edits applied to a new file"""
        if not self.pdf_document:
            self.logger.warning("No PDF document loaded")
            return False
        
        try:
            # For now, we'll use the existing PDFProcessor to apply edits
            from pdf.pdf_processor import PDFProcessor
            
            # Get edit data for this PDF
            edit_data = self.get_edit_data()
            
            # If no edits, just return True (no need to save)
            if not self._has_edits(edit_data):
                self.logger.info("No edits to save")
                return True
            
            # Generate output path if not provided
            if not output_path:
                from pathlib import Path
                import time
                timestamp = int(time.time())
                output_path = f"temp/edited_{timestamp}_{Path(self.pdf_path).name}"
                
                # Create temp directory if it doesn't exist
                Path("temp").mkdir(exist_ok=True)
            
            # Use PDFProcessor to apply edits
            processor = PDFProcessor()
            success = processor.apply_edits_to_pdf(self.pdf_path, edit_data, output_path)
            
            if success:
                self.logger.info(f"Successfully saved PDF with edits to: {output_path}")
                return True
            else:
                self.logger.error(f"Failed to save PDF with edits to: {output_path}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error saving PDF with edits: {e}")
            return False
    
    def _has_edits(self, edit_data: Dict[str, Any]) -> bool:
        """Check if edit data contains any actual edits"""
        pages_data = edit_data.get('pages', [])
        
        for page_data in pages_data:
            # Check for excluded pages
            if page_data.get('excluded', False):
                return True
                
            # Check for brush strokes
            if page_data.get('brush_strokes'):
                return True
                
            # Check for annotations
            if page_data.get('annotations'):
                return True
        
        return False
    
    def closeEvent(self, event):
        """Clean up when widget is closed"""
        if self.pdf_document:
            self.pdf_document.close()
        event.accept()
