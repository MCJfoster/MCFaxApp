"""
Custom Progress Button Widget
A button that displays progress as a visual fill from left to right
"""

from PyQt6.QtWidgets import QPushButton
from PyQt6.QtCore import Qt, QPropertyAnimation, QEasingCurve, pyqtProperty
from PyQt6.QtGui import QPainter, QColor, QLinearGradient, QBrush
from typing import Optional

class ProgressButton(QPushButton):
    """A button that can display progress as a visual fill"""
    
    def __init__(self, text: str = "", parent=None):
        super().__init__(text, parent)
        self._progress = 0.0
        self._is_processing = False
        self._original_text = text
        self._processing_text = "Generating Final Preview"
        
        # Set up default styling
        self.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: none;
                padding: 8px 16px;
                font-size: 12px;
                font-weight: bold;
                border-radius: 4px;
                min-height: 20px;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
            QPushButton:disabled {
                background-color: #CCCCCC;
                color: #666666;
            }
        """)
    
    @pyqtProperty(float)
    def progress(self):
        """Get the current progress value (0.0 to 1.0)"""
        return self._progress
    
    @progress.setter
    def progress(self, value: float):
        """Set the progress value (0.0 to 1.0)"""
        self._progress = max(0.0, min(1.0, value))
        self.update()  # Trigger repaint
    
    def set_progress(self, value: int):
        """Set progress from integer percentage (0-100)"""
        self.progress = value / 100.0
    
    def start_processing(self):
        """Start processing mode"""
        self._is_processing = True
        self.setEnabled(False)
        self.setText(self._processing_text)
        self.progress = 0.0
        
        # Change to grey background during processing
        self.setStyleSheet("""
            QPushButton {
                background-color: #CCCCCC;
                color: #666666;
                border: none;
                padding: 8px 16px;
                font-size: 12px;
                font-weight: bold;
                border-radius: 4px;
                min-height: 20px;
            }
        """)
    
    def finish_processing(self, success: bool = True):
        """Finish processing mode"""
        self._is_processing = False
        self.setEnabled(True)
        self.setText(self._original_text)
        
        if success:
            self.progress = 1.0
        else:
            self.progress = 0.0
        
        # Restore normal styling
        self.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: none;
                padding: 8px 16px;
                font-size: 12px;
                font-weight: bold;
                border-radius: 4px;
                min-height: 20px;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
            QPushButton:disabled {
                background-color: #CCCCCC;
                color: #666666;
            }
        """)
    
    def reset(self):
        """Reset button to initial state"""
        self.finish_processing(success=False)
    
    def paintEvent(self, event):
        """Custom paint event to draw progress fill"""
        super().paintEvent(event)
        
        if self._is_processing and self._progress > 0:
            painter = QPainter(self)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            
            # Calculate progress width
            button_rect = self.rect()
            progress_width = int(button_rect.width() * self._progress)
            
            if progress_width > 0:
                # Create gradient for progress fill
                gradient = QLinearGradient(0, 0, progress_width, 0)
                gradient.setColorAt(0, QColor(33, 150, 243, 180))  # Semi-transparent blue
                gradient.setColorAt(1, QColor(25, 118, 210, 180))  # Darker blue
                
                # Draw progress fill
                progress_rect = button_rect.adjusted(0, 0, -(button_rect.width() - progress_width), 0)
                painter.fillRect(progress_rect, QBrush(gradient))
            
            painter.end()
    
    def set_original_text(self, text: str):
        """Set the original button text"""
        self._original_text = text
        if not self._is_processing:
            self.setText(text)
    
    def set_processing_text(self, text: str):
        """Set the processing button text"""
        self._processing_text = text
        if self._is_processing:
            self.setText(text)
