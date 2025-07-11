"""
Fax Job Creation Window
Handles the creation and configuration of fax jobs
"""

import os
import logging
import base64
from pathlib import Path
from typing import List, Optional, Dict, Any
from PyQt6.QtWidgets import (
    QDialog, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QPushButton, QLabel, QListWidget, QListWidgetItem, QGroupBox,
    QLineEdit, QTextEdit, QComboBox, QSpinBox, QCheckBox,
    QTabWidget, QScrollArea, QMessageBox, QProgressBar,
    QSplitter, QFrame, QSlider, QButtonGroup
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt6.QtGui import QFont, QPixmap, QPainter, QColor

from pdf.pdf_viewer import PDFViewer
from pdf.pdf_editor import PDFEditor
from pdf.pdf_processor import PDFProcessor
from pdf.cover_page import CoverPageGenerator
from database.models import Contact, FaxJob, CoverPageDetails, ContactRepository, FaxJobRepository
from fax.xml_generator import FaxXMLGenerator
from .integrated_pdf_viewer import IntegratedPDFViewer
from .progress_button import ProgressButton

class FaxJobWindow(QDialog):
    """Window for creating and configuring fax jobs"""
    
    def __init__(self, selected_pdfs: List[str], contact_repo: ContactRepository, 
                 fax_job_repo: FaxJobRepository, parent=None):
        super().__init__(parent)
        self.logger = logging.getLogger(__name__)
        
        # Store dependencies
        self.selected_pdfs = selected_pdfs
        self.contact_repo = contact_repo
        self.fax_job_repo = fax_job_repo
        
        # Track edit data for each PDF
        self.pdf_edit_data = {}  # Maps PDF path to edit data
        
        # Initialize components
        self.pdf_viewer = None
        self.pdf_processor = PDFProcessor()
        self.cover_page_generator = CoverPageGenerator()
        self.xml_generator = FaxXMLGenerator()
        
        # Current state
        self.current_fax_job = FaxJob()
        self.contacts = []
        self.processed_pdf_path = None
        
        # Setup UI
        self.setup_ui()
        self.load_contacts()
        self.load_selected_pdfs()
        self.load_sender_info()
    
    def setup_ui(self):
        """Setup the user interface"""
        self.setWindowTitle("Create New Fax Job")
        self.setGeometry(150, 150, 1400, 900)
        self.setModal(True)
        
        # Main layout
        main_layout = QVBoxLayout(self)
        
        # Create tab widget
        self.tab_widget = QTabWidget()
        # Connect tab change signal to update summary automatically
        self.tab_widget.currentChanged.connect(self.on_tab_changed)
        main_layout.addWidget(self.tab_widget)
        
        # Create tabs
        self.create_pdf_tab()
        self.create_recipient_tab()
        self.create_cover_page_tab()
        self.create_preview_tab()
        
        # Button layout
        button_layout = QHBoxLayout()
        
        self.back_btn = QPushButton("< Back")
        self.back_btn.clicked.connect(self.previous_tab)
        button_layout.addWidget(self.back_btn)
        
        button_layout.addStretch()
        
        self.next_btn = QPushButton("Next >")
        self.next_btn.clicked.connect(self.next_tab)
        button_layout.addWidget(self.next_btn)
        
        # Submit button is now in the Preview Controls section
        # Keep this for backward compatibility but hide it
        self.submit_btn = QPushButton("Submit Fax Job")
        self.submit_btn.setVisible(False)  # Always hidden now
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        main_layout.addLayout(button_layout)
        
        # Update button states
        self.update_navigation_buttons()
    
    def create_pdf_tab(self):
        """Create PDF selection and editing tab"""
        tab = QWidget()
        layout = QHBoxLayout(tab)
        
        # Left panel - PDF list and controls (narrower)
        left_panel = QGroupBox("PDF Files")
        left_layout = QVBoxLayout(left_panel)
        
        # PDF list
        self.pdf_list = QListWidget()
        self.pdf_list.itemSelectionChanged.connect(self.on_pdf_selected)
        left_layout.addWidget(self.pdf_list)
        
        # PDF controls
        controls_layout = QVBoxLayout()
        
        self.remove_pdf_btn = QPushButton("Remove PDF")
        self.remove_pdf_btn.clicked.connect(self.remove_selected_pdf)
        self.remove_pdf_btn.setEnabled(False)
        controls_layout.addWidget(self.remove_pdf_btn)
        
        left_layout.addLayout(controls_layout)
        
        # PDF info (smaller)
        self.pdf_info_text = QTextEdit()
        self.pdf_info_text.setMaximumHeight(100)
        self.pdf_info_text.setReadOnly(True)
        self.pdf_info_text.setPlaceholderText("Select a PDF to view details...")
        left_layout.addWidget(self.pdf_info_text)
        
        layout.addWidget(left_panel, 1)  # Smaller proportion
        
        # Right panel - Integrated PDF viewer/editor (wider)
        right_panel = QGroupBox("PDF Viewer & Editor")
        right_layout = QVBoxLayout(right_panel)
        
        # PDF editing toolbar
        toolbar_layout = QHBoxLayout()
        
        # Page navigation
        self.prev_page_btn = QPushButton("◀ Previous")
        self.prev_page_btn.clicked.connect(self.previous_page)
        self.prev_page_btn.setEnabled(False)
        toolbar_layout.addWidget(self.prev_page_btn)
        
        self.page_label = QLabel("No PDF selected")
        toolbar_layout.addWidget(self.page_label)
        
        self.next_page_btn = QPushButton("Next ▶")
        self.next_page_btn.clicked.connect(self.next_page)
        self.next_page_btn.setEnabled(False)
        toolbar_layout.addWidget(self.next_page_btn)
        
        toolbar_layout.addStretch()
        
        # Zoom controls
        self.zoom_out_btn = QPushButton("Zoom Out")
        self.zoom_out_btn.clicked.connect(self.zoom_out)
        self.zoom_out_btn.setEnabled(False)
        toolbar_layout.addWidget(self.zoom_out_btn)
        
        self.zoom_label = QLabel("100%")
        toolbar_layout.addWidget(self.zoom_label)
        
        self.zoom_in_btn = QPushButton("Zoom In")
        self.zoom_in_btn.clicked.connect(self.zoom_in)
        self.zoom_in_btn.setEnabled(False)
        toolbar_layout.addWidget(self.zoom_in_btn)
        
        right_layout.addLayout(toolbar_layout)
        
        # PDF editing tools
        edit_toolbar_layout = QHBoxLayout()
        
        self.redact_btn = QPushButton("🖍️ Redact")
        self.redact_btn.clicked.connect(self.toggle_redact_mode)
        self.redact_btn.setEnabled(False)
        self.redact_btn.setCheckable(True)
        edit_toolbar_layout.addWidget(self.redact_btn)
        
        self.highlight_btn = QPushButton("🖍️ Highlight")
        self.highlight_btn.clicked.connect(self.toggle_highlight_mode)
        self.highlight_btn.setEnabled(False)
        self.highlight_btn.setCheckable(True)
        edit_toolbar_layout.addWidget(self.highlight_btn)
        
        self.text_btn = QPushButton("📝 Add Text")
        self.text_btn.clicked.connect(self.toggle_text_mode)
        self.text_btn.setEnabled(False)
        self.text_btn.setCheckable(True)
        edit_toolbar_layout.addWidget(self.text_btn)
        
        edit_toolbar_layout.addStretch()
        
        self.undo_btn = QPushButton("↶ Undo")
        self.undo_btn.clicked.connect(self.undo_edit)
        self.undo_btn.setEnabled(False)
        edit_toolbar_layout.addWidget(self.undo_btn)
        
        edit_toolbar_layout.addStretch()
        
        # Brush size controls
        edit_toolbar_layout.addWidget(QLabel("Brush Size:"))
        self.brush_size_slider = QSlider(Qt.Orientation.Horizontal)
        self.brush_size_slider.setRange(1, 50)
        self.brush_size_slider.setValue(10)
        self.brush_size_slider.setMaximumWidth(100)
        self.brush_size_slider.valueChanged.connect(self.update_brush_size)
        self.brush_size_slider.setEnabled(False)
        edit_toolbar_layout.addWidget(self.brush_size_slider)
        
        self.brush_size_label = QLabel("10px")
        edit_toolbar_layout.addWidget(self.brush_size_label)
        
        # Color selection buttons
        edit_toolbar_layout.addWidget(QLabel("Color:"))
        
        self.black_btn = QPushButton("Black")
        self.black_btn.setStyleSheet("QPushButton { background-color: black; color: white; }")
        self.black_btn.clicked.connect(lambda: self.set_brush_color(QColor(0, 0, 0)))
        self.black_btn.setEnabled(False)
        self.black_btn.setCheckable(True)
        self.black_btn.setChecked(True)
        edit_toolbar_layout.addWidget(self.black_btn)
        
        self.grey_btn = QPushButton("Grey")
        self.grey_btn.setStyleSheet("QPushButton { background-color: grey; color: white; }")
        self.grey_btn.clicked.connect(lambda: self.set_brush_color(QColor(128, 128, 128)))
        self.grey_btn.setEnabled(False)
        self.grey_btn.setCheckable(True)
        edit_toolbar_layout.addWidget(self.grey_btn)
        
        self.white_btn = QPushButton("White")
        self.white_btn.setStyleSheet("QPushButton { background-color: white; color: black; border: 1px solid black; }")
        self.white_btn.clicked.connect(lambda: self.set_brush_color(QColor(255, 255, 255)))
        self.white_btn.setEnabled(False)
        self.white_btn.setCheckable(True)
        edit_toolbar_layout.addWidget(self.white_btn)
        
        # Create button group for color selection
        self.color_button_group = QButtonGroup()
        self.color_button_group.addButton(self.black_btn)
        self.color_button_group.addButton(self.grey_btn)
        self.color_button_group.addButton(self.white_btn)
        
        edit_toolbar_layout.addStretch()
        
        self.exclude_page_btn = QPushButton("🚫 Exclude Page")
        self.exclude_page_btn.clicked.connect(self.toggle_page_exclusion)
        self.exclude_page_btn.setEnabled(False)
        self.exclude_page_btn.setCheckable(True)
        edit_toolbar_layout.addWidget(self.exclude_page_btn)
        
        self.save_pdf_btn = QPushButton("💾 Save PDF")
        self.save_pdf_btn.clicked.connect(self.save_pdf_edits)
        self.save_pdf_btn.setEnabled(False)
        edit_toolbar_layout.addWidget(self.save_pdf_btn)
        
        right_layout.addLayout(edit_toolbar_layout)
        
        # PDF viewer area
        self.pdf_viewer_container = QWidget()
        self.pdf_viewer_container.setMinimumHeight(400)
        self.pdf_viewer_container.setStyleSheet("""
            QWidget {
                background-color: #f0f0f0;
                border: 1px solid #ccc;
            }
        """)
        self.pdf_viewer_layout = QVBoxLayout(self.pdf_viewer_container)
        
        # Placeholder label
        self.pdf_placeholder_label = QLabel("Select a PDF file from the list to view and edit it here")
        self.pdf_placeholder_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.pdf_placeholder_label.setStyleSheet("color: #666; font-size: 14px; font-style: italic;")
        self.pdf_viewer_layout.addWidget(self.pdf_placeholder_label)
        
        scroll_area = QScrollArea()
        scroll_area.setWidget(self.pdf_viewer_container)
        scroll_area.setWidgetResizable(True)
        right_layout.addWidget(scroll_area)
        
        layout.addWidget(right_panel, 3)  # Larger proportion
        
        # Initialize PDF viewer state
        self.current_pdf_path = None
        self.current_page = 0
        self.zoom_level = 1.0
        self.pdf_viewer = None
        self.edit_mode = None  # 'redact', 'highlight', 'text', or None
        
        self.tab_widget.addTab(tab, "1. PDF Selection & Editing")
    
    def create_cover_page_tab(self):
        """Create cover page configuration tab"""
        tab = QWidget()
        main_layout = QHBoxLayout(tab)
        
        # Left side - Form controls (60% width)
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 10, 0)
        
        # Sender Information Section (Compact)
        sender_group = QGroupBox("Sender Information")
        sender_layout = QGridLayout(sender_group)
        sender_layout.setVerticalSpacing(8)
        sender_layout.setHorizontalSpacing(10)
        
        # From Name
        sender_layout.addWidget(QLabel("Name:"), 0, 0)
        self.from_name_edit = QLineEdit()
        sender_layout.addWidget(self.from_name_edit, 0, 1)
        
        # From Company
        sender_layout.addWidget(QLabel("Company:"), 1, 0)
        self.from_company_edit = QLineEdit()
        sender_layout.addWidget(self.from_company_edit, 1, 1)
        
        # From Phone
        sender_layout.addWidget(QLabel("Phone:"), 2, 0)
        self.from_phone_edit = QLineEdit()
        sender_layout.addWidget(self.from_phone_edit, 2, 1)
        
        # From Email
        sender_layout.addWidget(QLabel("Email:"), 3, 0)
        self.from_email_edit = QLineEdit()
        sender_layout.addWidget(self.from_email_edit, 3, 1)
        
        # Save sender info button
        save_sender_btn = QPushButton("Save as Default")
        save_sender_btn.clicked.connect(self.save_sender_info)
        sender_layout.addWidget(save_sender_btn, 4, 0, 1, 2)
        
        # Create aliases for backward compatibility
        self.sender_name_edit = self.from_name_edit
        self.sender_email_edit = self.from_email_edit
        
        left_layout.addWidget(sender_group)
        
        # Recipient Information Section (auto-filled, compact)
        recipient_group = QGroupBox("Recipient Information")
        recipient_layout = QGridLayout(recipient_group)
        recipient_layout.setVerticalSpacing(8)
        recipient_layout.setHorizontalSpacing(10)
        
        # To Name (auto-filled)
        recipient_layout.addWidget(QLabel("To:"), 0, 0)
        self.to_edit = QLineEdit()
        self.to_edit.setReadOnly(True)
        self.to_edit.setStyleSheet("background-color: #f0f0f0;")
        recipient_layout.addWidget(self.to_edit, 0, 1)
        
        # Fax Number (auto-filled)
        recipient_layout.addWidget(QLabel("Fax:"), 1, 0)
        self.fax_edit = QLineEdit()
        self.fax_edit.setReadOnly(True)
        self.fax_edit.setStyleSheet("background-color: #f0f0f0;")
        recipient_layout.addWidget(self.fax_edit, 1, 1)
        
        left_layout.addWidget(recipient_group)
        
        # Message Details Section (Compact)
        details_group = QGroupBox("Message Details")
        details_layout = QGridLayout(details_group)
        details_layout.setVerticalSpacing(8)
        details_layout.setHorizontalSpacing(10)
        
        # RE field
        details_layout.addWidget(QLabel("Re:"), 0, 0)
        self.re_edit = QLineEdit()
        details_layout.addWidget(self.re_edit, 0, 1)
        
        # Comments field (smaller)
        details_layout.addWidget(QLabel("Comments:"), 1, 0, Qt.AlignmentFlag.AlignTop)
        self.comments_edit = QTextEdit()
        self.comments_edit.setMaximumHeight(60)
        details_layout.addWidget(self.comments_edit, 1, 1)
        
        left_layout.addWidget(details_group)
        
        # Priority Options Section (Compact)
        priority_group = QGroupBox("Priority Options")
        priority_layout = QGridLayout(priority_group)
        priority_layout.setVerticalSpacing(5)
        priority_layout.setHorizontalSpacing(10)
        
        self.urgent_checkbox = QCheckBox("Urgent")
        self.for_review_checkbox = QCheckBox("For Review")
        self.please_comment_checkbox = QCheckBox("Please Comment")
        self.please_reply_checkbox = QCheckBox("Please Reply")
        
        priority_layout.addWidget(self.urgent_checkbox, 0, 0)
        priority_layout.addWidget(self.for_review_checkbox, 0, 1)
        priority_layout.addWidget(self.please_comment_checkbox, 1, 0)
        priority_layout.addWidget(self.please_reply_checkbox, 1, 1)
        
        left_layout.addWidget(priority_group)
        left_layout.addStretch()
        
        # Right side - Visual Preview (40% width)
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(10, 0, 0, 0)
        
        # Visual Preview Section
        preview_group = QGroupBox("Cover Page Preview")
        preview_layout = QVBoxLayout(preview_group)
        
        # Visual preview image area
        self.cover_preview_scroll = QScrollArea()
        self.cover_preview_scroll.setWidgetResizable(True)
        self.cover_preview_scroll.setMinimumHeight(280)
        self.cover_preview_scroll.setStyleSheet("""
            QScrollArea {
                background-color: #f8f8f8;
                border: 1px solid #ccc;
            }
        """)
        
        self.cover_preview_label = QLabel()
        self.cover_preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.cover_preview_label.setStyleSheet("""
            QLabel {
                background-color: white;
                border: 1px solid #ddd;
                margin: 5px;
            }
        """)
        self.cover_preview_label.setText("Visual preview will appear here")
        
        self.cover_preview_scroll.setWidget(self.cover_preview_label)
        preview_layout.addWidget(self.cover_preview_scroll)
        
        # Preview buttons
        preview_buttons_layout = QHBoxLayout()
        
        refresh_preview_btn = QPushButton("🔄 Refresh")
        refresh_preview_btn.clicked.connect(self.update_cover_visual_preview)
        preview_buttons_layout.addWidget(refresh_preview_btn)
        
        preview_buttons_layout.addStretch()
        
        preview_layout.addLayout(preview_buttons_layout)
        
        right_layout.addWidget(preview_group)
        
        # Add panels to main layout with proper proportions
        main_layout.addWidget(left_panel, 60)  # 60% width
        main_layout.addWidget(right_panel, 40)  # 40% width
        
        # Connect form fields to update preview on field exit
        self.from_name_edit.editingFinished.connect(self.update_cover_visual_preview)
        self.from_company_edit.editingFinished.connect(self.update_cover_visual_preview)
        self.from_phone_edit.editingFinished.connect(self.update_cover_visual_preview)
        self.re_edit.editingFinished.connect(self.update_cover_visual_preview)
        self.comments_edit.textChanged.connect(self.schedule_preview_update)
        self.urgent_checkbox.toggled.connect(self.update_cover_visual_preview)
        self.for_review_checkbox.toggled.connect(self.update_cover_visual_preview)
        self.please_comment_checkbox.toggled.connect(self.update_cover_visual_preview)
        self.please_reply_checkbox.toggled.connect(self.update_cover_visual_preview)
        
        # Initialize preview update timer for comments field
        self.preview_update_timer = QTimer()
        self.preview_update_timer.setSingleShot(True)
        self.preview_update_timer.timeout.connect(self.update_cover_visual_preview)
        
        # Initial preview update
        QTimer.singleShot(500, self.update_cover_visual_preview)
        
        self.tab_widget.addTab(tab, "3. Cover Page")
    
    def create_recipient_tab(self):
        """Create recipient selection tab"""
        tab = QWidget()
        main_layout = QVBoxLayout(tab)
        
        # Fax Job Settings Section (at top)
        settings_group = QGroupBox("Fax Job Settings")
        settings_layout = QGridLayout(settings_group)
        settings_layout.setVerticalSpacing(8)
        settings_layout.setHorizontalSpacing(15)
        
        # Priority
        settings_layout.addWidget(QLabel("Priority:"), 0, 0)
        self.priority_combo = QComboBox()
        self.priority_combo.addItems(["1st", "High", "Medium/High", "Medium", "Medium/Low", "Low"])
        self.priority_combo.setCurrentText("Medium")
        settings_layout.addWidget(self.priority_combo, 0, 1)
        
        # Max attempts
        settings_layout.addWidget(QLabel("Max Attempts:"), 0, 2)
        self.max_attempts_spin = QSpinBox()
        self.max_attempts_spin.setRange(1, 10)
        self.max_attempts_spin.setValue(3)
        settings_layout.addWidget(self.max_attempts_spin, 0, 3)
        
        # Retry interval
        settings_layout.addWidget(QLabel("Retry Interval:"), 1, 0)
        self.retry_interval_spin = QSpinBox()
        self.retry_interval_spin.setRange(1, 60)
        self.retry_interval_spin.setValue(5)
        self.retry_interval_spin.setSuffix(" minutes")
        settings_layout.addWidget(self.retry_interval_spin, 1, 1)
        
        # Add some spacing
        settings_layout.setColumnStretch(4, 1)
        
        main_layout.addWidget(settings_group)
        
        # Contact selection and details section
        contact_layout = QHBoxLayout()
        
        # Left panel - Contact selection
        left_panel = QGroupBox("Select Recipient")
        left_layout = QVBoxLayout(left_panel)
        
        # Contact search
        search_layout = QHBoxLayout()
        search_layout.addWidget(QLabel("Search:"))
        self.contact_search = QLineEdit()
        self.contact_search.textChanged.connect(self.filter_contacts)
        search_layout.addWidget(self.contact_search)
        left_layout.addLayout(search_layout)
        
        # Contact list
        self.contact_list = QListWidget()
        self.contact_list.itemSelectionChanged.connect(self.on_contact_selected)
        left_layout.addWidget(self.contact_list)
        
        # New contact button
        new_contact_btn = QPushButton("Add New Contact")
        new_contact_btn.clicked.connect(self.add_new_contact)
        left_layout.addWidget(new_contact_btn)
        
        contact_layout.addWidget(left_panel, 1)
        
        # Right panel - Contact details
        right_panel = QGroupBox("Contact Details")
        right_layout = QGridLayout(right_panel)
        
        # Contact form
        right_layout.addWidget(QLabel("Name:"), 0, 0)
        self.contact_name_edit = QLineEdit()
        right_layout.addWidget(self.contact_name_edit, 0, 1)
        
        right_layout.addWidget(QLabel("Fax Number:"), 1, 0)
        self.contact_fax_edit = QLineEdit()
        right_layout.addWidget(self.contact_fax_edit, 1, 1)
        
        right_layout.addWidget(QLabel("Organization:"), 2, 0)
        self.contact_org_edit = QLineEdit()
        right_layout.addWidget(self.contact_org_edit, 2, 1)
        
        right_layout.addWidget(QLabel("Phone:"), 3, 0)
        self.contact_phone_edit = QLineEdit()
        right_layout.addWidget(self.contact_phone_edit, 3, 1)
        
        right_layout.addWidget(QLabel("Email:"), 4, 0)
        self.contact_email_edit = QLineEdit()
        right_layout.addWidget(self.contact_email_edit, 4, 1)
        
        right_layout.addWidget(QLabel("Notes:"), 5, 0, Qt.AlignmentFlag.AlignTop)
        self.contact_notes_edit = QTextEdit()
        self.contact_notes_edit.setMaximumHeight(80)
        right_layout.addWidget(self.contact_notes_edit, 5, 1)
        
        # Save contact button
        save_contact_btn = QPushButton("Save Contact")
        save_contact_btn.clicked.connect(self.save_contact)
        right_layout.addWidget(save_contact_btn, 6, 0, 1, 2)
        
        contact_layout.addWidget(right_panel, 1)
        
        main_layout.addLayout(contact_layout)
        
        self.tab_widget.addTab(tab, "2. Recipient")
    
    
    def create_preview_tab(self):
        """Create preview and submission tab"""
        tab = QWidget()
        layout = QHBoxLayout(tab)
        
        # Left panel - Summary and controls
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        
        # Summary section (expanded - no height limit)
        summary_group = QGroupBox("Fax Job Summary")
        summary_layout = QVBoxLayout(summary_group)
        
        self.summary_text = QTextEdit()
        self.summary_text.setReadOnly(True)
        # Remove height limit to allow summary to expand
        summary_layout.addWidget(self.summary_text)
        
        left_layout.addWidget(summary_group, 3)  # Give summary more weight
        
        # Preview controls (pushed down)
        preview_controls_group = QGroupBox("Preview Controls")
        preview_controls_layout = QVBoxLayout(preview_controls_group)
        
        # Generate preview button (using custom progress button)
        self.generate_preview_btn = ProgressButton("🔄 Generate Final Preview")
        self.generate_preview_btn.clicked.connect(self.generate_final_preview)
        preview_controls_layout.addWidget(self.generate_preview_btn)
        
        # Preview navigation
        nav_layout = QHBoxLayout()
        
        self.preview_prev_btn = QPushButton("◀ Previous")
        self.preview_prev_btn.clicked.connect(self.preview_previous_page)
        self.preview_prev_btn.setEnabled(False)
        nav_layout.addWidget(self.preview_prev_btn)
        
        self.preview_page_label = QLabel("No preview generated")
        nav_layout.addWidget(self.preview_page_label)
        
        self.preview_next_btn = QPushButton("Next ▶")
        self.preview_next_btn.clicked.connect(self.preview_next_page)
        self.preview_next_btn.setEnabled(False)
        nav_layout.addWidget(self.preview_next_btn)
        
        preview_controls_layout.addLayout(nav_layout)
        
        # Zoom controls for preview
        zoom_layout = QHBoxLayout()
        
        self.preview_zoom_out_btn = QPushButton("Zoom Out")
        self.preview_zoom_out_btn.clicked.connect(self.preview_zoom_out)
        self.preview_zoom_out_btn.setEnabled(False)
        zoom_layout.addWidget(self.preview_zoom_out_btn)
        
        self.preview_zoom_label = QLabel("100%")
        zoom_layout.addWidget(self.preview_zoom_label)
        
        self.preview_zoom_in_btn = QPushButton("Zoom In")
        self.preview_zoom_in_btn.clicked.connect(self.preview_zoom_in)
        self.preview_zoom_in_btn.setEnabled(False)
        zoom_layout.addWidget(self.preview_zoom_in_btn)
        
        preview_controls_layout.addLayout(zoom_layout)
        
        # Add Submit Fax Job button to preview controls
        preview_controls_layout.addWidget(QLabel())  # Small spacer
        
        # Create the submit button here (moved from main button layout)
        self.preview_submit_btn = QPushButton("Submit Fax Job")
        self.preview_submit_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 12px 24px;
                font-size: 14px;
                font-weight: bold;
                border-radius: 5px;
                margin-top: 10px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        self.preview_submit_btn.clicked.connect(self.submit_fax_job)
        preview_controls_layout.addWidget(self.preview_submit_btn)
        
        left_layout.addWidget(preview_controls_group, 1)  # Give controls less weight
        
        layout.addWidget(left_panel, 1)  # 30% width
        
        # Right panel - Final PDF preview
        right_panel = QGroupBox("Final Fax Document Preview")
        right_layout = QVBoxLayout(right_panel)
        
        # Preview area
        self.final_preview_container = QWidget()
        self.final_preview_container.setMinimumHeight(500)
        self.final_preview_container.setStyleSheet("""
            QWidget {
                background-color: #f8f8f8;
                border: 1px solid #ccc;
            }
        """)
        self.final_preview_layout = QVBoxLayout(self.final_preview_container)
        
        # Placeholder label
        self.final_preview_placeholder = QLabel("Click 'Generate Final Preview' to see the complete fax document\n(Cover Page + Selected PDFs)")
        self.final_preview_placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.final_preview_placeholder.setStyleSheet("color: #666; font-size: 14px; font-style: italic;")
        self.final_preview_layout.addWidget(self.final_preview_placeholder)
        
        scroll_area = QScrollArea()
        scroll_area.setWidget(self.final_preview_container)
        scroll_area.setWidgetResizable(True)
        right_layout.addWidget(scroll_area)
        
        layout.addWidget(right_panel, 2)  # 70% width
        
        # Initialize preview state
        self.final_preview_pdf_path = None
        self.final_preview_viewer = None
        self.final_preview_current_page = 0
        self.final_preview_zoom_level = 1.0
        
        self.tab_widget.addTab(tab, "4. Preview & Submit")
    
    def load_contacts(self):
        """Load contacts from database"""
        try:
            self.contacts = self.contact_repo.get_all()
            self.update_contact_list()
        except Exception as e:
            self.logger.error(f"Error loading contacts: {e}")
            QMessageBox.warning(self, "Error", f"Failed to load contacts: {str(e)}")
    
    def update_contact_list(self):
        """Update the contact list widget"""
        self.contact_list.clear()
        search_term = self.contact_search.text().lower()
        
        for contact in self.contacts:
            if (not search_term or 
                search_term in contact.name.lower() or 
                search_term in contact.fax_number.lower() or 
                (contact.organization and search_term in contact.organization.lower())):
                
                item_text = f"{contact.name} - {contact.fax_number}"
                if contact.organization:
                    item_text += f" ({contact.organization})"
                
                item = QListWidgetItem(item_text)
                item.setData(Qt.ItemDataRole.UserRole, contact)
                self.contact_list.addItem(item)
    
    def filter_contacts(self):
        """Filter contacts based on search term"""
        self.update_contact_list()
    
    def on_contact_selected(self):
        """Handle contact selection"""
        current_item = self.contact_list.currentItem()
        if current_item:
            contact = current_item.data(Qt.ItemDataRole.UserRole)
            self.populate_contact_form(contact)
    
    def populate_contact_form(self, contact: Contact):
        """Populate contact form with contact data"""
        self.contact_name_edit.setText(contact.name or "")
        self.contact_fax_edit.setText(contact.fax_number or "")
        self.contact_org_edit.setText(contact.organization or "")
        self.contact_phone_edit.setText(contact.phone_number or "")
        self.contact_email_edit.setText(contact.email or "")
        self.contact_notes_edit.setText(contact.notes or "")
    
    def add_new_contact(self):
        """Add a new contact"""
        self.contact_list.clearSelection()
        self.contact_name_edit.clear()
        self.contact_fax_edit.clear()
        self.contact_org_edit.clear()
        self.contact_phone_edit.clear()
        self.contact_email_edit.clear()
        self.contact_notes_edit.clear()
        self.contact_name_edit.setFocus()
    
    def save_contact(self):
        """Save the current contact"""
        try:
            # Get current contact if editing
            current_item = self.contact_list.currentItem()
            contact = current_item.data(Qt.ItemDataRole.UserRole) if current_item else Contact()
            
            # Update contact data
            contact.name = self.contact_name_edit.text().strip()
            contact.fax_number = self.contact_fax_edit.text().strip()
            contact.organization = self.contact_org_edit.text().strip() or None
            contact.phone_number = self.contact_phone_edit.text().strip() or None
            contact.email = self.contact_email_edit.text().strip() or None
            contact.notes = self.contact_notes_edit.toPlainText().strip() or None
            
            # Validate
            errors = contact.validate()
            if errors:
                QMessageBox.warning(self, "Validation Error", "\n".join(errors))
                return
            
            # Save to database
            if contact.contact_id:
                # Update existing
                self.contact_repo.update(contact)
                QMessageBox.information(self, "Success", "Contact updated successfully")
            else:
                # Create new
                contact_id = self.contact_repo.create(contact)
                contact.contact_id = contact_id
                QMessageBox.information(self, "Success", "Contact created successfully")
            
            # Refresh contact list
            self.load_contacts()
            
        except Exception as e:
            self.logger.error(f"Error saving contact: {e}")
            QMessageBox.critical(self, "Error", f"Failed to save contact: {str(e)}")
    
    def load_selected_pdfs(self):
        """Load the selected PDF files"""
        self.pdf_list.clear()
        for pdf_path in self.selected_pdfs:
            item = QListWidgetItem(Path(pdf_path).name)
            item.setData(Qt.ItemDataRole.UserRole, pdf_path)
            self.pdf_list.addItem(item)
        
        self.update_pdf_info()
    
    def update_pdf_info(self):
        """Update PDF information display"""
        total_size = 0
        total_pages = 0
        file_count = len(self.selected_pdfs)
        
        info_text = f"Selected Files: {file_count}\n"
        
        for pdf_path in self.selected_pdfs:
            try:
                file_path = Path(pdf_path)
                size_mb = file_path.stat().st_size / (1024 * 1024)
                total_size += size_mb
                
                # Get page count (simplified for now)
                # TODO: Implement proper page counting with exclusions
                
            except Exception as e:
                self.logger.error(f"Error analyzing {pdf_path}: {e}")
        
        info_text += f"Total Size: {total_size:.1f} MB\n"
        info_text += f"Size Limit: 36.0 MB\n"
        
        if total_size > 36.0:
            info_text += "⚠️ WARNING: Size exceeds limit!"
        
        self.pdf_info_text.setText(info_text)
    
    def view_selected_pdf(self):
        """View/edit the selected PDF"""
        current_item = self.pdf_list.currentItem()
        if not current_item:
            QMessageBox.information(self, "No Selection", "Please select a PDF file to view.")
            return
        
        pdf_path = current_item.data(Qt.ItemDataRole.UserRole)
        
        try:
            # Create custom message box with clear options
            msg_box = QMessageBox(self)
            msg_box.setWindowTitle("PDF Action")
            msg_box.setText(f"What would you like to do with {Path(pdf_path).name}?")
            
            view_btn = msg_box.addButton("View PDF", QMessageBox.ButtonRole.YesRole)
            edit_btn = msg_box.addButton("Edit PDF", QMessageBox.ButtonRole.NoRole)
            cancel_btn = msg_box.addButton("Cancel", QMessageBox.ButtonRole.RejectRole)
            
            msg_box.setDefaultButton(view_btn)
            msg_box.exec()
            
            clicked_button = msg_box.clickedButton()
            
            if clicked_button == view_btn:
                # View PDF using dialog
                from pdf.pdf_viewer import PDFViewerDialog
                viewer = PDFViewerDialog(pdf_path, self)
                viewer.exec()
                self.logger.info(f"Opened PDF viewer for: {Path(pdf_path).name}")
                
            elif clicked_button == edit_btn:
                # Edit PDF using dialog
                from pdf.pdf_viewer import PDFViewerDialog
                editor = PDFViewerDialog(pdf_path, self)
                editor.exec()
                self.logger.info(f"Opened PDF editor for: {Path(pdf_path).name}")
                
            # Cancel - do nothing
            
        except Exception as e:
            self.logger.error(f"Error opening PDF viewer/editor: {e}")
            QMessageBox.critical(
                self,
                "PDF Error",
                f"Failed to open PDF viewer/editor:\n{str(e)}"
            )
    
    def remove_selected_pdf(self):
        """Remove the selected PDF from the list"""
        current_item = self.pdf_list.currentItem()
        if not current_item:
            QMessageBox.information(self, "No Selection", "Please select a PDF file to remove.")
            return
        
        pdf_path = current_item.data(Qt.ItemDataRole.UserRole)
        self.selected_pdfs.remove(pdf_path)
        
        row = self.pdf_list.row(current_item)
        self.pdf_list.takeItem(row)
        
        self.update_pdf_info()
    
    def preview_cover_page(self):
        """Preview the cover page"""
        # TODO: Implement cover page preview
        QMessageBox.information(self, "Cover Page Preview", "Cover page preview will be implemented here.")
    
    def next_tab(self):
        """Go to next tab"""
        current_index = self.tab_widget.currentIndex()
        
        # Save edits if leaving PDF tab
        if current_index == 0 and self.pdf_viewer and self.current_pdf_path:
            edit_data = self.pdf_viewer.get_edit_data()
            self.pdf_edit_data[self.current_pdf_path] = edit_data
        
        if current_index < self.tab_widget.count() - 1:
            self.tab_widget.setCurrentIndex(current_index + 1)
        self.update_navigation_buttons()

    def previous_tab(self):
        """Go to previous tab"""
        current_index = self.tab_widget.currentIndex()
        
        # Save edits if leaving PDF tab (though previous_tab typically doesn't leave PDF, but for safety)
        if current_index == 0 and self.pdf_viewer and self.current_pdf_path:
            edit_data = self.pdf_viewer.get_edit_data()
            self.pdf_edit_data[self.current_pdf_path] = edit_data
        
        if current_index > 0:
            self.tab_widget.setCurrentIndex(current_index - 1)
        self.update_navigation_buttons()
    
    def on_tab_changed(self, index: int):
        """Handle tab change events"""
        # Update navigation buttons
        self.update_navigation_buttons()
        
        # Auto-update summary when switching to Preview & Submit tab
        if index == self.tab_widget.count() - 1:  # Last tab (Preview & Submit)
            self.update_summary()
    
    def update_navigation_buttons(self):
        """Update navigation button states"""
        # Safety check to ensure buttons exist before trying to use them
        if not hasattr(self, 'back_btn') or not hasattr(self, 'next_btn'):
            return
        
        current_index = self.tab_widget.currentIndex()
        
        self.back_btn.setEnabled(current_index > 0)
        # Hide Next button on the final tab (Preview & Submit)
        self.next_btn.setVisible(current_index < self.tab_widget.count() - 1)
        # Submit button is now in Preview Controls section, always visible on final tab
    
    def update_summary(self):
        """Update the enhanced fax job summary with detailed information"""
        # Safety check to ensure summary_text widget exists
        if not hasattr(self, 'summary_text'):
            return
            
        try:
            summary = "Fax Job Summary:\n\n"
            
            # Recipient Information
            current_contact = self.contact_list.currentItem()
            if current_contact:
                contact = current_contact.data(Qt.ItemDataRole.UserRole)
                summary += "Recipient:\n"
                summary += f"• Name: {contact.name}\n"
                summary += f"• Fax: {contact.fax_number}\n"
                if contact.organization:
                    summary += f"• Organization: {contact.organization}\n"
                summary += "\n"
            else:
                summary += "Recipient: ⚠️ Not selected\n\n"
            
            # Document Information
            total_size_mb = 0.0
            total_pages = 0
            
            summary += "Documents:\n"
            summary += "• Cover Page: Included\n"
            summary += f"• PDF Files: {len(self.selected_pdfs)} files\n"
            
            # Calculate file sizes and estimate pages
            for pdf_path in self.selected_pdfs:
                try:
                    file_path = Path(pdf_path)
                    size_mb = file_path.stat().st_size / (1024 * 1024)
                    total_size_mb += size_mb
                    
                    # Try to get page count if PyMuPDF is available
                    try:
                        import fitz
                        doc = fitz.open(pdf_path)
                        pages = len(doc)
                        doc.close()
                        total_pages += pages
                        summary += f"  - {file_path.name} ({size_mb:.1f} MB, {pages} pages)\n"
                    except ImportError:
                        summary += f"  - {file_path.name} ({size_mb:.1f} MB)\n"
                    except Exception:
                        summary += f"  - {file_path.name} ({size_mb:.1f} MB)\n"
                        
                except Exception as e:
                    summary += f"  - {Path(pdf_path).name} (Error reading file)\n"
            
            # Add cover page to totals (estimate 1 page, ~0.1 MB)
            total_pages += 1
            total_size_mb += 0.1
            
            # Total information with size validation
            if total_pages > 0:
                summary += f"• Total Pages: {total_pages} pages\n"
            summary += f"• Total Size: {total_size_mb:.1f} MB / 36.0 MB limit\n"
            
            # Size warning
            if total_size_mb > 36.0:
                summary += "• ⚠️ WARNING: Size exceeds 36 MB limit!\n"
            elif total_size_mb > 30.0:
                summary += "• ⚠️ CAUTION: Approaching size limit\n"
            
            summary += "\n"
            
            # Settings Information
            summary += "Settings:\n"
            summary += f"• Priority: {self.priority_combo.currentText()}\n"
            summary += f"• Max Attempts: {self.max_attempts_spin.value()}\n"
            summary += f"• Retry Interval: {self.retry_interval_spin.value()} minutes\n"
            
            # Sender Information
            sender_name = self.sender_name_edit.text().strip()
            if sender_name:
                summary += f"• Sender: {sender_name}\n"
            else:
                summary += "• Sender: ⚠️ Not specified\n"
            
            # Validation Status
            summary += "\nValidation:\n"
            validation_errors = []
            
            if not self.selected_pdfs:
                validation_errors.append("No PDF files selected")
            if not current_contact:
                validation_errors.append("No recipient selected")
            if not sender_name:
                validation_errors.append("Sender name required")
            if total_size_mb > 36.0:
                validation_errors.append("File size exceeds limit")
            
            if validation_errors:
                summary += "• ❌ Issues found:\n"
                for error in validation_errors:
                    summary += f"  - {error}\n"
            else:
                summary += "• ✅ Ready to submit\n"
            
            self.summary_text.setText(summary)
            
        except Exception as e:
            self.logger.error(f"Error updating summary: {e}")
            self.summary_text.setText(f"Error generating summary: {str(e)}")
    
    def submit_fax_job(self):
        """Submit the fax job"""
        try:
            # Save current edits before submitting (if user is on PDF tab when submitting)
            if self.tab_widget.currentIndex() == 0 and self.pdf_viewer and self.current_pdf_path:
                edit_data = self.pdf_viewer.get_edit_data()
                self.pdf_edit_data[self.current_pdf_path] = edit_data
            
            # Validate all required fields
            if not self.validate_fax_job():
                return
            
            # Create fax job object
            fax_job = self.create_fax_job_object()
            
            # Step 1: Generate cover page and combine with PDFs
            final_pdf_path = self.generate_final_pdf(fax_job)
            if not final_pdf_path:
                QMessageBox.critical(self, "Error", "Failed to generate final PDF")
                return
            
            # Step 2: Check file size
            file_size_mb = Path(final_pdf_path).stat().st_size / (1024 * 1024)
            if file_size_mb > 36:
                response = QMessageBox.question(
                    self, 
                    "File Size Warning", 
                    f"The final PDF is {file_size_mb:.1f} MB, which exceeds the 36 MB limit.\n\n"
                    "Would you like to:\n"
                    "• Continue anyway (may fail)\n"
                    "• Cancel and remove some PDFs\n\n"
                    "Continue with oversized file?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                    QMessageBox.StandardButton.No
                )
                
                if response == QMessageBox.StandardButton.No:
                    self.cleanup_temp_file(final_pdf_path)
                    return
            
            # Step 3: Update fax job with file paths and metadata
            fax_job.pdf_path = final_pdf_path
            fax_job.page_count = self.calculate_page_count(final_pdf_path)
            fax_job.file_size_mb = file_size_mb
            
            # Step 4: Save to database
            fax_id = self.fax_job_repo.create(fax_job)
            fax_job.fax_id = fax_id
            
            # Step 5: Generate local XML file for storage (with base64 content)
            xml_file_path = self.generate_xml_file_with_base64(fax_job, final_pdf_path)
            if xml_file_path:
                self.logger.info(f"Generated local XML file with base64: {xml_file_path}")
            else:
                self.logger.warning("Failed to generate local XML file")
            
            # Step 6: Submit to FaxFinder (if configured)
            # The FaxFinder API will generate its own XML with base64 content
            submission_result = self.submit_to_faxfinder(fax_job, final_pdf_path)
            
            # Step 7: Update status based on submission result
            if submission_result['success']:
                # Update database with submission details
                if submission_result.get('fax_entry_url'):
                    # Update the fax job with the FaxFinder entry URL
                    # Note: We'd need to add this method to the repository
                    pass
                
                QMessageBox.information(
                    self, 
                    "Success", 
                    f"Fax job created and submitted successfully!\n\n"
                    f"Fax ID: {fax_id}\n"
                    f"PDF: {Path(final_pdf_path).name}\n"
                    f"Size: {file_size_mb:.1f} MB\n"
                    f"Pages: {fax_job.page_count}"
                )
            else:
                # Update status to indicate submission failure
                self.fax_job_repo.update_status(fax_id, "Failed", submission_result.get('error', 'Unknown submission error'))
                
                QMessageBox.warning(
                    self, 
                    "Partial Success", 
                    f"Fax job created but FaxFinder submission failed:\n\n"
                    f"Error: {submission_result.get('error', 'Unknown error')}\n\n"
                    f"The job has been saved and can be resubmitted later.\n"
                    f"Fax ID: {fax_id}"
                )
            
            self.accept()
            
        except Exception as e:
            self.logger.error(f"Error submitting fax job: {e}")
            QMessageBox.critical(self, "Error", f"Failed to submit fax job: {str(e)}")
    
    def validate_fax_job(self) -> bool:
        """Validate the fax job before submission"""
        errors = []
        
        # Check PDFs
        if not self.selected_pdfs:
            errors.append("No PDF files selected")
        
        # Check recipient
        current_contact = self.contact_list.currentItem()
        if not current_contact:
            errors.append("No recipient selected")
        
        # Check sender
        if not self.sender_name_edit.text().strip():
            errors.append("Sender name is required")
        
        if errors:
            QMessageBox.warning(self, "Validation Error", "\n".join(errors))
            return False
        
        return True
    
    def create_fax_job_object(self) -> FaxJob:
        """Create a FaxJob object from the form data"""
        # Get selected contact
        current_contact = self.contact_list.currentItem()
        contact = current_contact.data(Qt.ItemDataRole.UserRole)
        
        # Create cover page details
        cover_page = CoverPageDetails(
            to=self.to_edit.text().strip() or None,
            from_field=self.from_name_edit.text().strip() or None,
            company=self.from_company_edit.text().strip() or None,
            fax=self.fax_edit.text().strip() or None,
            phone=self.from_phone_edit.text().strip() or None,
            re=self.re_edit.text().strip() or None,
            comments=self.comments_edit.toPlainText().strip() or None,
            urgent=self.urgent_checkbox.isChecked(),
            for_review=self.for_review_checkbox.isChecked(),
            please_comment=self.please_comment_checkbox.isChecked(),
            please_reply=self.please_reply_checkbox.isChecked()
        )
        
        # Create fax job
        fax_job = FaxJob(
            sender_name=self.sender_name_edit.text().strip(),
            sender_email=self.sender_email_edit.text().strip() or None,
            recipient_id=contact.contact_id,
            recipient_fax=contact.fax_number,
            priority=self.priority_combo.currentText(),
            max_attempts=self.max_attempts_spin.value(),
            retry_interval=self.retry_interval_spin.value(),
            cover_page_details=cover_page
        )
        
        return fax_job
    
    # New methods for integrated PDF viewer/editor functionality
    
    def on_pdf_selected(self):
        """Handle PDF selection from the list"""
        current_item = self.pdf_list.currentItem()
        if current_item:
            pdf_path = current_item.data(Qt.ItemDataRole.UserRole)
            
            # Save edits from previous PDF if it was loaded
            if self.pdf_viewer and self.current_pdf_path and pdf_path != self.current_pdf_path:
                edit_data = self.pdf_viewer.get_edit_data()
                self.pdf_edit_data[self.current_pdf_path] = edit_data
            
            self.load_pdf_in_viewer(pdf_path)
            self.remove_pdf_btn.setEnabled(True)
            
            # Update PDF info for selected file
            try:
                file_path = Path(pdf_path)
                size_mb = file_path.stat().st_size / (1024 * 1024)
                
                info_text = f"File: {file_path.name}\n"
                info_text += f"Size: {size_mb:.1f} MB\n"
                info_text += f"Path: {pdf_path}"
                
                self.pdf_info_text.setText(info_text)
                
            except Exception as e:
                self.pdf_info_text.setText(f"Error reading file info: {e}")
        else:
            self.clear_pdf_viewer()
            self.remove_pdf_btn.setEnabled(False)
            self.pdf_info_text.clear()
    
    def load_pdf_in_viewer(self, pdf_path: str):
        """Load a PDF file in the integrated viewer"""
        try:
            # Save current PDF path before changing it
            old_pdf_path = self.current_pdf_path
            
            # Update current PDF path
            self.current_pdf_path = pdf_path
            self.current_page = 0
            self.zoom_level = 1.0
            
            # Clear existing viewer (but don't save edit data since we already saved it in on_pdf_selected)
            self.clear_pdf_viewer_without_saving()
            
            # Hide placeholder
            self.pdf_placeholder_label.hide()
            
            # Create integrated PDF viewer widget
            self.pdf_viewer = IntegratedPDFViewer(pdf_path)
            
            # Connect signals
            self.pdf_viewer.page_changed.connect(self.on_viewer_page_changed)
            self.pdf_viewer.zoom_changed.connect(self.on_viewer_zoom_changed)
            
            # Connect edit signal to capture edit data
            if hasattr(self.pdf_viewer, 'pdf_edited'):
                self.pdf_viewer.pdf_edited.connect(self.on_pdf_edited)
            
            # Apply saved edit data if exists
            if pdf_path in self.pdf_edit_data:
                self.pdf_viewer.apply_edit_data(self.pdf_edit_data[pdf_path])
                self.logger.info(f"Applied saved edit data for {Path(pdf_path).name}")
            
            # Add to layout
            self.pdf_viewer_layout.addWidget(self.pdf_viewer)
            
            # Enable controls
            self.enable_pdf_controls(True)
            
            # Update zoom display to match the loaded zoom level
            self.zoom_level = self.pdf_viewer.zoom_level
            self.zoom_label.setText(f"{int(self.zoom_level * 100)}%")
            
            # Update page info with exclusion support
            self.update_page_info_with_exclusion()
            
            self.logger.info(f"Loaded PDF in integrated viewer: {Path(pdf_path).name}")
                
        except Exception as e:
            self.logger.error(f"Error loading PDF in viewer: {e}")
            self.show_pdf_error(f"Error loading PDF: {str(e)}")
    
    def clear_pdf_viewer(self):
        """Clear the PDF viewer"""
        # Save current edits before clearing
        if self.pdf_viewer and self.current_pdf_path:
            try:
                edit_data = self.pdf_viewer.get_edit_data()
                self.pdf_edit_data[self.current_pdf_path] = edit_data
                self.logger.info(f"Saved edit data for {Path(self.current_pdf_path).name} before clearing viewer")
            except Exception as e:
                self.logger.error(f"Error saving edit data before clearing viewer: {e}")
        
        # Remove existing viewer widget
        for i in reversed(range(self.pdf_viewer_layout.count())):
            child = self.pdf_viewer_layout.itemAt(i).widget()
            if child and child != self.pdf_placeholder_label:
                child.setParent(None)
        
        # Show placeholder
        self.pdf_placeholder_label.show()
        
        # Disable controls
        self.enable_pdf_controls(False)
        
        # Reset state
        self.current_pdf_path = None
        self.current_page = 0
        self.zoom_level = 1.0
        self.pdf_viewer = None
        self.edit_mode = None
        
        # Reset button states
        self.redact_btn.setChecked(False)
        self.highlight_btn.setChecked(False)
        self.text_btn.setChecked(False)
    
    def clear_pdf_viewer_without_saving(self):
        """Clear the PDF viewer without saving edit data (used when we already saved it)"""
        # Remove existing viewer widget
        for i in reversed(range(self.pdf_viewer_layout.count())):
            child = self.pdf_viewer_layout.itemAt(i).widget()
            if child and child != self.pdf_placeholder_label:
                child.setParent(None)
        
        # Show placeholder
        self.pdf_placeholder_label.show()
        
        # Disable controls
        self.enable_pdf_controls(False)
        
        # Reset state (but don't save edit data)
        self.pdf_viewer = None
        self.edit_mode = None
        
        # Reset button states
        self.redact_btn.setChecked(False)
        self.highlight_btn.setChecked(False)
        self.text_btn.setChecked(False)
    
    def enable_pdf_controls(self, enabled: bool):
        """Enable or disable PDF controls"""
        self.prev_page_btn.setEnabled(enabled)
        self.next_page_btn.setEnabled(enabled)
        self.zoom_out_btn.setEnabled(enabled)
        self.zoom_in_btn.setEnabled(enabled)
        self.redact_btn.setEnabled(enabled)
        self.highlight_btn.setEnabled(enabled)
        self.text_btn.setEnabled(enabled)
        self.undo_btn.setEnabled(enabled)
        self.exclude_page_btn.setEnabled(enabled)
        self.save_pdf_btn.setEnabled(enabled)
        
        # Enable brush controls
        self.brush_size_slider.setEnabled(enabled)
        self.black_btn.setEnabled(enabled)
        self.grey_btn.setEnabled(enabled)
        self.white_btn.setEnabled(enabled)
        
        if not enabled:
            self.page_label.setText("No PDF selected")
            self.zoom_label.setText("100%")
    
    def update_page_info(self):
        """Update page information display"""
        if self.pdf_viewer and self.current_pdf_path:
            total_pages = self.pdf_viewer.get_page_count()
            current_page_display = self.current_page + 1  # Display 1-based
            self.page_label.setText(f"Page {current_page_display} of {total_pages}")
            
            # Update navigation buttons
            self.prev_page_btn.setEnabled(self.current_page > 0)
            self.next_page_btn.setEnabled(self.current_page < total_pages - 1)
        else:
            self.page_label.setText("No PDF selected")
    
    def show_pdf_error(self, message: str):
        """Show an error message in the PDF viewer area"""
        self.clear_pdf_viewer()
        error_label = QLabel(f"❌ {message}")
        error_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        error_label.setStyleSheet("color: red; font-size: 14px;")
        self.pdf_viewer_layout.addWidget(error_label)
    
    def previous_page(self):
        """Go to previous page"""
        if self.pdf_viewer and self.current_page > 0:
            try:
                # Store current zoom level before navigation
                current_zoom = self.zoom_level
                
                self.current_page -= 1
                self.pdf_viewer.go_to_page(self.current_page)
                
                # Always restore zoom level after page navigation
                self.pdf_viewer.set_zoom(current_zoom)
                self.zoom_level = current_zoom
                self.zoom_label.setText(f"{int(current_zoom * 100)}%")
                
                self.update_page_info_with_exclusion()
                self.logger.info(f"Navigated to page {self.current_page + 1}, zoom maintained at {int(current_zoom * 100)}%")
            except RuntimeError as e:
                if "wrapped C/C++ object" in str(e):
                    self.logger.warning(f"PDF viewer widget was deleted, reloading PDF: {e}")
                    # Try to reload the PDF viewer
                    if self.current_pdf_path:
                        self.load_pdf_in_viewer(self.current_pdf_path)
                else:
                    raise e
    
    def next_page(self):
        """Go to next page"""
        if self.pdf_viewer:
            total_pages = self.pdf_viewer.get_page_count()
            if self.current_page < total_pages - 1:
                # Store current zoom level before navigation
                current_zoom = self.zoom_level
                
                self.current_page += 1
                self.pdf_viewer.go_to_page(self.current_page)
                
                # Always restore zoom level after page navigation
                self.pdf_viewer.set_zoom(current_zoom)
                self.zoom_level = current_zoom
                self.zoom_label.setText(f"{int(current_zoom * 100)}%")
                
                self.update_page_info_with_exclusion()
                self.logger.info(f"Navigated to page {self.current_page + 1}, zoom maintained at {int(current_zoom * 100)}%")
    
    def zoom_in(self):
        """Zoom in on the PDF"""
        if self.pdf_viewer:
            new_zoom = min(self.zoom_level * 1.25, 5.0)  # Max 500%
            self.zoom_level = new_zoom
            self.pdf_viewer.set_zoom(new_zoom)
            self.zoom_label.setText(f"{int(new_zoom * 100)}%")
            self.logger.debug(f"Zoom in: set to {new_zoom:.2f}")
    
    def zoom_out(self):
        """Zoom out on the PDF"""
        if self.pdf_viewer:
            new_zoom = max(self.zoom_level / 1.25, 0.25)  # Min 25%
            self.zoom_level = new_zoom
            self.pdf_viewer.set_zoom(new_zoom)
            self.zoom_label.setText(f"{int(new_zoom * 100)}%")
            self.logger.debug(f"Zoom out: set to {new_zoom:.2f}")
    
    def toggle_redact_mode(self):
        """Toggle redaction mode"""
        if self.redact_btn.isChecked():
            self.edit_mode = 'redaction'
            # Uncheck other modes
            self.highlight_btn.setChecked(False)
            self.text_btn.setChecked(False)
            
            if self.pdf_viewer:
                self.pdf_viewer.set_edit_mode('redaction')
        else:
            self.edit_mode = None
            if self.pdf_viewer:
                self.pdf_viewer.set_edit_mode(None)
    
    def toggle_highlight_mode(self):
        """Toggle highlight mode"""
        if self.highlight_btn.isChecked():
            self.edit_mode = 'highlight'
            # Uncheck other modes
            self.redact_btn.setChecked(False)
            self.text_btn.setChecked(False)
            
            # Set yellow color for highlighting
            highlight_color = QColor(255, 255, 0)  # Yellow
            if self.pdf_viewer:
                self.pdf_viewer.set_edit_mode('highlight')
                self.pdf_viewer.set_brush_color(highlight_color)
            
            # Update color button states to show yellow is selected
            self.black_btn.setChecked(False)
            self.grey_btn.setChecked(False)
            self.white_btn.setChecked(False)
        else:
            self.edit_mode = None
            if self.pdf_viewer:
                self.pdf_viewer.set_edit_mode(None)
    
    def toggle_text_mode(self):
        """Toggle text addition mode"""
        if self.text_btn.isChecked():
            self.edit_mode = 'text'
            # Uncheck other modes
            self.redact_btn.setChecked(False)
            self.highlight_btn.setChecked(False)
            
            if self.pdf_viewer:
                self.pdf_viewer.set_edit_mode('text')
        else:
            self.edit_mode = None
            if self.pdf_viewer:
                self.pdf_viewer.set_edit_mode(None)
    
    def undo_edit(self):
        """Undo the last edit"""
        if self.pdf_viewer:
            self.pdf_viewer.undo_last_edit()
    
    def toggle_page_exclusion(self):
        """Toggle exclusion of current page"""
        if self.pdf_viewer:
            self.pdf_viewer.toggle_page_exclusion()
            
            # Update button state
            is_excluded = self.pdf_viewer.is_page_excluded(self.current_page)
            self.exclude_page_btn.setChecked(is_excluded)
            
            # Update page info to show exclusion status
            self.update_page_info_with_exclusion()
    
    def update_page_info_with_exclusion(self):
        """Update page info including exclusion status"""
        if self.pdf_viewer and self.current_pdf_path:
            total_pages = self.pdf_viewer.get_page_count()
            current_page_display = self.current_page + 1  # Display 1-based
            
            # Check if current page is excluded
            is_excluded = self.pdf_viewer.is_page_excluded(self.current_page)
            excluded_count = len(self.pdf_viewer.get_excluded_pages())
            included_count = self.pdf_viewer.get_included_page_count()
            
            page_text = f"Page {current_page_display} of {total_pages}"
            if is_excluded:
                page_text += " (EXCLUDED)"
            
            if excluded_count > 0:
                page_text += f" • {included_count} pages will be faxed"
            
            self.page_label.setText(page_text)
            
            # Update navigation buttons
            self.prev_page_btn.setEnabled(self.current_page > 0)
            self.next_page_btn.setEnabled(self.current_page < total_pages - 1)
        else:
            self.page_label.setText("No PDF selected")
    
    def save_pdf_edits(self):
        """Save PDF edits"""
        if self.pdf_viewer and self.current_pdf_path:
            try:
                # Save the edited PDF
                if self.pdf_viewer.save_pdf():
                    QMessageBox.information(self, "Success", "PDF edits saved successfully!")
                    self.logger.info(f"Saved PDF edits for: {Path(self.current_pdf_path).name}")
                else:
                    QMessageBox.warning(self, "Save Failed", "Failed to save PDF edits.")
                    
            except Exception as e:
                self.logger.error(f"Error saving PDF edits: {e}")
                QMessageBox.critical(self, "Save Error", f"Error saving PDF edits:\n{str(e)}")
    
    def update_page_info_simple(self, pages):
        """Update page info with simple page count"""
        if pages != 'Unknown':
            self.page_label.setText(f"PDF loaded • {pages} pages")
        else:
            self.page_label.setText("PDF loaded")
    
    def on_pdf_edited(self, edit_info: Dict[str, Any]):
        """Handle PDF edits from the integrated viewer"""
        if self.current_pdf_path:
            # Store edit data for this PDF
            self.pdf_edit_data[self.current_pdf_path] = edit_info
            self.logger.info(f"Captured edit data for {Path(self.current_pdf_path).name}")
    
    def _save_current_pdf_edits(self):
        """Save current PDF edits to the edit data map"""
        if self.pdf_viewer and self.current_pdf_path:
            try:
                edit_data = self.pdf_viewer.get_edit_data()
                self.pdf_edit_data[self.current_pdf_path] = edit_data
                self.logger.info(f"Saved current PDF edits for {Path(self.current_pdf_path).name}")
            except Exception as e:
                self.logger.error(f"Error saving current PDF edits: {e}")
    
    def open_full_pdf_editor(self, pdf_path: str):
        """Open the full PDF editor dialog"""
        try:
            from pdf.pdf_viewer import PDFViewerDialog
            editor_dialog = PDFViewerDialog(pdf_path, self)
            
            # Connect to capture edits when dialog closes
            editor_dialog.edits_applied.connect(lambda edit_info: self.on_pdf_edited(edit_info))
            
            if editor_dialog.exec() == QDialog.DialogCode.Accepted:
                QMessageBox.information(self, "PDF Editor", "PDF editor closed. Any changes have been applied.")
                self.logger.info(f"PDF editor closed for: {Path(pdf_path).name}")
            
        except Exception as e:
            self.logger.error(f"Error opening full PDF editor: {e}")
            QMessageBox.critical(self, "Editor Error", f"Failed to open PDF editor:\n{str(e)}")
    
    def on_viewer_page_changed(self, page_number: int):
        """Handle page change from the integrated viewer"""
        self.current_page = page_number
        self.update_page_info()
    
    def on_viewer_zoom_changed(self, zoom_level: float):
        """Handle zoom change from the integrated viewer"""
        self.zoom_level = zoom_level
        self.zoom_label.setText(f"{int(zoom_level * 100)}%")
        self.logger.debug(f"Zoom level synchronized: {zoom_level:.2f}")
    
    def update_brush_size(self, size: int):
        """Update brush size for PDF editing"""
        self.brush_size_label.setText(f"{size}px")
        if self.pdf_viewer:
            self.pdf_viewer.set_brush_size(size)
    
    def set_brush_color(self, color: QColor):
        """Set brush color for PDF editing"""
        if self.pdf_viewer:
            self.pdf_viewer.set_brush_color(color)
        
        # Update button states to show which color is selected
        self.black_btn.setChecked(color == QColor(0, 0, 0))
        self.grey_btn.setChecked(color == QColor(128, 128, 128))
        self.white_btn.setChecked(color == QColor(255, 255, 255))
    
    def load_sender_info(self):
        """Load sender information from settings"""
        try:
            from core.settings import get_settings
            settings = get_settings()
            sender_info = settings.get_sender_info()
            
            # Populate sender fields
            self.from_name_edit.setText(sender_info.get('from_name', ''))
            self.from_company_edit.setText(sender_info.get('from_company', 'The Spine Hospital Louisiana'))
            self.from_phone_edit.setText(sender_info.get('from_phone', '(225) 906-4805'))
            
            self.logger.info("Loaded sender information from settings")
            
        except Exception as e:
            self.logger.error(f"Error loading sender info: {e}")
            # Set defaults if loading fails
            self.from_company_edit.setText('The Spine Hospital Louisiana')
            self.from_phone_edit.setText('(225) 906-4805')
    
    def save_sender_info(self):
        """Save sender information to settings"""
        try:
            from core.settings import get_settings
            settings = get_settings()
            
            # Save sender information
            settings.set_sender_info(
                from_name=self.from_name_edit.text().strip(),
                from_company=self.from_company_edit.text().strip(),
                from_phone=self.from_phone_edit.text().strip()
            )
            
            # Save settings to file
            settings.save_settings()
            
            QMessageBox.information(self, "Success", "Sender information saved as default!")
            self.logger.info("Saved sender information to settings")
            
        except Exception as e:
            self.logger.error(f"Error saving sender info: {e}")
            QMessageBox.warning(self, "Error", f"Failed to save sender information: {str(e)}")
    
    def on_contact_selected(self):
        """Handle contact selection and auto-populate recipient fields"""
        current_item = self.contact_list.currentItem()
        if current_item:
            contact = current_item.data(Qt.ItemDataRole.UserRole)
            
            # Populate contact form
            self.populate_contact_form(contact)
            
            # Auto-populate recipient fields in cover page tab
            self.to_edit.setText(contact.name or "")
            self.fax_edit.setText(contact.fax_number or "")
            
            self.logger.info(f"Selected contact: {contact.name} - {contact.fax_number}")
            
            # Update cover page preview when contact is selected
            self.update_cover_preview()
    
    def update_cover_preview(self):
        """Update the visual cover page preview (text preview removed)"""
        # This method now just calls the visual preview update
        self.update_cover_visual_preview()
    
    def generate_cover_pdf_preview(self):
        """Generate a PDF preview of the cover page"""
        try:
            # Create cover page details from current form data
            cover_details = CoverPageDetails(
                to=self.to_edit.text().strip() or None,
                from_field=self.from_name_edit.text().strip() or None,
                company=self.from_company_edit.text().strip() or None,
                fax=self.fax_edit.text().strip() or None,
                phone=self.from_phone_edit.text().strip() or None,
                re=self.re_edit.text().strip() or None,
                comments=self.comments_edit.toPlainText().strip() or None,
                urgent=self.urgent_checkbox.isChecked(),
                for_review=self.for_review_checkbox.isChecked(),
                please_comment=self.please_comment_checkbox.isChecked(),
                please_reply=self.please_reply_checkbox.isChecked()
            )
            
            # Generate PDF preview
            preview_path = "cover_page_preview.pdf"
            success = self.cover_page_generator.generate_cover_page(
                cover_details=cover_details,
                output_path=preview_path,
                page_count=len(self.selected_pdfs)
            )
            
            if success:
                # Open the PDF preview
                import subprocess
                subprocess.run(["start", preview_path], shell=True, check=False)
                QMessageBox.information(self, "Preview Generated", f"Cover page preview saved as: {preview_path}")
            else:
                QMessageBox.warning(self, "Preview Failed", "Failed to generate PDF preview.")
                
        except Exception as e:
            self.logger.error(f"Error generating PDF preview: {e}")
            QMessageBox.critical(self, "Preview Error", f"Error generating PDF preview:\n{str(e)}")
    
    def schedule_preview_update(self):
        """Schedule a preview update after a delay (for text fields)"""
        self.preview_update_timer.stop()
        self.preview_update_timer.start(1000)  # 1 second delay
    
    def update_cover_previews(self):
        """Update both text and visual cover page previews"""
        self.update_cover_preview()  # Update text preview
        self.update_cover_visual_preview()  # Update visual preview
    
    def update_cover_visual_preview(self):
        """Update the visual cover page preview"""
        try:
            # Create cover page details from current form data
            cover_details = CoverPageDetails(
                to=self.to_edit.text().strip() or None,
                from_field=self.from_name_edit.text().strip() or None,
                company=self.from_company_edit.text().strip() or None,
                fax=self.fax_edit.text().strip() or None,
                phone=self.from_phone_edit.text().strip() or None,
                re=self.re_edit.text().strip() or None,
                comments=self.comments_edit.toPlainText().strip() or None,
                urgent=self.urgent_checkbox.isChecked(),
                for_review=self.for_review_checkbox.isChecked(),
                please_comment=self.please_comment_checkbox.isChecked(),
                please_reply=self.please_reply_checkbox.isChecked()
            )
            
            # Generate temporary PDF for preview
            temp_preview_path = "temp_cover_preview.pdf"
            logo_path = r"c:\mcfaxapp\sholalogo.jpg"
            
            success = self.cover_page_generator.generate_cover_page(
                cover_details=cover_details,
                output_path=temp_preview_path,
                page_count=len(self.selected_pdfs),
                logo_path=logo_path if os.path.exists(logo_path) else None
            )
            
            if success:
                # Convert PDF to image for display
                self.convert_pdf_to_preview_image(temp_preview_path)
                
                # Clean up temporary file
                try:
                    os.remove(temp_preview_path)
                except:
                    pass
            else:
                self.cover_preview_label.setText("Error generating cover page preview")
                
        except Exception as e:
            self.logger.error(f"Error updating visual cover preview: {e}")
            self.cover_preview_label.setText(f"Preview error: {str(e)}")
    
    def convert_pdf_to_preview_image(self, pdf_path: str):
        """Convert PDF to image for preview display"""
        try:
            # Try to use PyMuPDF for PDF to image conversion
            try:
                import fitz  # PyMuPDF
                
                # Open PDF
                doc = fitz.open(pdf_path)
                page = doc[0]  # First page only
                
                # Render page to image at appropriate resolution
                # Scale to fit preview area while maintaining aspect ratio
                available_width = self.cover_preview_scroll.width() - 20  # Account for margins
                available_height = self.cover_preview_scroll.height() - 20
                
                # Calculate scale factor to fit in preview area
                page_rect = page.rect
                scale_x = available_width / page_rect.width
                scale_y = available_height / page_rect.height
                scale = min(scale_x, scale_y, 1.0)  # Don't scale up beyond 100%
                
                # Create transformation matrix
                mat = fitz.Matrix(scale, scale)
                
                # Render to pixmap
                pix = page.get_pixmap(matrix=mat)
                
                # Convert to QPixmap
                img_data = pix.tobytes("ppm")
                qpixmap = QPixmap()
                qpixmap.loadFromData(img_data)
                
                # Display in preview label
                self.cover_preview_label.setPixmap(qpixmap)
                self.cover_preview_label.resize(qpixmap.size())
                
                doc.close()
                
                self.logger.info("Cover page visual preview updated successfully")
                
            except ImportError:
                # Fallback: show message that PyMuPDF is needed for visual preview
                self.cover_preview_label.setText(
                    "Visual preview requires PyMuPDF\n"
                    "Install with: pip install PyMuPDF\n\n"
                    "PDF generated successfully at:\n" + pdf_path
                )
                
        except Exception as e:
            self.logger.error(f"Error converting PDF to preview image: {e}")
            self.cover_preview_label.setText(f"Preview conversion error: {str(e)}")
    
    # Final preview methods for the preview tab
    
    def generate_final_preview(self):
        """Generate the final combined PDF preview (cover page + selected PDFs)"""
        try:
            # Validate that we have the required data
            if not self.selected_pdfs:
                QMessageBox.warning(self, "No PDFs", "No PDF files selected to preview.")
                return
            
            current_contact = self.contact_list.currentItem()
            if not current_contact:
                QMessageBox.warning(self, "No Recipient", "Please select a recipient first.")
                return
            
            # Start progress button animation
            self.generate_preview_btn.start_processing()
            
            # Clear any existing preview first to release file locks
            self.clear_final_preview()
            
            # Update progress button
            self.generate_preview_btn.set_progress(10)
            
            # Create cover page details
            cover_details = CoverPageDetails(
                to=self.to_edit.text().strip() or None,
                from_field=self.from_name_edit.text().strip() or None,
                company=self.from_company_edit.text().strip() or None,
                fax=self.fax_edit.text().strip() or None,
                phone=self.from_phone_edit.text().strip() or None,
                re=self.re_edit.text().strip() or None,
                comments=self.comments_edit.toPlainText().strip() or None,
                urgent=self.urgent_checkbox.isChecked(),
                for_review=self.for_review_checkbox.isChecked(),
                please_comment=self.please_comment_checkbox.isChecked(),
                please_reply=self.please_reply_checkbox.isChecked()
            )
            
            # Generate cover page
            self.generate_preview_btn.set_progress(30)
            
            cover_page_path = "temp_final_cover.pdf"
            logo_path = r"c:\mcfaxapp\sholalogo.jpg"
            
            cover_success = self.cover_page_generator.generate_cover_page(
                cover_details=cover_details,
                output_path=cover_page_path,
                page_count=len(self.selected_pdfs),
                logo_path=logo_path if os.path.exists(logo_path) else None
            )
            
            if not cover_success:
                self.generate_preview_btn.finish_processing(success=False)
                QMessageBox.warning(self, "Cover Page Error", "Failed to generate cover page.")
                return
            
            # Combine cover page with selected PDFs
            self.generate_preview_btn.set_progress(60)
            
            final_pdf_path = "temp_final_preview.pdf"
            combined_success = self.combine_pdfs_for_preview(cover_page_path, self.selected_pdfs, final_pdf_path)
            
            if not combined_success:
                self.generate_preview_btn.finish_processing(success=False)
                QMessageBox.warning(self, "Combine Error", "Failed to combine PDFs.")
                return
            
            # Load the final PDF in the preview viewer
            self.generate_preview_btn.set_progress(90)
            
            self.load_final_preview(final_pdf_path)
            
            # Clean up temporary cover page
            try:
                os.remove(cover_page_path)
            except:
                pass
            
            # Complete progress
            self.generate_preview_btn.set_progress(100)
            self.generate_preview_btn.finish_processing(success=True)
            
            self.logger.info("Final preview generated successfully")
            
        except Exception as e:
            self.logger.error(f"Error generating final preview: {e}")
            self.generate_preview_btn.finish_processing(success=False)
            self.status_label.setText(f"Preview generation failed: {str(e)}")
            QMessageBox.critical(self, "Preview Error", f"Failed to generate final preview:\n{str(e)}")
    
    def combine_pdfs_for_preview(self, cover_page_path: str, pdf_paths: List[str], output_path: str) -> bool:
        """Combine cover page and selected PDFs into a single preview PDF (with edits applied)"""
        try:
            # First, ensure any existing preview file is properly closed and removed
            if os.path.exists(output_path):
                # Clear the final preview to release file locks
                self.clear_final_preview()
                
                # Try to remove the existing file with retry logic
                import time
                max_attempts = 5
                for attempt in range(max_attempts):
                    try:
                        os.remove(output_path)
                        self.logger.debug(f"Successfully removed existing preview file: {output_path}")
                        break
                    except PermissionError:
                        if attempt < max_attempts - 1:
                            self.logger.warning(f"File locked, retrying in 0.5 seconds (attempt {attempt + 1}/{max_attempts})")
                            time.sleep(0.5)
                        else:
                            self.logger.error(f"Could not remove existing preview file after {max_attempts} attempts: {output_path}")
                            return False
                    except Exception as e:
                        self.logger.error(f"Error removing existing preview file {output_path}: {e}")
                        return False
            
            # Save current PDF edits before generating preview
            self._save_current_pdf_edits()
            
            # Check if we have any PDF edits to apply for preview
            if self.pdf_edit_data:
                self.logger.info(f"Applying edits to preview - found edit data for {len(self.pdf_edit_data)} PDFs")
                
                # Use the PDF processor's combine_pdfs_with_edits method for preview
                success = self.pdf_processor.combine_pdfs_with_edits(
                    pdf_files=[cover_page_path] + pdf_paths,
                    output_path=output_path,
                    edit_data_map=self.pdf_edit_data,
                    excluded_pages=None  # Page exclusions are handled within edit data
                )
                
                if success:
                    self.logger.info("Successfully combined preview PDFs with edits applied")
                    return True
                else:
                    error_msg = "Failed to combine preview PDFs with edits applied"
                    self.logger.error(error_msg)
                    from PyQt6.QtWidgets import QMessageBox
                    QMessageBox.critical(
                        self, 
                        "Preview Generation Failed", 
                        f"{error_msg}\n\nCheck logs for detailed error information.\nOperation stopped."
                    )
                    return False
            else:
                self.logger.info("No PDF edits found for preview, using standard combination")
            
            # Standard PDF combination (no edits)
            try:
                import fitz  # PyMuPDF
                
                # Create new PDF document
                combined_doc = fitz.open()
                
                # Add cover page
                cover_doc = fitz.open(cover_page_path)
                combined_doc.insert_pdf(cover_doc)
                cover_doc.close()
                
                # Add each selected PDF
                for pdf_path in pdf_paths:
                    try:
                        pdf_doc = fitz.open(pdf_path)
                        combined_doc.insert_pdf(pdf_doc)
                        pdf_doc.close()
                    except Exception as e:
                        self.logger.warning(f"Error adding PDF {pdf_path}: {e}")
                        continue
                
                # Save combined PDF
                combined_doc.save(output_path)
                combined_doc.close()
                
                return True
                
            except ImportError:
                # Fallback: just copy the cover page as preview
                try:
                    import shutil
                    shutil.copy2(cover_page_path, output_path)
                    return True
                except Exception as e:
                    self.logger.error(f"Fallback copy failed: {e}")
                    return False
                    
        except Exception as e:
            self.logger.error(f"Error combining PDFs for preview: {e}")
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.critical(
                self, 
                "Preview Generation Error", 
                f"Error combining PDFs for preview:\n\n{str(e)}\n\nOperation stopped."
            )
            return False
    
    def load_final_preview(self, pdf_path: str):
        """Load the final combined PDF in the preview viewer"""
        try:
            # Clear existing preview
            self.clear_final_preview()
            
            # Hide placeholder
            self.final_preview_placeholder.hide()
            
            # Create integrated PDF viewer for final preview
            self.final_preview_viewer = IntegratedPDFViewer(pdf_path)
            
            # Connect signals
            self.final_preview_viewer.page_changed.connect(self.on_final_preview_page_changed)
            self.final_preview_viewer.zoom_changed.connect(self.on_final_preview_zoom_changed)
            
            # Add to layout
            self.final_preview_layout.addWidget(self.final_preview_viewer)
            
            # Enable preview controls
            self.enable_final_preview_controls(True)
            
            # Store the path for cleanup later
            self.final_preview_pdf_path = pdf_path
            
            # Set initial zoom to fit the panel
            self.fit_preview_to_panel()
            
            # Update page info
            self.update_final_preview_page_info()
            
            self.logger.info(f"Loaded final preview: {pdf_path}")
            
        except Exception as e:
            self.logger.error(f"Error loading final preview: {e}")
            self.show_final_preview_error(f"Error loading preview: {str(e)}")
    
    def clear_final_preview(self):
        """Clear the final preview viewer"""
        # Remove existing viewer widget
        for i in reversed(range(self.final_preview_layout.count())):
            child = self.final_preview_layout.itemAt(i).widget()
            if child and child != self.final_preview_placeholder:
                child.setParent(None)
        
        # Show placeholder
        self.final_preview_placeholder.show()
        
        # Disable controls
        self.enable_final_preview_controls(False)
        
        # Clean up temporary file
        if self.final_preview_pdf_path and os.path.exists(self.final_preview_pdf_path):
            try:
                os.remove(self.final_preview_pdf_path)
            except:
                pass
        
        # Reset state
        self.final_preview_pdf_path = None
        self.final_preview_viewer = None
        self.final_preview_current_page = 0
        self.final_preview_zoom_level = 1.0
    
    def enable_final_preview_controls(self, enabled: bool):
        """Enable or disable final preview controls"""
        self.preview_prev_btn.setEnabled(enabled)
        self.preview_next_btn.setEnabled(enabled)
        self.preview_zoom_out_btn.setEnabled(enabled)
        self.preview_zoom_in_btn.setEnabled(enabled)
        
        if not enabled:
            self.preview_page_label.setText("No preview generated")
            self.preview_zoom_label.setText("100%")
    
    def update_final_preview_page_info(self):
        """Update final preview page information"""
        if self.final_preview_viewer and self.final_preview_pdf_path:
            total_pages = self.final_preview_viewer.get_page_count()
            current_page_display = self.final_preview_current_page + 1  # Display 1-based
            self.preview_page_label.setText(f"Page {current_page_display} of {total_pages}")
            
            # Update navigation buttons
            self.preview_prev_btn.setEnabled(self.final_preview_current_page > 0)
            self.preview_next_btn.setEnabled(self.final_preview_current_page < total_pages - 1)
        else:
            self.preview_page_label.setText("No preview generated")
    
    def show_final_preview_error(self, message: str):
        """Show an error message in the final preview area"""
        self.clear_final_preview()
        error_label = QLabel(f"❌ {message}")
        error_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        error_label.setStyleSheet("color: red; font-size: 14px;")
        self.final_preview_layout.addWidget(error_label)
    
    
    def create_simple_pdf_viewer(self, pdf_path: str):
        """Create a simple PDF viewer using basic image display"""
        try:
            import fitz  # PyMuPDF
            
            # Open PDF document
            self.final_preview_pdf_doc = fitz.open(pdf_path)
            self.final_preview_total_pages = len(self.final_preview_pdf_doc)
            
            # Create a simple label for displaying PDF pages
            self.final_preview_label = QLabel()
            self.final_preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.final_preview_label.setStyleSheet("""
                QLabel {
                    background-color: white;
                    border: 1px solid #ddd;
                    margin: 5px;
                }
            """)
            
            # Add to layout
            self.final_preview_layout.addWidget(self.final_preview_label)
            
            # Set initial zoom level to fit panel
            self.final_preview_zoom_level = 0.6  # Start at 60% to fit better
            
            self.logger.info(f"Created simple PDF viewer for {self.final_preview_total_pages} pages")
            
        except ImportError:
            self.show_final_preview_error("PyMuPDF is required for PDF preview. Please install with: pip install PyMuPDF")
        except Exception as e:
            self.logger.error(f"Error creating simple PDF viewer: {e}")
            self.show_final_preview_error(f"Error creating PDF viewer: {str(e)}")
    
    def load_preview_page(self, page_number: int):
        """Load and display a specific page in the simple PDF viewer"""
        try:
            if not hasattr(self, 'final_preview_pdf_doc') or not self.final_preview_pdf_doc:
                return
            
            if 0 <= page_number < self.final_preview_total_pages:
                # Get the page
                page = self.final_preview_pdf_doc[page_number]
                
                # Calculate zoom to fit panel
                available_width = self.final_preview_container.width() - 60  # Account for margins and scrollbars
                available_height = self.final_preview_container.height() - 60
                
                # Get page dimensions
                page_rect = page.rect
                
                # Calculate scale factors
                scale_x = available_width / page_rect.width if page_rect.width > 0 else 1.0
                scale_y = available_height / page_rect.height if page_rect.height > 0 else 1.0
                
                # Use the smaller scale to ensure the page fits completely, but don't go below 0.3 or above 1.0
                auto_fit_scale = max(0.3, min(scale_x, scale_y, 1.0))
                
                # Use the current zoom level or auto-fit if this is the first load
                if not hasattr(self, '_preview_zoom_set'):
                    self.final_preview_zoom_level = auto_fit_scale
                    self._preview_zoom_set = True
                
                # Create transformation matrix
                mat = fitz.Matrix(self.final_preview_zoom_level, self.final_preview_zoom_level)
                
                # Render page to pixmap
                pix = page.get_pixmap(matrix=mat)
                
                # Convert to QPixmap
                img_data = pix.tobytes("ppm")
                qpixmap = QPixmap()
                qpixmap.loadFromData(img_data)
                
                # Display in label
                self.final_preview_label.setPixmap(qpixmap)
                self.final_preview_label.resize(qpixmap.size())
                
                # Update zoom label
                self.preview_zoom_label.setText(f"{int(self.final_preview_zoom_level * 100)}%")
                
                self.logger.info(f"Loaded preview page {page_number + 1} at {int(self.final_preview_zoom_level * 100)}% zoom")
                
        except Exception as e:
            self.logger.error(f"Error loading preview page {page_number}: {e}")
            self.show_final_preview_error(f"Error loading page: {str(e)}")
    
    def preview_previous_page(self):
        """Go to previous page in final preview"""
        if self.final_preview_viewer and self.final_preview_current_page > 0:
            self.final_preview_current_page -= 1
            self.final_preview_viewer.go_to_page(self.final_preview_current_page)
            self.update_final_preview_page_info()
    
    def preview_next_page(self):
        """Go to next page in final preview"""
        if self.final_preview_viewer:
            total_pages = self.final_preview_viewer.get_page_count()
            if self.final_preview_current_page < total_pages - 1:
                self.final_preview_current_page += 1
                self.final_preview_viewer.go_to_page(self.final_preview_current_page)
                self.update_final_preview_page_info()
    
    def preview_zoom_in(self):
        """Zoom in on the final preview"""
        if self.final_preview_viewer:
            self.final_preview_zoom_level = min(self.final_preview_zoom_level * 1.25, 5.0)  # Max 500%
            self.final_preview_viewer.set_zoom(self.final_preview_zoom_level)
            self.preview_zoom_label.setText(f"{int(self.final_preview_zoom_level * 100)}%")
    
    def preview_zoom_out(self):
        """Zoom out on the final preview"""
        if self.final_preview_viewer:
            self.final_preview_zoom_level = max(self.final_preview_zoom_level / 1.25, 0.25)  # Min 25%
            self.final_preview_viewer.set_zoom(self.final_preview_zoom_level)
            self.preview_zoom_label.setText(f"{int(self.final_preview_zoom_level * 100)}%")
    
    def update_final_preview_page_info(self):
        """Update final preview page information"""
        if hasattr(self, 'final_preview_pdf_doc') and self.final_preview_pdf_doc:
            current_page_display = self.final_preview_current_page + 1  # Display 1-based
            self.preview_page_label.setText(f"Page {current_page_display} of {self.final_preview_total_pages}")
            
            # Update navigation buttons
            self.preview_prev_btn.setEnabled(self.final_preview_current_page > 0)
            self.preview_next_btn.setEnabled(self.final_preview_current_page < self.final_preview_total_pages - 1)
        else:
            self.preview_page_label.setText("No preview generated")
    
    def on_final_preview_page_changed(self, page_number: int):
        """Handle page change from the final preview viewer"""
        self.final_preview_current_page = page_number
        self.update_final_preview_page_info()
    
    def on_final_preview_zoom_changed(self, zoom_level: float):
        """Handle zoom change from the final preview viewer"""
        self.final_preview_zoom_level = zoom_level
        self.preview_zoom_label.setText(f"{int(zoom_level * 100)}%")
    
    def fit_preview_to_panel(self):
        """Set the preview zoom to fit the panel width"""
        if not self.final_preview_viewer:
            return
        
        try:
            # Get the available width of the preview panel
            available_width = self.final_preview_container.width() - 40  # Account for margins and scrollbars
            available_height = self.final_preview_container.height() - 40
            
            # Get the first page to calculate dimensions
            if self.final_preview_viewer.page_images:
                first_page = self.final_preview_viewer.page_images[0]
                page_width = first_page.width()
                page_height = first_page.height()
                
                # Calculate scale factors
                scale_x = available_width / page_width if page_width > 0 else 1.0
                scale_y = available_height / page_height if page_height > 0 else 1.0
                
                # Use the smaller scale to ensure the page fits completely
                fit_scale = min(scale_x, scale_y, 1.0)  # Don't scale up beyond 100%
                
                # Apply the fit scale
                if fit_scale < 1.0:  # Only scale down if needed
                    self.final_preview_zoom_level = fit_scale
                    self.final_preview_viewer.set_zoom(fit_scale)
                    self.preview_zoom_label.setText(f"{int(fit_scale * 100)}%")
                    
                    self.logger.info(f"Set preview zoom to fit panel: {int(fit_scale * 100)}%")
                
        except Exception as e:
            self.logger.error(f"Error fitting preview to panel: {e}")
            # Fallback to a reasonable default zoom
            self.final_preview_zoom_level = 0.75  # 75%
            if self.final_preview_viewer:
                self.final_preview_viewer.set_zoom(0.75)
            self.preview_zoom_label.setText("75%")
    
    def clear_final_preview(self):
        """Clear the final preview viewer"""
        # First, close and clean up the viewer to release file locks
        if self.final_preview_viewer:
            try:
                # Close the PDF document in the viewer
                if hasattr(self.final_preview_viewer, 'pdf_document') and self.final_preview_viewer.pdf_document:
                    self.final_preview_viewer.pdf_document.close()
                
                # Remove the viewer widget
                self.final_preview_viewer.setParent(None)
                self.final_preview_viewer = None
                
                # Force garbage collection to release file handles
                import gc
                gc.collect()
                
            except Exception as e:
                self.logger.warning(f"Error closing preview viewer: {e}")
        
        # Remove existing viewer widgets
        for i in reversed(range(self.final_preview_layout.count())):
            child = self.final_preview_layout.itemAt(i).widget()
            if child and child != self.final_preview_placeholder:
                child.setParent(None)
        
        # Show placeholder
        self.final_preview_placeholder.show()
        
        # Disable controls
        self.enable_final_preview_controls(False)
        
        # Clean up PDF document
        if hasattr(self, 'final_preview_pdf_doc') and self.final_preview_pdf_doc:
            try:
                self.final_preview_pdf_doc.close()
            except:
                pass
        
        # Clean up temporary file with retry logic
        if self.final_preview_pdf_path and os.path.exists(self.final_preview_pdf_path):
            self.cleanup_temp_file(self.final_preview_pdf_path)
        
        # Reset state
        self.final_preview_pdf_path = None
        self.final_preview_pdf_doc = None
        self.final_preview_current_page = 0
        self.final_preview_zoom_level = 1.0
        self.final_preview_total_pages = 0
        if hasattr(self, '_preview_zoom_set'):
            delattr(self, '_preview_zoom_set')
    
    def cleanup_temp_file(self, file_path: str):
        """Clean up temporary file with retry logic"""
        import time
        max_attempts = 3
        
        for attempt in range(max_attempts):
            try:
                os.remove(file_path)
                self.logger.debug(f"Successfully removed temporary file: {file_path}")
                return
            except PermissionError:
                if attempt < max_attempts - 1:
                    self.logger.warning(f"File locked, retrying in 0.5 seconds (attempt {attempt + 1}/{max_attempts})")
                    time.sleep(0.5)
                else:
                    self.logger.warning(f"Could not remove temporary file after {max_attempts} attempts: {file_path}")
            except Exception as e:
                self.logger.warning(f"Error removing temporary file {file_path}: {e}")
                break
    
    # XML Generation and FaxFinder Submission Methods
    
    def generate_final_pdf(self, fax_job: FaxJob) -> Optional[str]:
        """Generate the final combined PDF (cover page + selected PDFs with edits applied)"""
        try:
            from datetime import datetime
            
            # Save current PDF edits before generating final PDF
            self._save_current_pdf_edits()
            
            # Create output directories
            processed_dir = Path("processed")
            processed_dir.mkdir(exist_ok=True)
            
            temp_dir = Path("temp")
            temp_dir.mkdir(exist_ok=True)
            
            # Generate timestamp for unique filenames
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # Generate cover page
            cover_page_path = temp_dir / f"cover_{timestamp}.pdf"
            logo_path = Path("SholaLogo.JPG")
            
            cover_success = self.cover_page_generator.generate_cover_page(
                cover_details=fax_job.cover_page_details,
                output_path=str(cover_page_path),
                page_count=len(self.selected_pdfs),
                logo_path=str(logo_path) if logo_path.exists() else None
            )
            
            if not cover_success:
                self.logger.error("Failed to generate cover page")
                return None
            
            # Combine cover page with selected PDFs (applying edits if any)
            final_pdf_path = processed_dir / f"fax_job_{timestamp}.pdf"
            
            # Check if we have any PDF edits to apply
            if self.pdf_edit_data:
                self.logger.info(f"Found edit data for {len(self.pdf_edit_data)} PDFs, applying edits...")
                
                # Use the new combine_pdfs_with_edits method
                success = self.pdf_processor.combine_pdfs_with_edits(
                    pdf_files=[str(cover_page_path)] + self.selected_pdfs,
                    output_path=str(final_pdf_path),
                    edit_data_map=self.pdf_edit_data,
                    excluded_pages=None  # Page exclusions are handled within edit data
                )
                
                if not success:
                    error_msg = "Failed to combine PDFs with edits applied"
                    self.logger.error(error_msg)
                    from PyQt6.QtWidgets import QMessageBox
                    QMessageBox.critical(
                        self, 
                        "Final PDF Generation Failed", 
                        f"{error_msg}\n\nCheck logs for detailed error information.\nOperation stopped."
                    )
                    return None
                    
            else:
                # No edits, use standard PDF combination
                self.logger.info("No PDF edits found, using standard combination...")
                
                try:
                    import fitz  # PyMuPDF
                    
                    # Create new PDF document
                    combined_doc = fitz.open()
                    
                    # Add cover page
                    cover_doc = fitz.open(str(cover_page_path))
                    combined_doc.insert_pdf(cover_doc)
                    cover_doc.close()
                    
                    # Add each selected PDF
                    for pdf_path in self.selected_pdfs:
                        try:
                            pdf_doc = fitz.open(pdf_path)
                            combined_doc.insert_pdf(pdf_doc)
                            pdf_doc.close()
                            self.logger.info(f"Added PDF to final document: {Path(pdf_path).name}")
                        except Exception as e:
                            self.logger.warning(f"Error adding PDF {pdf_path}: {e}")
                            continue
                    
                    # Save combined PDF
                    combined_doc.save(str(final_pdf_path))
                    combined_doc.close()
                    
                except ImportError:
                    self.logger.error("PyMuPDF is required for PDF combination")
                    return None
            
            # Clean up temporary cover page
            self.cleanup_temp_file(str(cover_page_path))
            
            self.logger.info(f"Generated final PDF: {final_pdf_path}")
            return str(final_pdf_path)
                
        except Exception as e:
            self.logger.error(f"Error generating final PDF: {e}")
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.critical(
                self, 
                "Final PDF Generation Error", 
                f"Error generating final PDF:\n\n{str(e)}\n\nOperation stopped."
            )
            return None
    
    def generate_xml_file(self, fax_job: FaxJob, pdf_path: str) -> Optional[str]:
        """Generate XML file for local storage (without base64 content)"""
        try:
            from datetime import datetime
            
            # Ensure XML directory exists relative to current working directory
            xml_dir = Path.cwd() / "xml"
            xml_dir.mkdir(parents=True, exist_ok=True)
            
            # Generate timestamp for unique filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            xml_filename = f"fax_job_{timestamp}.xml"
            xml_path = xml_dir / xml_filename
            
            # Get selected contact
            current_contact = self.contact_list.currentItem()
            if not current_contact:
                self.logger.error("No contact selected for XML generation")
                return None
            
            contact = current_contact.data(Qt.ItemDataRole.UserRole)
            
            # Use the generate_fax_xml method for local storage (no base64)
            success = self.xml_generator.generate_fax_xml(
                fax_job=fax_job,
                contact=contact,
                pdf_file_path=pdf_path,
                output_path=str(xml_path)
            )
            
            if success:
                self.logger.info(f"Generated XML file for local storage: {xml_path}")
                return str(xml_path)
            else:
                self.logger.error("Failed to generate XML file")
                return None
                
        except Exception as e:
            self.logger.error(f"Error generating XML file: {e}")
            return None
    
    def generate_xml_file_with_base64(self, fax_job: FaxJob, pdf_path: str) -> Optional[str]:
        """Generate XML file for local storage (WITH base64 content)"""
        try:
            from datetime import datetime
            
            # Ensure XML directory exists relative to current working directory
            xml_dir = Path.cwd() / "xml"
            xml_dir.mkdir(parents=True, exist_ok=True)
            
            # Generate timestamp for unique filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            xml_filename = f"fax_job_{timestamp}.xml"
            xml_path = xml_dir / xml_filename
            
            # Get selected contact
            current_contact = self.contact_list.currentItem()
            if not current_contact:
                self.logger.error("No contact selected for XML generation")
                return None
            
            contact = current_contact.data(Qt.ItemDataRole.UserRole)
            
            # Use the generate_faxfinder_xml method to get XML WITH base64 content
            xml_content = self.xml_generator.generate_faxfinder_xml(
                fax_job=fax_job,
                contact=contact,
                pdf_file_path=pdf_path
            )
            
            if xml_content:
                # Save the XML content to file
                with open(xml_path, 'w', encoding='utf-8') as f:
                    f.write(xml_content)
                
                self.logger.info(f"Generated XML file with base64 content: {xml_path}")
                return str(xml_path)
            else:
                self.logger.error("Failed to generate XML content with base64")
                return None
                
        except Exception as e:
            self.logger.error(f"Error generating XML file with base64: {e}")
            return None
    
    def calculate_page_count(self, pdf_path: str) -> int:
        """Calculate the total page count of the final PDF"""
        try:
            import fitz  # PyMuPDF
            
            doc = fitz.open(pdf_path)
            page_count = len(doc)
            doc.close()
            
            return page_count
            
        except ImportError:
            self.logger.warning("PyMuPDF not available for page counting")
            return 0
        except Exception as e:
            self.logger.error(f"Error calculating page count: {e}")
            return 0
    
    def submit_to_faxfinder(self, fax_job: FaxJob, pdf_path: str) -> Dict[str, Any]:
        """Submit the fax job to FaxFinder using the correct API method"""
        try:
            from core.settings import get_settings
            from fax.faxfinder_api import FaxFinderAPI
            
            # Get FaxFinder settings
            settings = get_settings()
            faxfinder_settings = settings.get_faxfinder_settings()
            
            # Check if FaxFinder is configured
            if not faxfinder_settings.get('host'):
                return {
                    'success': False,
                    'error': 'FaxFinder not configured. Please configure FaxFinder settings first.'
                }
            
            # Create FaxFinder API client
            api = FaxFinderAPI(
                host=faxfinder_settings['host'],
                username=faxfinder_settings['username'],
                password=faxfinder_settings['password'],
                use_https=faxfinder_settings.get('use_https', False)
            )
            
            # Test connection first
            connection_test = api.test_connection()
            if not connection_test['success']:
                return {
                    'success': False,
                    'error': f'Cannot connect to FaxFinder: {connection_test.get("error", "Unknown connection error")}'
                }
            
            # Get selected contact
            current_contact = self.contact_list.currentItem()
            if not current_contact:
                return {
                    'success': False,
                    'error': 'No contact selected for submission'
                }
            
            contact = current_contact.data(Qt.ItemDataRole.UserRole)
            
            # DEBUG: Verify PDF file exists and is readable
            if not os.path.exists(pdf_path):
                self.logger.error(f"PDF file does not exist: {pdf_path}")
                return {
                    'success': False,
                    'error': f'PDF file not found: {pdf_path}'
                }
            
            # DEBUG: Check file size
            file_size = os.path.getsize(pdf_path)
            self.logger.info(f"PDF file size: {file_size} bytes ({file_size/1024/1024:.1f} MB)")
            
            # DEBUG: Test base64 conversion locally before sending
            try:
                self.logger.info("=== DEBUG: Testing Base64 conversion locally ===")
                with open(pdf_path, 'rb') as test_file:
                    pdf_data = test_file.read()
                    pdf_base64_encoded = base64.b64encode(pdf_data).decode('utf-8')
                    self.logger.info(f"Base64 conversion successful: {len(pdf_base64_encoded)} characters")
                    self.logger.info(f"Base64 sample: {pdf_base64_encoded[:100]}...")
            except Exception as base64_error:
                self.logger.error(f"Base64 conversion failed: {base64_error}")
                return {
                    'success': False,
                    'error': f'Base64 conversion failed: {str(base64_error)}'
                }
            
            # DEBUG: Test XML generation before submission
            self.logger.info("=== DEBUG: Testing XML generation ===")
            from fax.xml_generator import FaxXMLGenerator
            test_generator = FaxXMLGenerator()
            
            try:
                test_xml = test_generator.generate_faxfinder_xml(fax_job, contact, pdf_path)
                
                if test_xml:
                    self.logger.info(f"XML generated successfully, length: {len(test_xml)} characters")
                    
                    # Check for base64 content in XML
                    if 'base64' in test_xml:
                        self.logger.info("✓ Base64 content found in XML")
                        
                        # Extract and verify base64 content
                        start_marker = '<content>'
                        end_marker = '</content>'
                        start_pos = test_xml.find(start_marker)
                        end_pos = test_xml.find(end_marker)
                        
                        if start_pos != -1 and end_pos != -1:
                            start_pos += len(start_marker)
                            base64_content = test_xml[start_pos:end_pos].strip()
                            self.logger.info(f"✓ Extracted base64 content: {len(base64_content)} characters")
                            
                            # Verify it's valid base64
                            try:
                                decoded = base64.b64decode(base64_content)
                                self.logger.info(f"✓ Base64 validation successful: {len(decoded)} bytes")
                            except Exception as b64_error:
                                self.logger.error(f"✗ Base64 validation failed: {b64_error}")
                        else:
                            self.logger.error("✗ Base64 content markers not found in XML")
                    else:
                        self.logger.error("✗ No base64 content found in XML")
                        
                    # Save debug XML for inspection
                    debug_xml_path = "debug_xml_with_base64.xml"
                    with open(debug_xml_path, 'w', encoding='utf-8') as f:
                        f.write(test_xml)
                    self.logger.info(f"Debug XML saved to: {debug_xml_path}")
                    
                else:
                    self.logger.error("XML generation returned None/empty")
                    return {
                        'success': False,
                        'error': 'XML generation failed'
                    }
                    
            except Exception as xml_error:
                self.logger.error(f"XML generation failed: {xml_error}")
                return {
                    'success': False,
                    'error': f'XML generation failed: {str(xml_error)}'
                }
            
            # Use the correct submit_fax_job method that calls generate_faxfinder_xml
            self.logger.info("=== DEBUG: Submitting to FaxFinder ===")
            result = api.submit_fax_job(fax_job, contact, pdf_path)
            
            if result['success']:
                self.logger.info(f"Successfully submitted fax to FaxFinder: {result.get('fax_entry_url', 'No URL returned')}")
                return {
                    'success': True,
                    'fax_entry_url': result.get('fax_entry_url'),
                    'message': 'Fax submitted successfully to FaxFinder'
                }
            else:
                self.logger.error(f"FaxFinder submission failed: {result.get('error', 'Unknown error')}")
                return {
                    'success': False,
                    'error': result.get('error', 'Unknown FaxFinder error')
                }
                
        except Exception as e:
            self.logger.error(f"Error submitting to FaxFinder: {e}")
            return {
                'success': False,
                'error': f'Submission error: {str(e)}'
            }
    
    def _has_unsaved_edits(self) -> bool:
        """Check if there are any unsaved PDF edits"""
        # Check if current PDF viewer has edits
        if self.pdf_viewer and self.current_pdf_path:
            current_edit_data = self.pdf_viewer.get_edit_data()
            if self.pdf_viewer._has_edits(current_edit_data):
                return True
        
        # Check if any stored edit data has actual edits
        for pdf_path, edit_data in self.pdf_edit_data.items():
            if edit_data and self._edit_data_has_changes(edit_data):
                return True
        
        return False
    
    def _edit_data_has_changes(self, edit_data: Dict[str, Any]) -> bool:
        """Check if edit data contains actual changes"""
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
        """Handle window close event - warn about unsaved edits"""
        try:
            # Save current PDF edits before checking
            if self.pdf_viewer and self.current_pdf_path:
                edit_data = self.pdf_viewer.get_edit_data()
                self.pdf_edit_data[self.current_pdf_path] = edit_data
            
            # Check for unsaved edits
            if self._has_unsaved_edits():
                reply = QMessageBox.question(
                    self,
                    "Unsaved PDF Edits",
                    "You have unsaved PDF edits that will be lost if you close this window.\n\n"
                    "Are you sure you want to close without saving?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                    QMessageBox.StandardButton.No
                )
                
                if reply == QMessageBox.StandardButton.No:
                    event.ignore()
                    return
            
            # Clean up resources
            self.clear_final_preview()
            
            # Accept the close event
            event.accept()
            
        except Exception as e:
            self.logger.error(f"Error in closeEvent: {e}")
            # If there's an error, still allow closing
            event.accept()
