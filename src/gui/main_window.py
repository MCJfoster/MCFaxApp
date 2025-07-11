"""
Main Window for MCFax Application
Provides the primary interface for fax management
"""

import os
import logging
from pathlib import Path
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QPushButton, QLabel, QListWidget, QListWidgetItem, QGroupBox,
    QFileDialog, QMessageBox, QStatusBar, QMenuBar, QMenu,
    QSplitter, QTextEdit, QProgressBar
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QAction, QIcon, QFont

from .fax_job_window import FaxJobWindow
from .contact_window import ContactWindow
from .fax_history_window import FaxHistoryWindow
from pdf.pdf_browser import PDFBrowser
from pdf.pdf_viewer import PDFViewer
from pdf.pdf_editor import PDFEditor
from database.connection import DatabaseConnection
from database.models import ContactRepository, FaxJobRepository
from core.folder_watcher import FolderWatcher
from core.settings_portable import get_settings

class MainWindow(QMainWindow):
    """Main application window"""
    
    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger(__name__)
        
        # Initialize settings
        self.settings = get_settings()
        
        # Initialize components
        self.db_connection = None
        self.contact_repo = None
        self.fax_job_repo = None
        self.pdf_browser = None
        self.temp_folder = None
        
        # Folder monitoring
        self.folder_watcher = None
        self.monitoring_enabled = self.settings.is_folder_monitoring_enabled()
        
        # Child windows
        self.fax_job_window = None
        self.contact_window = None
        
        # Setup UI
        self.setup_ui()
        self.load_window_settings()
        self.setup_database()
        self.setup_temp_folder()
        
        # Start smart periodic updates
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.smart_refresh_pdf_list)
        refresh_interval = self.settings.get_auto_refresh_interval()
        self.update_timer.start(refresh_interval)
    
    def setup_ui(self):
        """Setup the user interface"""
        self.setWindowTitle("MCFax - Fax Management System")
        self.setGeometry(100, 100, 1200, 800)
        
        # Create menu bar
        self.create_menu_bar()
        
        # Create status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready")
        
        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        main_layout = QHBoxLayout(central_widget)
        
        # Create splitter for resizable panels
        splitter = QSplitter(Qt.Orientation.Horizontal)
        main_layout.addWidget(splitter)
        
        # Left panel - PDF Browser
        left_panel = self.create_pdf_panel()
        splitter.addWidget(left_panel)
        
        # Right panel - Actions and Status
        right_panel = self.create_action_panel()
        splitter.addWidget(right_panel)
        
        # Set splitter proportions
        splitter.setSizes([600, 400])
    
    def create_menu_bar(self):
        """Create application menu bar"""
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu('&File')
        
        # Select temp folder action
        select_folder_action = QAction('Select &Temp Folder...', self)
        select_folder_action.setShortcut('Ctrl+T')
        select_folder_action.triggered.connect(self.select_temp_folder)
        file_menu.addAction(select_folder_action)
        
        file_menu.addSeparator()
        
        # Exit action
        exit_action = QAction('E&xit', self)
        exit_action.setShortcut('Ctrl+Q')
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Fax menu
        fax_menu = menubar.addMenu('&Fax')
        
        # New fax job action
        new_fax_action = QAction('&New Fax Job...', self)
        new_fax_action.setShortcut('Ctrl+N')
        new_fax_action.triggered.connect(self.create_new_fax_job)
        fax_menu.addAction(new_fax_action)
        
        fax_menu.addSeparator()
        
        # Fax history action
        history_action = QAction('Fax &History...', self)
        history_action.setShortcut('Ctrl+H')
        history_action.triggered.connect(self.open_fax_history)
        fax_menu.addAction(history_action)
        
        # Contacts menu
        contacts_menu = menubar.addMenu('&Contacts')
        
        # Manage contacts action
        manage_contacts_action = QAction('&Manage Contacts...', self)
        manage_contacts_action.setShortcut('Ctrl+M')
        manage_contacts_action.triggered.connect(self.open_contact_manager)
        contacts_menu.addAction(manage_contacts_action)
        
        # Tools menu
        tools_menu = menubar.addMenu('&Tools')
        
        # Settings action
        settings_action = QAction('&Settings...', self)
        settings_action.setShortcut('Ctrl+,')
        settings_action.triggered.connect(self.open_settings)
        tools_menu.addAction(settings_action)
        
        # Help menu
        help_menu = menubar.addMenu('&Help')
        
        # About action
        about_action = QAction('&About MCFax', self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
    
    def create_pdf_panel(self):
        """Create the PDF browser panel"""
        panel = QGroupBox("PDF Files")
        layout = QVBoxLayout(panel)
        
        # Folder selection
        folder_layout = QHBoxLayout()
        self.folder_label = QLabel("No temp folder selected")
        self.folder_label.setStyleSheet("QLabel { color: #666; font-style: italic; }")
        folder_layout.addWidget(self.folder_label)
        
        select_folder_btn = QPushButton("Select Folder")
        select_folder_btn.clicked.connect(self.select_temp_folder)
        folder_layout.addWidget(select_folder_btn)
        
        layout.addLayout(folder_layout)
        
        # PDF list
        self.pdf_list = QListWidget()
        self.pdf_list.setSelectionMode(QListWidget.SelectionMode.ExtendedSelection)
        self.pdf_list.itemSelectionChanged.connect(self.on_pdf_selection_changed)
        layout.addWidget(self.pdf_list)
        
        # PDF actions
        pdf_actions_layout = QHBoxLayout()
        
        view_pdf_btn = QPushButton("View PDF")
        view_pdf_btn.clicked.connect(self.view_selected_pdf)
        pdf_actions_layout.addWidget(view_pdf_btn)
        
        edit_pdf_btn = QPushButton("Edit PDF")
        edit_pdf_btn.clicked.connect(self.edit_selected_pdf)
        pdf_actions_layout.addWidget(edit_pdf_btn)
        
        layout.addLayout(pdf_actions_layout)
        
        # PDF info
        self.pdf_info = QTextEdit()
        self.pdf_info.setMaximumHeight(100)
        self.pdf_info.setReadOnly(True)
        self.pdf_info.setPlaceholderText("Select PDF files to view information...")
        layout.addWidget(self.pdf_info)
        
        # Refresh button
        refresh_btn = QPushButton("Refresh PDF List")
        refresh_btn.clicked.connect(self.refresh_pdf_list)
        layout.addWidget(refresh_btn)
        
        return panel
    
    def create_action_panel(self):
        """Create the action panel"""
        panel = QGroupBox("Actions")
        layout = QVBoxLayout(panel)
        
        # New Fax Job section
        fax_group = QGroupBox("Fax Operations")
        fax_layout = QVBoxLayout(fax_group)
        
        self.new_fax_btn = QPushButton("Create New Fax Job")
        self.new_fax_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 10px;
                font-size: 14px;
                font-weight: bold;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:disabled {
                background-color: #cccccc;
                color: #666666;
            }
        """)
        self.new_fax_btn.clicked.connect(self.create_new_fax_job)
        self.new_fax_btn.setEnabled(False)
        fax_layout.addWidget(self.new_fax_btn)
        
        layout.addWidget(fax_group)
        
        # Contact Management section
        contact_group = QGroupBox("Contact Management")
        contact_layout = QVBoxLayout(contact_group)
        
        manage_contacts_btn = QPushButton("Manage Contacts")
        manage_contacts_btn.clicked.connect(self.open_contact_manager)
        contact_layout.addWidget(manage_contacts_btn)
        
        layout.addWidget(contact_group)
        
        # Status section
        status_group = QGroupBox("System Status")
        status_layout = QVBoxLayout(status_group)
        
        self.db_status_label = QLabel("Database: Not connected")
        self.folder_status_label = QLabel("Temp Folder: Not selected")
        self.pdf_count_label = QLabel("PDF Files: 0")
        
        status_layout.addWidget(self.db_status_label)
        status_layout.addWidget(self.folder_status_label)
        status_layout.addWidget(self.pdf_count_label)
        
        layout.addWidget(status_group)
        
        # Add stretch to push everything to top
        layout.addStretch()
        
        return panel
    
    def setup_database(self):
        """Setup database connection"""
        try:
            self.db_connection = DatabaseConnection()
            if self.db_connection.connect():
                self.contact_repo = ContactRepository(self.db_connection)
                self.fax_job_repo = FaxJobRepository(self.db_connection)
                self.db_status_label.setText("Database: Connected")
                self.db_status_label.setStyleSheet("QLabel { color: green; }")
                self.status_bar.showMessage("Database connected successfully")
                self.logger.info("Database connected successfully")
            else:
                self.db_status_label.setText("Database: Connection failed")
                self.db_status_label.setStyleSheet("QLabel { color: red; }")
                self.status_bar.showMessage("Database connection failed")
                self.logger.error("Failed to connect to database")
        except Exception as e:
            self.db_status_label.setText("Database: Error")
            self.db_status_label.setStyleSheet("QLabel { color: red; }")
            self.status_bar.showMessage(f"Database error: {str(e)}")
            self.logger.error(f"Database setup error: {e}")
    
    def load_window_settings(self):
        """Load window geometry and settings from persistent storage"""
        try:
            # Load window geometry
            geometry = self.settings.get_window_geometry()
            self.setGeometry(geometry['x'], geometry['y'], geometry['width'], geometry['height'])
            
            # Load maximized state
            if self.settings.is_window_maximized():
                self.showMaximized()
            
            # Load splitter sizes
            splitter_sizes = self.settings.get_splitter_sizes()
            # Note: We'll apply splitter sizes after the splitter is created
            
            self.logger.info("Window settings loaded from configuration")
            
        except Exception as e:
            self.logger.error(f"Error loading window settings: {e}")
    
    def save_window_settings(self):
        """Save current window geometry and settings"""
        try:
            # Save window geometry
            if not self.isMaximized():
                geometry = self.geometry()
                self.settings.set_window_geometry(
                    geometry.x(), geometry.y(), 
                    geometry.width(), geometry.height()
                )
            
            # Save maximized state
            self.settings.set_window_maximized(self.isMaximized())
            
            # Save splitter sizes (if splitter exists)
            central_widget = self.centralWidget()
            if central_widget:
                layout = central_widget.layout()
                if layout and layout.count() > 0:
                    splitter = layout.itemAt(0).widget()
                    if isinstance(splitter, QSplitter):
                        self.settings.set_splitter_sizes(splitter.sizes())
            
            # Save settings to file
            self.settings.save_settings()
            
            self.logger.info("Window settings saved")
            
        except Exception as e:
            self.logger.error(f"Error saving window settings: {e}")
    
    def setup_temp_folder(self):
        """Setup temp folder from settings or default"""
        # Try to load from settings first
        saved_temp_folder = self.settings.get_temp_folder()
        if saved_temp_folder and Path(saved_temp_folder).exists():
            self.set_temp_folder(saved_temp_folder)
            self.logger.info(f"Loaded temp folder from settings: {saved_temp_folder}")
            return
        
        # Try to use a default temp folder
        default_temp = Path.cwd() / "temp"
        if default_temp.exists():
            self.set_temp_folder(str(default_temp))
    
    def select_temp_folder(self):
        """Open folder selection dialog"""
        folder = QFileDialog.getExistingDirectory(
            self,
            "Select Temp Folder for PDF Files",
            str(Path.home()),
            QFileDialog.Option.ShowDirsOnly
        )
        
        if folder:
            self.set_temp_folder(folder)
    
    def set_temp_folder(self, folder_path):
        """Set the temp folder and update UI"""
        self.temp_folder = Path(folder_path)
        self.folder_label.setText(f"Temp Folder: {folder_path}")
        self.folder_label.setStyleSheet("QLabel { color: black; }")
        
        self.folder_status_label.setText(f"Temp Folder: {self.temp_folder.name}")
        self.folder_status_label.setStyleSheet("QLabel { color: green; }")
        
        # Save to settings
        self.settings.set_temp_folder(folder_path)
        self.settings.save_settings()
        
        # Initialize PDF browser
        self.pdf_browser = PDFBrowser(str(self.temp_folder))
        
        # Setup folder monitoring
        self.setup_folder_monitoring()
        
        # Refresh PDF list
        self.refresh_pdf_list()
        
        self.status_bar.showMessage(f"Temp folder set to: {folder_path}")
        self.logger.info(f"Temp folder set to: {folder_path}")
    
    def setup_folder_monitoring(self):
        """Setup automatic folder monitoring"""
        if not self.temp_folder or not self.monitoring_enabled:
            return
        
        try:
            # Stop existing watcher if any
            if self.folder_watcher:
                self.folder_watcher.stop_monitoring()
            
            # Create new folder watcher
            self.folder_watcher = FolderWatcher()
            
            # Configure folder watcher
            self.folder_watcher.set_folder(str(self.temp_folder), recursive=False)
            self.folder_watcher.set_callback(self.on_file_detected)
            
            # Start monitoring
            if self.folder_watcher.start_monitoring():
                self.logger.info(f"Started folder monitoring for: {self.temp_folder}")
            else:
                self.logger.error("Failed to start folder monitoring")
            
        except Exception as e:
            self.logger.error(f"Error setting up folder monitoring: {e}")
    
    def on_file_added(self, file_path):
        """Handle file added to monitored folder"""
        self.logger.info(f"File added: {file_path}")
        
        # Check if it's a PDF file
        if file_path.lower().endswith('.pdf'):
            self.status_bar.showMessage(f"New PDF detected: {Path(file_path).name}")
            
            # Refresh PDF list after a short delay to ensure file is fully written
            QTimer.singleShot(1000, self.refresh_pdf_list)
    
    def on_file_removed(self, file_path):
        """Handle file removed from monitored folder"""
        self.logger.info(f"File removed: {file_path}")
        
        if file_path.lower().endswith('.pdf'):
            self.status_bar.showMessage(f"PDF removed: {Path(file_path).name}")
            self.refresh_pdf_list()
    
    def on_file_detected(self, file_path):
        """Handle file detected by folder watcher"""
        self.logger.info(f"PDF file detected: {file_path}")
        
        # Check if it's a PDF file
        if file_path.lower().endswith('.pdf'):
            self.status_bar.showMessage(f"New PDF detected: {Path(file_path).name}")
            
            # Refresh PDF list after a short delay to ensure file is fully written
            QTimer.singleShot(1000, self.refresh_pdf_list)
    
    def smart_refresh_pdf_list(self):
        """Smart refresh that avoids interrupting user interactions"""
        # Check if user is actively interacting with the PDF list
        if (self.pdf_list.hasFocus() or 
            len(self.pdf_list.selectedItems()) > 0 or
            self.fax_job_window is not None):
            # User is busy - defer refresh for another 10 seconds
            QTimer.singleShot(10000, self.smart_refresh_pdf_list)
            return
        
        # Safe to refresh
        self.refresh_pdf_list()
    
    def refresh_pdf_list(self):
        """Refresh the PDF file list while preserving user selections"""
        if not self.pdf_browser:
            return
        
        try:
            # SAVE current selections before clearing
            selected_paths = []
            for item in self.pdf_list.selectedItems():
                selected_paths.append(item.data(Qt.ItemDataRole.UserRole))
            
            # Get PDF files
            pdf_files = self.pdf_browser.get_pdf_files()
            
            # Clear current list
            self.pdf_list.clear()
            
            # Add PDF files to list
            for pdf_file in pdf_files:
                item = QListWidgetItem(pdf_file.name)
                item.setData(Qt.ItemDataRole.UserRole, str(pdf_file.file_path))
                self.pdf_list.addItem(item)
                
                # RESTORE selection if this file was previously selected
                if str(pdf_file.file_path) in selected_paths:
                    item.setSelected(True)
            
            # Update status
            count = len(pdf_files)
            self.pdf_count_label.setText(f"PDF Files: {count}")
            
            # Update selection counter
            selected_count = len(selected_paths)
            if selected_count > 0:
                self.status_bar.showMessage(f"{selected_count} PDF file(s) selected")
            
            # Enable/disable new fax button
            self.new_fax_btn.setEnabled(count > 0 and self.db_connection is not None)
            
            if count > 0:
                self.pdf_count_label.setStyleSheet("QLabel { color: green; }")
            else:
                self.pdf_count_label.setStyleSheet("QLabel { color: #666; }")
                
        except Exception as e:
            self.logger.error(f"Error refreshing PDF list: {e}")
            self.status_bar.showMessage(f"Error refreshing PDF list: {str(e)}")
    
    def create_new_fax_job(self):
        """Create a new fax job"""
        if not self.pdf_browser or not self.db_connection:
            QMessageBox.warning(
                self,
                "Cannot Create Fax Job",
                "Please ensure both database connection and temp folder are configured."
            )
            return
        
        # Get selected PDFs
        selected_items = self.pdf_list.selectedItems()
        if not selected_items:
            QMessageBox.information(
                self,
                "No PDFs Selected",
                "Please select one or more PDF files to include in the fax job."
            )
            return
        
        # Get selected PDF paths
        selected_pdfs = []
        for item in selected_items:
            pdf_path = item.data(Qt.ItemDataRole.UserRole)
            selected_pdfs.append(pdf_path)
        
        # Open fax job window
        if self.fax_job_window:
            self.fax_job_window.close()
        
        self.fax_job_window = FaxJobWindow(
            selected_pdfs,
            self.contact_repo,
            self.fax_job_repo,
            self
        )
        self.fax_job_window.show()
    
    def open_contact_manager(self):
        """Open contact management window"""
        if not self.contact_repo:
            QMessageBox.warning(
                self,
                "Database Not Connected",
                "Please ensure database connection is established."
            )
            return
        
        if self.contact_window:
            self.contact_window.close()
        
        self.contact_window = ContactWindow(self.contact_repo, self)
        self.contact_window.show()
    
    def open_fax_history(self):
        """Open fax history window"""
        if not self.contact_repo or not self.fax_job_repo:
            QMessageBox.warning(
                self,
                "Database Not Connected",
                "Please ensure database connection is established."
            )
            return
        
        # Create and show fax history window
        history_window = FaxHistoryWindow(
            self.fax_job_repo,
            self.contact_repo,
            self
        )
        
        # Connect resend signal to handle fax resending
        history_window.fax_selected.connect(self.handle_fax_resend)
        
        history_window.exec()
    
    def handle_fax_resend(self, fax_job):
        """Handle fax resend request from history window"""
        try:
            # Check if the original PDF file still exists
            if fax_job.pdf_path and os.path.exists(fax_job.pdf_path):
                # Open fax job window with the original PDF
                if self.fax_job_window:
                    self.fax_job_window.close()
                
                self.fax_job_window = FaxJobWindow(
                    [fax_job.pdf_path],
                    self.contact_repo,
                    self.fax_job_repo,
                    self
                )
                
                # Pre-populate with original fax job data
                if hasattr(self.fax_job_window, 'populate_from_fax_job'):
                    self.fax_job_window.populate_from_fax_job(fax_job)
                
                self.fax_job_window.show()
            else:
                QMessageBox.warning(
                    self,
                    "PDF Not Found",
                    f"The original PDF file for this fax job could not be found:\n{fax_job.pdf_path or 'No path recorded'}\n\n"
                    "Please select the PDF files manually to resend this fax."
                )
                # Open empty fax job window
                self.create_new_fax_job()
                
        except Exception as e:
            self.logger.error(f"Error handling fax resend: {e}")
            QMessageBox.critical(
                self,
                "Resend Error",
                f"An error occurred while preparing to resend the fax:\n{str(e)}"
            )
    
    def on_pdf_selection_changed(self):
        """Handle PDF selection change"""
        selected_items = self.pdf_list.selectedItems()
        
        if not selected_items:
            self.pdf_info.clear()
            return
        
        # Show info for selected PDFs
        info_text = []
        for item in selected_items:
            pdf_path = item.data(Qt.ItemDataRole.UserRole)
            try:
                # Get file info
                file_path = Path(pdf_path)
                file_size = file_path.stat().st_size
                size_mb = file_size / (1024 * 1024)
                
                info_text.append(f"File: {file_path.name}")
                info_text.append(f"Size: {size_mb:.1f} MB")
                info_text.append(f"Path: {pdf_path}")
                info_text.append("-" * 40)
                
            except Exception as e:
                info_text.append(f"Error reading {pdf_path}: {e}")
                info_text.append("-" * 40)
        
        self.pdf_info.setText("\n".join(info_text))
    
    def view_selected_pdf(self):
        """View selected PDF"""
        selected_items = self.pdf_list.selectedItems()
        
        if not selected_items:
            QMessageBox.information(
                self,
                "No PDF Selected",
                "Please select a PDF file to view."
            )
            return
        
        if len(selected_items) > 1:
            QMessageBox.information(
                self,
                "Multiple PDFs Selected",
                "Please select only one PDF file to view."
            )
            return
        
        pdf_path = selected_items[0].data(Qt.ItemDataRole.UserRole)
        
        try:
            # Create and show PDF viewer dialog
            from pdf.pdf_viewer import PDFViewerDialog
            viewer = PDFViewerDialog(pdf_path, self)
            viewer.exec()
            
            self.status_bar.showMessage(f"Opened PDF viewer for: {Path(pdf_path).name}")
            
        except Exception as e:
            self.logger.error(f"Error opening PDF viewer: {e}")
            QMessageBox.critical(
                self,
                "PDF Viewer Error",
                f"Failed to open PDF viewer:\n{str(e)}"
            )
    
    def edit_selected_pdf(self):
        """Edit selected PDF"""
        selected_items = self.pdf_list.selectedItems()
        
        if not selected_items:
            QMessageBox.information(
                self,
                "No PDF Selected",
                "Please select a PDF file to edit."
            )
            return
        
        if len(selected_items) > 1:
            QMessageBox.information(
                self,
                "Multiple PDFs Selected",
                "Please select only one PDF file to edit."
            )
            return
        
        pdf_path = selected_items[0].data(Qt.ItemDataRole.UserRole)
        
        try:
            # Create and show PDF editor dialog
            from pdf.pdf_viewer import PDFViewerDialog
            editor = PDFViewerDialog(pdf_path, self)
            editor.exec()
            
            self.status_bar.showMessage(f"Opened PDF editor for: {Path(pdf_path).name}")
            
        except Exception as e:
            self.logger.error(f"Error opening PDF editor: {e}")
            QMessageBox.critical(
                self,
                "PDF Editor Error",
                f"Failed to open PDF editor:\n{str(e)}"
            )
    
    def open_settings(self):
        """Open settings configuration window"""
        try:
            from .settings_window import SettingsWindow
            
            settings_window = SettingsWindow(self)
            if settings_window.exec() == SettingsWindow.DialogCode.Accepted:
                # Settings were saved, update any relevant UI elements
                self.status_bar.showMessage("Settings updated successfully")
                self.logger.info("Settings updated by user")
                
                # Refresh monitoring settings if changed
                self.monitoring_enabled = self.settings.is_folder_monitoring_enabled()
                if self.temp_folder:
                    self.setup_folder_monitoring()
                
                # Update refresh timer interval if changed
                new_interval = self.settings.get_auto_refresh_interval()
                if self.update_timer.interval() != new_interval:
                    self.update_timer.setInterval(new_interval)
                    self.logger.info(f"Updated refresh interval to {new_interval}ms")
            
        except Exception as e:
            self.logger.error(f"Error opening settings window: {e}")
            QMessageBox.critical(
                self,
                "Settings Error",
                f"Failed to open settings window:\n{str(e)}"
            )
    
    def show_about(self):
        """Show about dialog"""
        QMessageBox.about(
            self,
            "About MCFax",
            """
            <h3>MCFax - Fax Management System</h3>
            <p>Version 1.0.0</p>
            <p>A comprehensive fax management solution for MultiTech FaxFinder FF240.R1</p>
            <p><b>Features:</b></p>
            <ul>
                <li>PDF processing and editing</li>
                <li>Cover page generation</li>
                <li>Contact management</li>
                <li>Fax job tracking</li>
                <li>FaxFinder integration</li>
                <li>Settings management</li>
            </ul>
            <p>© 2025 MCFax Solutions</p>
            """
        )
    
    def closeEvent(self, event):
        """Handle application close event"""
        # Save window settings before closing
        self.save_window_settings()
        
        # Stop folder monitoring
        if self.folder_watcher:
            self.folder_watcher.stop_monitoring()
            self.logger.info("Folder monitoring stopped")
        
        # Close child windows
        if self.fax_job_window:
            self.fax_job_window.close()
        if self.contact_window:
            self.contact_window.close()
        
        # Close database connection
        if self.db_connection and hasattr(self.db_connection, 'disconnect'):
            self.db_connection.disconnect()
        
        self.logger.info("MCFax Application closed")
        event.accept()
