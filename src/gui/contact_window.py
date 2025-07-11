"""
Contact Management Window
Handles contact CRUD operations and CSV import/export
"""

import os
import csv
import logging
from pathlib import Path
from typing import List, Optional
from PyQt6.QtWidgets import (
    QDialog, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QPushButton, QLabel, QTableWidget, QTableWidgetItem, QGroupBox,
    QLineEdit, QTextEdit, QHeaderView, QMessageBox, QFileDialog,
    QSplitter, QAbstractItemView
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont

from database.models import Contact, ContactRepository

class ContactWindow(QDialog):
    """Window for managing contacts"""
    
    contact_updated = pyqtSignal()  # Signal emitted when contacts are updated
    
    def __init__(self, contact_repo: ContactRepository, parent=None):
        super().__init__(parent)
        self.logger = logging.getLogger(__name__)
        self.contact_repo = contact_repo
        self.contacts = []
        self.current_contact = None
        
        self.setup_ui()
        self.load_contacts()
    
    def setup_ui(self):
        """Setup the user interface"""
        self.setWindowTitle("Contact Management")
        self.setGeometry(200, 200, 1000, 700)
        self.setModal(True)
        
        # Main layout
        main_layout = QVBoxLayout(self)
        
        # Create splitter for resizable panels
        splitter = QSplitter(Qt.Orientation.Horizontal)
        main_layout.addWidget(splitter)
        
        # Left panel - Contact list
        left_panel = self.create_contact_list_panel()
        splitter.addWidget(left_panel)
        
        # Right panel - Contact details
        right_panel = self.create_contact_details_panel()
        splitter.addWidget(right_panel)
        
        # Set splitter proportions
        splitter.setSizes([600, 400])
        
        # Button layout
        button_layout = QHBoxLayout()
        
        # Import/Export buttons
        import_btn = QPushButton("Import CSV")
        import_btn.clicked.connect(self.import_csv)
        button_layout.addWidget(import_btn)
        
        export_btn = QPushButton("Export CSV")
        export_btn.clicked.connect(self.export_csv)
        button_layout.addWidget(export_btn)
        
        button_layout.addStretch()
        
        # Close button
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        button_layout.addWidget(close_btn)
        
        main_layout.addLayout(button_layout)
    
    def create_contact_list_panel(self):
        """Create the contact list panel"""
        panel = QGroupBox("Contacts")
        layout = QVBoxLayout(panel)
        
        # Search bar
        search_layout = QHBoxLayout()
        search_layout.addWidget(QLabel("Search:"))
        
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Search by name, fax, or organization...")
        self.search_edit.textChanged.connect(self.filter_contacts)
        search_layout.addWidget(self.search_edit)
        
        layout.addLayout(search_layout)
        
        # Contact table
        self.contact_table = QTableWidget()
        self.contact_table.setColumnCount(4)
        self.contact_table.setHorizontalHeaderLabels(["Name", "Fax Number", "Organization", "Phone"])
        
        # Configure table
        header = self.contact_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        
        self.contact_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.contact_table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.contact_table.itemSelectionChanged.connect(self.on_contact_selected)
        
        layout.addWidget(self.contact_table)
        
        # Contact list buttons
        button_layout = QHBoxLayout()
        
        new_btn = QPushButton("New Contact")
        new_btn.clicked.connect(self.new_contact)
        button_layout.addWidget(new_btn)
        
        self.delete_btn = QPushButton("Delete Contact")
        self.delete_btn.clicked.connect(self.delete_contact)
        self.delete_btn.setEnabled(False)
        button_layout.addWidget(self.delete_btn)
        
        refresh_btn = QPushButton("Refresh")
        refresh_btn.clicked.connect(self.load_contacts)
        button_layout.addWidget(refresh_btn)
        
        layout.addLayout(button_layout)
        
        return panel
    
    def create_contact_details_panel(self):
        """Create the contact details panel"""
        panel = QGroupBox("Contact Details")
        layout = QVBoxLayout(panel)
        
        # Contact form
        form_layout = QGridLayout()
        
        # Name
        form_layout.addWidget(QLabel("Name:"), 0, 0)
        self.name_edit = QLineEdit()
        form_layout.addWidget(self.name_edit, 0, 1)
        
        # Fax Number
        form_layout.addWidget(QLabel("Fax Number:"), 1, 0)
        self.fax_edit = QLineEdit()
        form_layout.addWidget(self.fax_edit, 1, 1)
        
        # Organization
        form_layout.addWidget(QLabel("Organization:"), 2, 0)
        self.org_edit = QLineEdit()
        form_layout.addWidget(self.org_edit, 2, 1)
        
        # Phone Number
        form_layout.addWidget(QLabel("Phone Number:"), 3, 0)
        self.phone_edit = QLineEdit()
        form_layout.addWidget(self.phone_edit, 3, 1)
        
        # Email
        form_layout.addWidget(QLabel("Email:"), 4, 0)
        self.email_edit = QLineEdit()
        form_layout.addWidget(self.email_edit, 4, 1)
        
        # Notes
        form_layout.addWidget(QLabel("Notes:"), 5, 0, Qt.AlignmentFlag.AlignTop)
        self.notes_edit = QTextEdit()
        self.notes_edit.setMaximumHeight(100)
        form_layout.addWidget(self.notes_edit, 5, 1)
        
        layout.addLayout(form_layout)
        
        # Form buttons
        button_layout = QHBoxLayout()
        
        self.save_btn = QPushButton("Save Contact")
        self.save_btn.setStyleSheet("""
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
        self.save_btn.clicked.connect(self.save_contact)
        self.save_btn.setEnabled(False)
        button_layout.addWidget(self.save_btn)
        
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.clicked.connect(self.cancel_edit)
        self.cancel_btn.setEnabled(False)
        button_layout.addWidget(self.cancel_btn)
        
        layout.addLayout(button_layout)
        
        # Add stretch to push form to top
        layout.addStretch()
        
        # Connect form fields to enable/disable save button
        self.name_edit.textChanged.connect(self.on_form_changed)
        self.fax_edit.textChanged.connect(self.on_form_changed)
        self.org_edit.textChanged.connect(self.on_form_changed)
        self.phone_edit.textChanged.connect(self.on_form_changed)
        self.email_edit.textChanged.connect(self.on_form_changed)
        self.notes_edit.textChanged.connect(self.on_form_changed)
        
        return panel
    
    def load_contacts(self):
        """Load contacts from database"""
        try:
            self.contacts = self.contact_repo.get_all()
            self.update_contact_table()
            self.clear_form()
        except Exception as e:
            self.logger.error(f"Error loading contacts: {e}")
            QMessageBox.critical(self, "Error", f"Failed to load contacts: {str(e)}")
    
    def update_contact_table(self):
        """Update the contact table with current contacts"""
        # Filter contacts based on search
        search_term = self.search_edit.text().lower()
        filtered_contacts = []
        
        for contact in self.contacts:
            if (not search_term or 
                search_term in contact.name.lower() or 
                search_term in contact.fax_number.lower() or 
                (contact.organization and search_term in contact.organization.lower()) or
                (contact.phone_number and search_term in contact.phone_number.lower())):
                filtered_contacts.append(contact)
        
        # Update table
        self.contact_table.setRowCount(len(filtered_contacts))
        
        for row, contact in enumerate(filtered_contacts):
            # Name
            name_item = QTableWidgetItem(contact.name or "")
            name_item.setData(Qt.ItemDataRole.UserRole, contact)
            self.contact_table.setItem(row, 0, name_item)
            
            # Fax Number
            fax_item = QTableWidgetItem(contact.fax_number or "")
            self.contact_table.setItem(row, 1, fax_item)
            
            # Organization
            org_item = QTableWidgetItem(contact.organization or "")
            self.contact_table.setItem(row, 2, org_item)
            
            # Phone
            phone_item = QTableWidgetItem(contact.phone_number or "")
            self.contact_table.setItem(row, 3, phone_item)
    
    def filter_contacts(self):
        """Filter contacts based on search term"""
        self.update_contact_table()
    
    def on_contact_selected(self):
        """Handle contact selection in table"""
        current_row = self.contact_table.currentRow()
        if current_row >= 0:
            name_item = self.contact_table.item(current_row, 0)
            if name_item:
                contact = name_item.data(Qt.ItemDataRole.UserRole)
                self.load_contact_to_form(contact)
                self.delete_btn.setEnabled(True)
        else:
            self.delete_btn.setEnabled(False)
    
    def load_contact_to_form(self, contact: Contact):
        """Load contact data into the form"""
        self.current_contact = contact
        
        self.name_edit.setText(contact.name or "")
        self.fax_edit.setText(contact.fax_number or "")
        self.org_edit.setText(contact.organization or "")
        self.phone_edit.setText(contact.phone_number or "")
        self.email_edit.setText(contact.email or "")
        self.notes_edit.setText(contact.notes or "")
        
        self.save_btn.setEnabled(False)  # No changes yet
        self.cancel_btn.setEnabled(True)
    
    def clear_form(self):
        """Clear the contact form"""
        self.current_contact = None
        
        self.name_edit.clear()
        self.fax_edit.clear()
        self.org_edit.clear()
        self.phone_edit.clear()
        self.email_edit.clear()
        self.notes_edit.clear()
        
        self.save_btn.setEnabled(False)
        self.cancel_btn.setEnabled(False)
        self.delete_btn.setEnabled(False)
    
    def new_contact(self):
        """Start creating a new contact"""
        self.contact_table.clearSelection()
        self.clear_form()
        self.name_edit.setFocus()
        self.cancel_btn.setEnabled(True)
    
    def on_form_changed(self):
        """Handle form field changes"""
        # Enable save button if there are changes
        has_name = bool(self.name_edit.text().strip())
        has_fax = bool(self.fax_edit.text().strip())
        
        # Basic validation - need at least name and fax
        can_save = has_name and has_fax
        
        # Check if there are actual changes
        if self.current_contact:
            has_changes = (
                self.name_edit.text() != (self.current_contact.name or "") or
                self.fax_edit.text() != (self.current_contact.fax_number or "") or
                self.org_edit.text() != (self.current_contact.organization or "") or
                self.phone_edit.text() != (self.current_contact.phone_number or "") or
                self.email_edit.text() != (self.current_contact.email or "") or
                self.notes_edit.toPlainText() != (self.current_contact.notes or "")
            )
            can_save = can_save and has_changes
        
        self.save_btn.setEnabled(can_save)
    
    def save_contact(self):
        """Save the current contact"""
        try:
            # Create or update contact object
            if self.current_contact:
                contact = self.current_contact
            else:
                contact = Contact()
            
            # Update contact data
            contact.name = self.name_edit.text().strip()
            contact.fax_number = self.fax_edit.text().strip()
            contact.organization = self.org_edit.text().strip() or None
            contact.phone_number = self.phone_edit.text().strip() or None
            contact.email = self.email_edit.text().strip() or None
            contact.notes = self.notes_edit.toPlainText().strip() or None
            
            # Validate
            errors = contact.validate()
            if errors:
                QMessageBox.warning(self, "Validation Error", "\n".join(errors))
                return
            
            # Save to database
            if contact.contact_id:
                # Update existing
                success = self.contact_repo.update(contact)
                if success:
                    QMessageBox.information(self, "Success", "Contact updated successfully")
                else:
                    QMessageBox.warning(self, "Warning", "No changes were made to the contact")
            else:
                # Create new
                contact_id = self.contact_repo.create(contact)
                contact.contact_id = contact_id
                QMessageBox.information(self, "Success", "Contact created successfully")
            
            # Refresh the contact list
            self.load_contacts()
            
            # Emit signal for other windows
            self.contact_updated.emit()
            
        except Exception as e:
            self.logger.error(f"Error saving contact: {e}")
            QMessageBox.critical(self, "Error", f"Failed to save contact: {str(e)}")
    
    def cancel_edit(self):
        """Cancel current edit operation"""
        if self.current_contact:
            # Reload the original contact data
            self.load_contact_to_form(self.current_contact)
        else:
            # Clear form for new contact
            self.clear_form()
    
    def delete_contact(self):
        """Delete the selected contact"""
        if not self.current_contact:
            return
        
        # Confirm deletion
        reply = QMessageBox.question(
            self,
            "Confirm Deletion",
            f"Are you sure you want to delete contact '{self.current_contact.name}'?\n\n"
            "This action cannot be undone.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                success = self.contact_repo.delete(self.current_contact.contact_id)
                if success:
                    QMessageBox.information(self, "Success", "Contact deleted successfully")
                    self.load_contacts()
                    self.contact_updated.emit()
                else:
                    QMessageBox.warning(self, "Warning", "Contact was not found or already deleted")
            except Exception as e:
                self.logger.error(f"Error deleting contact: {e}")
                QMessageBox.critical(self, "Error", f"Failed to delete contact: {str(e)}")
    
    def import_csv(self):
        """Import contacts from CSV file"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Import Contacts from CSV",
            str(Path.home()),
            "CSV Files (*.csv);;All Files (*)"
        )
        
        if not file_path:
            return
        
        try:
            imported_count = 0
            error_count = 0
            errors = []
            
            with open(file_path, 'r', newline='', encoding='utf-8') as csvfile:
                # Try to detect if file has headers
                sample = csvfile.read(1024)
                csvfile.seek(0)
                sniffer = csv.Sniffer()
                has_header = sniffer.has_header(sample)
                
                reader = csv.reader(csvfile)
                
                # Skip header if present
                if has_header:
                    next(reader)
                
                for row_num, row in enumerate(reader, start=2 if has_header else 1):
                    try:
                        if len(row) < 2:  # Need at least name and fax
                            continue
                        
                        # Map CSV columns: Name, Fax, Phone, Organization, Notes
                        contact = Contact(
                            name=row[0].strip() if len(row) > 0 else "",
                            fax_number=row[1].strip() if len(row) > 1 else "",
                            phone_number=row[2].strip() if len(row) > 2 else None,
                            organization=row[3].strip() if len(row) > 3 else None,
                            notes=row[4].strip() if len(row) > 4 else None
                        )
                        
                        # Validate
                        validation_errors = contact.validate()
                        if validation_errors:
                            error_count += 1
                            errors.append(f"Row {row_num}: {', '.join(validation_errors)}")
                            continue
                        
                        # Check for duplicate fax number
                        existing = self.contact_repo.get_by_fax_number(contact.fax_number)
                        if existing:
                            error_count += 1
                            errors.append(f"Row {row_num}: Duplicate fax number {contact.fax_number}")
                            continue
                        
                        # Save contact
                        self.contact_repo.create(contact)
                        imported_count += 1
                        
                    except Exception as e:
                        error_count += 1
                        errors.append(f"Row {row_num}: {str(e)}")
            
            # Show results
            message = f"Import completed:\n"
            message += f"• {imported_count} contacts imported successfully\n"
            if error_count > 0:
                message += f"• {error_count} errors encountered\n\n"
                if errors:
                    message += "Errors:\n" + "\n".join(errors[:10])  # Show first 10 errors
                    if len(errors) > 10:
                        message += f"\n... and {len(errors) - 10} more errors"
            
            if error_count > 0:
                QMessageBox.warning(self, "Import Results", message)
            else:
                QMessageBox.information(self, "Import Results", message)
            
            # Refresh contact list
            if imported_count > 0:
                self.load_contacts()
                self.contact_updated.emit()
                
        except Exception as e:
            self.logger.error(f"Error importing CSV: {e}")
            QMessageBox.critical(self, "Import Error", f"Failed to import CSV file: {str(e)}")
    
    def export_csv(self):
        """Export contacts to CSV file"""
        if not self.contacts:
            QMessageBox.information(self, "No Data", "No contacts to export")
            return
        
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export Contacts to CSV",
            str(Path.home() / "contacts.csv"),
            "CSV Files (*.csv);;All Files (*)"
        )
        
        if not file_path:
            return
        
        try:
            with open(file_path, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                
                # Write header
                writer.writerow(["Name", "Fax", "Phone", "Organization", "Notes"])
                
                # Write contact data
                for contact in self.contacts:
                    writer.writerow([
                        contact.name or "",
                        contact.fax_number or "",
                        contact.phone_number or "",
                        contact.organization or "",
                        contact.notes or ""
                    ])
            
            QMessageBox.information(
                self,
                "Export Complete",
                f"Successfully exported {len(self.contacts)} contacts to:\n{file_path}"
            )
            
        except Exception as e:
            self.logger.error(f"Error exporting CSV: {e}")
            QMessageBox.critical(self, "Export Error", f"Failed to export CSV file: {str(e)}")
