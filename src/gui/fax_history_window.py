"""
Fax History Window
Displays historical fax jobs with filtering and viewing capabilities
"""

import os
import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Optional, Dict, Any
from PyQt6.QtWidgets import (
    QDialog, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QPushButton, QLabel, QTableWidget, QTableWidgetItem, QGroupBox,
    QLineEdit, QComboBox, QDateEdit, QHeaderView, QMessageBox,
    QSplitter, QAbstractItemView, QMenu, QTextEdit, QTabWidget,
    QScrollArea
)
from PyQt6.QtCore import Qt, QDate, pyqtSignal
from PyQt6.QtGui import QFont, QAction, QColor

from database.models import FaxJob, Contact, FaxJobRepository, ContactRepository

class FaxHistoryWindow(QDialog):
    """Window for viewing fax job history"""
    
    fax_selected = pyqtSignal(object)  # Signal emitted when fax is selected for resending
    
    def __init__(self, fax_job_repo: FaxJobRepository, contact_repo: ContactRepository, parent=None):
        super().__init__(parent)
        self.logger = logging.getLogger(__name__)
        self.fax_job_repo = fax_job_repo
        self.contact_repo = contact_repo
        
        # Data
        self.fax_jobs = []
        self.contacts = {}  # contact_id -> Contact object
        self.filtered_jobs = []
        
        # Current selection
        self.selected_fax_job = None
        
        self.setup_ui()
        self.load_data()
    
    def setup_ui(self):
        """Setup the user interface"""
        self.setWindowTitle("Fax History")
        self.setGeometry(200, 200, 1200, 800)
        self.setModal(True)
        
        # Main layout
        main_layout = QVBoxLayout(self)
        
        # Filter section
        filter_group = self.create_filter_section()
        main_layout.addWidget(filter_group)
        
        # Create splitter for resizable panels
        splitter = QSplitter(Qt.Orientation.Horizontal)
        main_layout.addWidget(splitter)
        
        # Left panel - Fax job list
        left_panel = self.create_fax_list_panel()
        splitter.addWidget(left_panel)
        
        # Right panel - Fax details
        right_panel = self.create_fax_details_panel()
        splitter.addWidget(right_panel)
        
        # Set splitter proportions
        splitter.setSizes([700, 500])
        
        # Button layout
        button_layout = QHBoxLayout()
        
        refresh_btn = QPushButton("Refresh")
        refresh_btn.clicked.connect(self.load_data)
        button_layout.addWidget(refresh_btn)
        
        button_layout.addStretch()
        
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        button_layout.addWidget(close_btn)
        
        main_layout.addLayout(button_layout)
    
    def create_filter_section(self):
        """Create the filter section"""
        group = QGroupBox("Filters")
        layout = QHBoxLayout(group)
        
        # Contact filter
        layout.addWidget(QLabel("Contact:"))
        self.contact_filter = QComboBox()
        self.contact_filter.addItem("All Contacts", None)
        self.contact_filter.currentTextChanged.connect(self.apply_filters)
        layout.addWidget(self.contact_filter)
        
        # Status filter
        layout.addWidget(QLabel("Status:"))
        self.status_filter = QComboBox()
        self.status_filter.addItems([
            "All Statuses", "Pending", "Processing", "Sent", "Failed", "Cancelled"
        ])
        self.status_filter.currentTextChanged.connect(self.apply_filters)
        layout.addWidget(self.status_filter)
        
        # Date range
        layout.addWidget(QLabel("From:"))
        self.date_from = QDateEdit()
        self.date_from.setDate(QDate.currentDate().addDays(-30))  # Default to last 30 days
        self.date_from.setCalendarPopup(True)
        self.date_from.dateChanged.connect(self.apply_filters)
        layout.addWidget(self.date_from)
        
        layout.addWidget(QLabel("To:"))
        self.date_to = QDateEdit()
        self.date_to.setDate(QDate.currentDate())
        self.date_to.setCalendarPopup(True)
        self.date_to.dateChanged.connect(self.apply_filters)
        layout.addWidget(self.date_to)
        
        # Search
        layout.addWidget(QLabel("Search:"))
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Search subject, recipient...")
        self.search_edit.textChanged.connect(self.apply_filters)
        layout.addWidget(self.search_edit)
        
        layout.addStretch()
        
        return group
    
    def create_fax_list_panel(self):
        """Create the fax job list panel"""
        panel = QGroupBox("Fax Jobs")
        layout = QVBoxLayout(panel)
        
        # Fax job table
        self.fax_table = QTableWidget()
        self.fax_table.setColumnCount(6)
        self.fax_table.setHorizontalHeaderLabels([
            "Date/Time", "Recipient", "Subject", "Status", "Pages", "Priority"
        ])
        
        # Configure table
        header = self.fax_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)
        
        self.fax_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.fax_table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.fax_table.itemSelectionChanged.connect(self.on_fax_selected)
        
        # Context menu
        self.fax_table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.fax_table.customContextMenuRequested.connect(self.show_context_menu)
        
        layout.addWidget(self.fax_table)
        
        # Status label
        self.status_label = QLabel("No fax jobs loaded")
        layout.addWidget(self.status_label)
        
        return panel
    
    def create_fax_details_panel(self):
        """Create the fax details panel"""
        panel = QGroupBox("Fax Details")
        layout = QVBoxLayout(panel)
        
        # Tab widget for different detail views
        self.details_tabs = QTabWidget()
        layout.addWidget(self.details_tabs)
        
        # General info tab
        self.create_general_info_tab()
        
        # Cover page tab
        self.create_cover_page_tab()
        
        # Technical details tab
        self.create_technical_tab()
        
        # Action buttons
        button_layout = QHBoxLayout()
        
        self.view_details_btn = QPushButton("View Full Details")
        self.view_details_btn.clicked.connect(self.view_full_details)
        self.view_details_btn.setEnabled(False)
        button_layout.addWidget(self.view_details_btn)
        
        self.resend_btn = QPushButton("Resend Fax")
        self.resend_btn.clicked.connect(self.resend_fax)
        self.resend_btn.setEnabled(False)
        self.resend_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 8px 16px;
                font-weight: bold;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:disabled {
                background-color: #cccccc;
                color: #666666;
            }
        """)
        button_layout.addWidget(self.resend_btn)
        
        layout.addLayout(button_layout)
        
        return panel
    
    def create_general_info_tab(self):
        """Create general information tab"""
        tab = QWidget()
        layout = QGridLayout(tab)
        
        # Create labels for displaying fax info
        self.info_labels = {}
        
        fields = [
            ("Fax ID:", "fax_id"),
            ("Status:", "status"),
            ("Created:", "created_at"),
            ("Sent:", "sent_at"),
            ("Sender:", "sender_name"),
            ("Sender Email:", "sender_email"),
            ("Recipient:", "recipient_name"),
            ("Recipient Fax:", "recipient_fax"),
            ("Priority:", "priority"),
            ("Max Attempts:", "max_attempts"),
            ("Retry Interval:", "retry_interval")
        ]
        
        for i, (label_text, field_name) in enumerate(fields):
            row = i // 2
            col = (i % 2) * 2
            
            layout.addWidget(QLabel(label_text), row, col)
            value_label = QLabel("-")
            value_label.setStyleSheet("QLabel { color: #333; font-weight: bold; }")
            layout.addWidget(value_label, row, col + 1)
            self.info_labels[field_name] = value_label
        
        layout.setRowStretch(len(fields) // 2 + 1, 1)
        
        self.details_tabs.addTab(tab, "General")
    
    def create_cover_page_tab(self):
        """Create cover page details tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Scroll area for cover page details
        scroll_area = QScrollArea()
        scroll_widget = QWidget()
        scroll_layout = QGridLayout(scroll_widget)
        
        # Cover page fields
        self.cover_page_labels = {}
        
        cover_fields = [
            ("To:", "to"),
            ("Attention:", "attn"),
            ("From:", "from_field"),
            ("Company:", "company"),
            ("Fax:", "fax"),
            ("Phone:", "phone"),
            ("Date:", "date"),
            ("Subject:", "subject"),
            ("Re:", "re"),
            ("CC:", "cc"),
            ("Pages:", "pages")
        ]
        
        for i, (label_text, field_name) in enumerate(cover_fields):
            scroll_layout.addWidget(QLabel(label_text), i, 0)
            value_label = QLabel("-")
            value_label.setWordWrap(True)
            value_label.setStyleSheet("QLabel { color: #333; }")
            scroll_layout.addWidget(value_label, i, 1)
            self.cover_page_labels[field_name] = value_label
        
        # Comments and message (larger fields)
        scroll_layout.addWidget(QLabel("Comments:"), len(cover_fields), 0, Qt.AlignmentFlag.AlignTop)
        self.comments_label = QTextEdit()
        self.comments_label.setReadOnly(True)
        self.comments_label.setMaximumHeight(80)
        scroll_layout.addWidget(self.comments_label, len(cover_fields), 1)
        
        scroll_layout.addWidget(QLabel("Message:"), len(cover_fields) + 1, 0, Qt.AlignmentFlag.AlignTop)
        self.message_label = QTextEdit()
        self.message_label.setReadOnly(True)
        self.message_label.setMaximumHeight(80)
        scroll_layout.addWidget(self.message_label, len(cover_fields) + 1, 1)
        
        scroll_area.setWidget(scroll_widget)
        layout.addWidget(scroll_area)
        
        self.details_tabs.addTab(tab, "Cover Page")
    
    def create_technical_tab(self):
        """Create technical details tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Technical info
        self.technical_text = QTextEdit()
        self.technical_text.setReadOnly(True)
        self.technical_text.setFont(QFont("Courier", 9))
        layout.addWidget(self.technical_text)
        
        self.details_tabs.addTab(tab, "Technical")
    
    def load_data(self):
        """Load fax jobs and contacts from database"""
        try:
            # Load contacts for filter dropdown
            contacts = self.contact_repo.get_all()
            self.contacts = {contact.contact_id: contact for contact in contacts}
            
            # Update contact filter
            self.contact_filter.clear()
            self.contact_filter.addItem("All Contacts", None)
            for contact in sorted(contacts, key=lambda c: c.name):
                self.contact_filter.addItem(f"{contact.name} ({contact.fax_number})", contact.contact_id)
            
            # Load fax jobs
            self.fax_jobs = self.fax_job_repo.get_all()
            
            # Apply filters and update display
            self.apply_filters()
            
            self.logger.info(f"Loaded {len(self.fax_jobs)} fax jobs and {len(contacts)} contacts")
            
        except Exception as e:
            self.logger.error(f"Error loading fax history data: {e}")
            QMessageBox.critical(self, "Error", f"Failed to load fax history: {str(e)}")
    
    def apply_filters(self):
        """Apply current filters to fax job list"""
        try:
            # Get filter values
            selected_contact_id = self.contact_filter.currentData()
            selected_status = self.status_filter.currentText()
            date_from = self.date_from.date().toPython()
            date_to = self.date_to.date().toPython()
            search_term = self.search_edit.text().lower()
            
            # Filter fax jobs
            self.filtered_jobs = []
            
            for fax_job in self.fax_jobs:
                # Contact filter
                if selected_contact_id is not None and fax_job.recipient_id != selected_contact_id:
                    continue
                
                # Status filter
                if selected_status != "All Statuses" and fax_job.status != selected_status:
                    continue
                
                # Date filter
                if fax_job.created_at:
                    job_date = fax_job.created_at.date()
                    if job_date < date_from or job_date > date_to:
                        continue
                
                # Search filter
                if search_term:
                    # Get contact name for search
                    contact = self.contacts.get(fax_job.recipient_id)
                    contact_name = contact.name.lower() if contact else ""
                    
                    # Get cover page subject
                    subject = ""
                    if fax_job.cover_page_details:
                        try:
                            cover_data = json.loads(fax_job.cover_page_details) if isinstance(fax_job.cover_page_details, str) else fax_job.cover_page_details
                            subject = (cover_data.get('subject', '') or '').lower()
                        except:
                            pass
                    
                    if (search_term not in contact_name and 
                        search_term not in subject and 
                        search_term not in (fax_job.sender_name or '').lower()):
                        continue
                
                self.filtered_jobs.append(fax_job)
            
            # Update table
            self.update_fax_table()
            
        except Exception as e:
            self.logger.error(f"Error applying filters: {e}")
    
    def update_fax_table(self):
        """Update the fax job table with filtered results"""
        self.fax_table.setRowCount(len(self.filtered_jobs))
        
        for row, fax_job in enumerate(self.filtered_jobs):
            # Date/Time
            date_str = fax_job.created_at.strftime("%Y-%m-%d %H:%M") if fax_job.created_at else "Unknown"
            date_item = QTableWidgetItem(date_str)
            date_item.setData(Qt.ItemDataRole.UserRole, fax_job)
            self.fax_table.setItem(row, 0, date_item)
            
            # Recipient
            contact = self.contacts.get(fax_job.recipient_id)
            recipient_name = contact.name if contact else f"Contact ID: {fax_job.recipient_id}"
            recipient_item = QTableWidgetItem(recipient_name)
            self.fax_table.setItem(row, 1, recipient_item)
            
            # Subject (from cover page)
            subject = "No Subject"
            if fax_job.cover_page_details:
                try:
                    cover_data = json.loads(fax_job.cover_page_details) if isinstance(fax_job.cover_page_details, str) else fax_job.cover_page_details
                    subject = cover_data.get('subject', 'No Subject') or 'No Subject'
                except:
                    pass
            subject_item = QTableWidgetItem(subject)
            self.fax_table.setItem(row, 2, subject_item)
            
            # Status
            status_item = QTableWidgetItem(fax_job.status or "Unknown")
            # Color code status
            if fax_job.status == "Sent":
                status_item.setBackground(QColor(200, 255, 200))  # Light green
            elif fax_job.status == "Failed":
                status_item.setBackground(QColor(255, 200, 200))  # Light red
            elif fax_job.status in ["Pending", "Processing"]:
                status_item.setBackground(QColor(255, 255, 200))  # Light yellow
            self.fax_table.setItem(row, 3, status_item)
            
            # Pages (placeholder - would need to parse from PDF or XML)
            pages_item = QTableWidgetItem("N/A")
            self.fax_table.setItem(row, 4, pages_item)
            
            # Priority
            priority_item = QTableWidgetItem(fax_job.priority or "Medium")
            self.fax_table.setItem(row, 5, priority_item)
        
        # Update status
        total_jobs = len(self.fax_jobs)
        filtered_jobs = len(self.filtered_jobs)
        self.status_label.setText(f"Showing {filtered_jobs} of {total_jobs} fax jobs")
    
    def on_fax_selected(self):
        """Handle fax job selection in table"""
        current_row = self.fax_table.currentRow()
        if current_row >= 0:
            date_item = self.fax_table.item(current_row, 0)
            if date_item:
                self.selected_fax_job = date_item.data(Qt.ItemDataRole.UserRole)
                self.update_fax_details()
                self.view_details_btn.setEnabled(True)
                self.resend_btn.setEnabled(True)
        else:
            self.selected_fax_job = None
            self.clear_fax_details()
            self.view_details_btn.setEnabled(False)
            self.resend_btn.setEnabled(False)
    
    def update_fax_details(self):
        """Update the fax details panel with selected fax job"""
        if not self.selected_fax_job:
            return
        
        fax_job = self.selected_fax_job
        
        # Update general info
        self.info_labels["fax_id"].setText(str(fax_job.fax_id or "N/A"))
        self.info_labels["status"].setText(fax_job.status or "Unknown")
        self.info_labels["created_at"].setText(
            fax_job.created_at.strftime("%Y-%m-%d %H:%M:%S") if fax_job.created_at else "N/A"
        )
        self.info_labels["sent_at"].setText(
            fax_job.sent_at.strftime("%Y-%m-%d %H:%M:%S") if fax_job.sent_at else "Not sent"
        )
        self.info_labels["sender_name"].setText(fax_job.sender_name or "N/A")
        self.info_labels["sender_email"].setText(fax_job.sender_email or "N/A")
        
        # Recipient info
        contact = self.contacts.get(fax_job.recipient_id)
        if contact:
            self.info_labels["recipient_name"].setText(contact.name)
            self.info_labels["recipient_fax"].setText(contact.fax_number)
        else:
            self.info_labels["recipient_name"].setText(f"Contact ID: {fax_job.recipient_id}")
            self.info_labels["recipient_fax"].setText(fax_job.recipient_fax or "N/A")
        
        self.info_labels["priority"].setText(fax_job.priority or "N/A")
        self.info_labels["max_attempts"].setText(str(fax_job.max_attempts or "N/A"))
        self.info_labels["retry_interval"].setText(f"{fax_job.retry_interval or 'N/A'} minutes")
        
        # Update cover page details
        self.update_cover_page_details(fax_job)
        
        # Update technical details
        self.update_technical_details(fax_job)
    
    def update_cover_page_details(self, fax_job):
        """Update cover page details tab"""
        # Clear all fields first
        for label in self.cover_page_labels.values():
            label.setText("-")
        self.comments_label.clear()
        self.message_label.clear()
        
        if not fax_job.cover_page_details:
            return
        
        try:
            # Parse cover page data
            if isinstance(fax_job.cover_page_details, str):
                cover_data = json.loads(fax_job.cover_page_details)
            else:
                cover_data = fax_job.cover_page_details
            
            # Update fields
            for field_name, label in self.cover_page_labels.items():
                value = cover_data.get(field_name, '') or '-'
                label.setText(str(value))
            
            # Update text fields
            self.comments_label.setText(cover_data.get('comments', '') or '')
            self.message_label.setText(cover_data.get('msg', '') or '')
            
        except Exception as e:
            self.logger.error(f"Error parsing cover page details: {e}")
            self.comments_label.setText(f"Error parsing cover page data: {str(e)}")
    
    def update_technical_details(self, fax_job):
        """Update technical details tab"""
        technical_info = []
        
        technical_info.append("=== FAX JOB TECHNICAL DETAILS ===\n")
        technical_info.append(f"Fax ID: {fax_job.fax_id}")
        technical_info.append(f"Entry URL: {fax_job.fax_entry_url or 'N/A'}")
        technical_info.append(f"PDF Path: {fax_job.pdf_path or 'N/A'}")
        technical_info.append(f"Created: {fax_job.created_at}")
        technical_info.append(f"Sent: {fax_job.sent_at or 'Not sent'}")
        technical_info.append("")
        
        # XML content (if available)
        if fax_job.xml_content:
            technical_info.append("=== XML CONTENT ===")
            technical_info.append(fax_job.xml_content)
        else:
            technical_info.append("=== XML CONTENT ===")
            technical_info.append("No XML content available")
        
        self.technical_text.setText("\n".join(technical_info))
    
    def clear_fax_details(self):
        """Clear the fax details panel"""
        # Clear general info
        for label in self.info_labels.values():
            label.setText("-")
        
        # Clear cover page
        for label in self.cover_page_labels.values():
            label.setText("-")
        self.comments_label.clear()
        self.message_label.clear()
        
        # Clear technical
        self.technical_text.clear()
    
    def show_context_menu(self, position):
        """Show context menu for fax table"""
        if self.fax_table.itemAt(position) is None:
            return
        
        menu = QMenu(self)
        
        view_action = QAction("View Details", self)
        view_action.triggered.connect(self.view_full_details)
        menu.addAction(view_action)
        
        resend_action = QAction("Resend Fax", self)
        resend_action.triggered.connect(self.resend_fax)
        menu.addAction(resend_action)
        
        menu.addSeparator()
        
        export_action = QAction("Export Details", self)
        export_action.triggered.connect(self.export_fax_details)
        menu.addAction(export_action)
        
        menu.exec(self.fax_table.mapToGlobal(position))
    
    def view_full_details(self):
        """View full details of selected fax job"""
        if not self.selected_fax_job:
            return
        
        # Create a detailed view dialog
        dialog = QDialog(self)
        dialog.setWindowTitle(f"Fax Details - ID {self.selected_fax_job.fax_id}")
        dialog.setGeometry(300, 300, 800, 600)
        
        layout = QVBoxLayout(dialog)
        
        # Full details text
        details_text = QTextEdit()
        details_text.setReadOnly(True)
        details_text.setFont(QFont("Courier", 10))
        
        # Generate detailed text
        details = self.generate_full_details_text(self.selected_fax_job)
        details_text.setText(details)
        
        layout.addWidget(details_text)
        
        # Close button
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(dialog.accept)
        layout.addWidget(close_btn)
        
        dialog.exec()
    
    def generate_full_details_text(self, fax_job):
        """Generate full details text for a fax job"""
        lines = []
        
        lines.append("=" * 60)
        lines.append(f"FAX JOB DETAILS - ID: {fax_job.fax_id}")
        lines.append("=" * 60)
        lines.append("")
        
        # Basic info
        lines.append("BASIC INFORMATION:")
        lines.append(f"  Status: {fax_job.status or 'Unknown'}")
        lines.append(f"  Created: {fax_job.created_at or 'N/A'}")
        lines.append(f"  Sent: {fax_job.sent_at or 'Not sent'}")
        lines.append(f"  Entry URL: {fax_job.fax_entry_url or 'N/A'}")
        lines.append("")
        
        # Sender info
        lines.append("SENDER INFORMATION:")
        lines.append(f"  Name: {fax_job.sender_name or 'N/A'}")
        lines.append(f"  Email: {fax_job.sender_email or 'N/A'}")
        lines.append("")
        
        # Recipient info
        lines.append("RECIPIENT INFORMATION:")
        contact = self.contacts.get(fax_job.recipient_id)
        if contact:
            lines.append(f"  Name: {contact.name}")
            lines.append(f"  Fax: {contact.fax_number}")
            lines.append(f"  Organization: {contact.organization or 'N/A'}")
            lines.append(f"  Phone: {contact.phone_number or 'N/A'}")
            lines.append(f"  Email: {contact.email or 'N/A'}")
        else:
            lines.append(f"  Contact ID: {fax_job.recipient_id}")
            lines.append(f"  Fax: {fax_job.recipient_fax or 'N/A'}")
        lines.append("")
        
        # Fax settings
        lines.append("FAX SETTINGS:")
        lines.append(f"  Priority: {fax_job.priority or 'N/A'}")
        lines.append(f"  Max Attempts: {fax_job.max_attempts or 'N/A'}")
        lines.append(f"  Retry Interval: {fax_job.retry_interval or 'N/A'} minutes")
        lines.append("")
        
        # Cover page details
        if fax_job.cover_page_details:
            lines.append("COVER PAGE DETAILS:")
            try:
                if isinstance(fax_job.cover_page_details, str):
                    cover_data = json.loads(fax_job.cover_page_details)
                else:
                    cover_data = fax_job.cover_page_details
                
                for key, value in cover_data.items():
                    if value:
                        lines.append(f"  {key.title()}: {value}")
            except Exception as e:
                lines.append(f"  Error parsing cover page: {str(e)}")
            lines.append("")
        
        # File info
        lines.append("FILE INFORMATION:")
        lines.append(f"  PDF Path: {fax_job.pdf_path or 'N/A'}")
        lines.append("")
        
        # XML content
        if fax_job.xml_content:
            lines.append("XML CONTENT:")
            lines.append("-" * 40)
            lines.append(fax_job.xml_content)
        
        return "\n".join(lines)
    
    def resend_fax(self):
        """Resend the selected fax job"""
        if not self.selected_fax_job:
            return
        
        reply = QMessageBox.question(
            self,
            "Resend Fax",
            f"Are you sure you want to resend fax job {self.selected_fax_job.fax_id}?\n\n"
            "This will create a new fax job with the same details.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            # Emit signal to parent window to handle resending
            self.fax_selected.emit(self.selected_fax_job)
            QMessageBox.information(self, "Resend Initiated", "Fax resend has been initiated.")
    
    def export_fax_details(self):
        """Export fax details to a text file"""
        if not self.selected_fax_job:
            return
        
        from PyQt6.QtWidgets import QFileDialog
        
        # Get save location
        filename = f"fax_details_{self.selected_fax_job.fax_id}.txt"
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export Fax Details",
            filename,
            "Text Files (*.txt);;All Files (*)"
        )
        
        if file_path:
            try:
                details = self.generate_full_details_text(self.selected_fax_job)
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(details)
                
                QMessageBox.information(
                    self,
                    "Export Complete",
                    f"Fax details exported to:\n{file_path}"
                )
                
            except Exception as e:
                self.logger.error(f"Error exporting fax details: {e}")
                QMessageBox.critical(
                    self,
                    "Export Error",
                    f"Failed to export fax details: {str(e)}"
                )
