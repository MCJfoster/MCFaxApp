"""
Settings Window for MCFax Application
Allows users to configure FaxFinder connection and other application settings
"""

import logging
from PyQt6.QtWidgets import (
    QDialog, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QPushButton, QLabel, QLineEdit, QCheckBox, QGroupBox,
    QTabWidget, QMessageBox, QSpinBox, QComboBox
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

from core.settings import get_settings
from fax.faxfinder_api import FaxFinderAPI

class SettingsWindow(QDialog):
    """Settings configuration window"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.logger = logging.getLogger(__name__)
        self.settings = get_settings()
        
        self.setup_ui()
        self.load_current_settings()
    
    def setup_ui(self):
        """Setup the user interface"""
        self.setWindowTitle("MCFax Settings")
        self.setGeometry(200, 200, 600, 500)
        self.setModal(True)
        
        # Main layout
        main_layout = QVBoxLayout(self)
        
        # Create tab widget
        self.tab_widget = QTabWidget()
        main_layout.addWidget(self.tab_widget)
        
        # Create tabs
        self.create_faxfinder_tab()
        self.create_database_tab()
        self.create_general_tab()
        self.create_sender_tab()
        
        # Button layout
        button_layout = QHBoxLayout()
        
        # Test connection button
        self.test_btn = QPushButton("Test FaxFinder Connection")
        self.test_btn.clicked.connect(self.test_faxfinder_connection)
        button_layout.addWidget(self.test_btn)
        
        button_layout.addStretch()
        
        # Save and Cancel buttons
        save_btn = QPushButton("Save Settings")
        save_btn.clicked.connect(self.save_settings)
        save_btn.setDefault(True)
        button_layout.addWidget(save_btn)
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        main_layout.addLayout(button_layout)
    
    def create_faxfinder_tab(self):
        """Create FaxFinder configuration tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # FaxFinder Connection Settings
        faxfinder_group = QGroupBox("FaxFinder Connection Settings")
        faxfinder_layout = QGridLayout(faxfinder_group)
        
        # Host/IP Address
        faxfinder_layout.addWidget(QLabel("Host/IP Address:"), 0, 0)
        self.host_edit = QLineEdit()
        self.host_edit.setPlaceholderText("192.168.1.100 or faxfinder.local")
        faxfinder_layout.addWidget(self.host_edit, 0, 1)
        
        # Username
        faxfinder_layout.addWidget(QLabel("Username:"), 1, 0)
        self.username_edit = QLineEdit()
        self.username_edit.setPlaceholderText("admin")
        faxfinder_layout.addWidget(self.username_edit, 1, 1)
        
        # Password
        faxfinder_layout.addWidget(QLabel("Password:"), 2, 0)
        self.password_edit = QLineEdit()
        self.password_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_edit.setPlaceholderText("Enter password")
        faxfinder_layout.addWidget(self.password_edit, 2, 1)
        
        # Use HTTPS
        self.use_https_checkbox = QCheckBox("Use HTTPS (Secure Connection)")
        faxfinder_layout.addWidget(self.use_https_checkbox, 3, 0, 1, 2)
        
        # Auto Submit
        self.auto_submit_checkbox = QCheckBox("Automatically submit faxes to FaxFinder")
        faxfinder_layout.addWidget(self.auto_submit_checkbox, 4, 0, 1, 2)
        
        layout.addWidget(faxfinder_group)
        
        # Connection Status
        status_group = QGroupBox("Connection Status")
        status_layout = QVBoxLayout(status_group)
        
        self.connection_status_label = QLabel("Status: Not tested")
        self.connection_status_label.setStyleSheet("QLabel { color: #666; }")
        status_layout.addWidget(self.connection_status_label)
        
        layout.addWidget(status_group)
        
        # Help text
        help_group = QGroupBox("Configuration Help")
        help_layout = QVBoxLayout(help_group)
        
        help_text = QLabel("""
<b>FaxFinder Configuration:</b><br>
• <b>Host/IP Address:</b> The IP address or hostname of your FaxFinder device<br>
• <b>Username/Password:</b> Login credentials for the FaxFinder web interface<br>
• <b>HTTPS:</b> Enable if your FaxFinder is configured for secure connections<br>
• <b>Auto Submit:</b> Automatically send faxes to FaxFinder when created<br><br>

<b>Default FaxFinder Settings:</b><br>
• Username: admin<br>
• Password: (device default or custom)<br>
• Port: 80 (HTTP) or 443 (HTTPS)<br>
        """)
        help_text.setWordWrap(True)
        help_text.setStyleSheet("QLabel { color: #444; font-size: 11px; }")
        help_layout.addWidget(help_text)
        
        layout.addWidget(help_group)
        
        layout.addStretch()
        
        self.tab_widget.addTab(tab, "FaxFinder")
    
    def create_database_tab(self):
        """Create database configuration tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Database Connection Settings
        database_group = QGroupBox("Database Connection Settings")
        database_layout = QGridLayout(database_group)
        
        # Server/IP Address
        database_layout.addWidget(QLabel("Server/IP Address:"), 0, 0)
        self.db_server_edit = QLineEdit()
        self.db_server_edit.setPlaceholderText("10.70.1.251 or server.domain.com")
        database_layout.addWidget(self.db_server_edit, 0, 1)
        
        # Database Name
        database_layout.addWidget(QLabel("Database Name:"), 1, 0)
        self.db_database_edit = QLineEdit()
        self.db_database_edit.setPlaceholderText("MCFAX")
        database_layout.addWidget(self.db_database_edit, 1, 1)
        
        # Username
        database_layout.addWidget(QLabel("Username:"), 2, 0)
        self.db_username_edit = QLineEdit()
        self.db_username_edit.setPlaceholderText("SA")
        database_layout.addWidget(self.db_username_edit, 2, 1)
        
        # Password
        database_layout.addWidget(QLabel("Password:"), 3, 0)
        self.db_password_edit = QLineEdit()
        self.db_password_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.db_password_edit.setPlaceholderText("Enter database password")
        database_layout.addWidget(self.db_password_edit, 3, 1)
        
        layout.addWidget(database_group)
        
        # Database Status
        db_status_group = QGroupBox("Database Status")
        db_status_layout = QVBoxLayout(db_status_group)
        
        self.db_connection_status_label = QLabel("Status: Not tested")
        self.db_connection_status_label.setStyleSheet("QLabel { color: #666; }")
        db_status_layout.addWidget(self.db_connection_status_label)
        
        # Test database connection button
        self.test_db_btn = QPushButton("Test Database Connection")
        self.test_db_btn.clicked.connect(self.test_database_connection)
        db_status_layout.addWidget(self.test_db_btn)
        
        layout.addWidget(db_status_group)
        
        # Help text
        db_help_group = QGroupBox("Configuration Help")
        db_help_layout = QVBoxLayout(db_help_group)
        
        db_help_text = QLabel("""
<b>Database Configuration:</b><br>
• <b>Server/IP Address:</b> The IP address or hostname of your SQL Server<br>
• <b>Database Name:</b> The name of the MCFax database (usually "MCFAX")<br>
• <b>Username/Password:</b> SQL Server authentication credentials<br><br>

<b>Connection Requirements:</b><br>
• SQL Server must be accessible from this machine<br>
• ODBC Driver 17 for SQL Server must be installed<br>
• Database user must have appropriate permissions<br>
• TrustServerCertificate is enabled for secure connections<br><br>

<b>Default Settings:</b><br>
• Server: 10.70.1.251<br>
• Database: MCFAX<br>
• Username: SA<br>
        """)
        db_help_text.setWordWrap(True)
        db_help_text.setStyleSheet("QLabel { color: #444; font-size: 11px; }")
        db_help_layout.addWidget(db_help_text)
        
        layout.addWidget(db_help_group)
        
        layout.addStretch()
        
        self.tab_widget.addTab(tab, "Database")
    
    def create_general_tab(self):
        """Create general settings tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # System Settings
        system_group = QGroupBox("System Settings")
        system_layout = QGridLayout(system_group)
        
        # Auto refresh interval
        system_layout.addWidget(QLabel("Auto Refresh Interval:"), 0, 0)
        self.refresh_interval_spin = QSpinBox()
        self.refresh_interval_spin.setRange(1000, 60000)
        self.refresh_interval_spin.setSingleStep(1000)
        self.refresh_interval_spin.setSuffix(" ms")
        self.refresh_interval_spin.setValue(5000)
        system_layout.addWidget(self.refresh_interval_spin, 0, 1)
        
        # Enable folder monitoring
        self.folder_monitoring_checkbox = QCheckBox("Enable automatic folder monitoring")
        system_layout.addWidget(self.folder_monitoring_checkbox, 1, 0, 1, 2)
        
        # Log level
        system_layout.addWidget(QLabel("Log Level:"), 2, 0)
        self.log_level_combo = QComboBox()
        self.log_level_combo.addItems(["DEBUG", "INFO", "WARNING", "ERROR"])
        self.log_level_combo.setCurrentText("INFO")
        system_layout.addWidget(self.log_level_combo, 2, 1)
        
        layout.addWidget(system_group)
        
        # PDF Settings
        pdf_group = QGroupBox("PDF Settings")
        pdf_layout = QGridLayout(pdf_group)
        
        # Default zoom level
        pdf_layout.addWidget(QLabel("Default Zoom Level:"), 0, 0)
        self.zoom_level_spin = QSpinBox()
        self.zoom_level_spin.setRange(25, 500)
        self.zoom_level_spin.setSingleStep(25)
        self.zoom_level_spin.setSuffix("%")
        self.zoom_level_spin.setValue(100)
        pdf_layout.addWidget(self.zoom_level_spin, 0, 1)
        
        # Auto save edits
        self.auto_save_checkbox = QCheckBox("Automatically save PDF edits")
        pdf_layout.addWidget(self.auto_save_checkbox, 1, 0, 1, 2)
        
        # Preview quality
        pdf_layout.addWidget(QLabel("Preview Quality:"), 2, 0)
        self.preview_quality_combo = QComboBox()
        self.preview_quality_combo.addItems(["low", "medium", "high"])
        self.preview_quality_combo.setCurrentText("high")
        pdf_layout.addWidget(self.preview_quality_combo, 2, 1)
        
        layout.addWidget(pdf_group)
        
        # Fax Defaults
        fax_group = QGroupBox("Fax Job Defaults")
        fax_layout = QGridLayout(fax_group)
        
        # Default priority
        fax_layout.addWidget(QLabel("Default Priority:"), 0, 0)
        self.priority_combo = QComboBox()
        self.priority_combo.addItems(["1st", "High", "Medium/High", "Medium", "Medium/Low", "Low"])
        self.priority_combo.setCurrentText("Medium")
        fax_layout.addWidget(self.priority_combo, 0, 1)
        
        # Max attempts
        fax_layout.addWidget(QLabel("Max Attempts:"), 1, 0)
        self.max_attempts_spin = QSpinBox()
        self.max_attempts_spin.setRange(1, 10)
        self.max_attempts_spin.setValue(3)
        fax_layout.addWidget(self.max_attempts_spin, 1, 1)
        
        # Retry interval
        fax_layout.addWidget(QLabel("Retry Interval:"), 2, 0)
        self.retry_interval_spin = QSpinBox()
        self.retry_interval_spin.setRange(1, 60)
        self.retry_interval_spin.setValue(5)
        self.retry_interval_spin.setSuffix(" minutes")
        fax_layout.addWidget(self.retry_interval_spin, 2, 1)
        
        # Include cover page
        self.include_cover_checkbox = QCheckBox("Include cover page by default")
        self.include_cover_checkbox.setChecked(True)
        fax_layout.addWidget(self.include_cover_checkbox, 3, 0, 1, 2)
        
        layout.addWidget(fax_group)
        
        layout.addStretch()
        
        self.tab_widget.addTab(tab, "General")
    
    def create_sender_tab(self):
        """Create sender information tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Sender Information
        sender_group = QGroupBox("Default Sender Information")
        sender_layout = QGridLayout(sender_group)
        
        # From Name
        sender_layout.addWidget(QLabel("From Name:"), 0, 0)
        self.from_name_edit = QLineEdit()
        self.from_name_edit.setPlaceholderText("Your full name")
        sender_layout.addWidget(self.from_name_edit, 0, 1)
        
        # From Company
        sender_layout.addWidget(QLabel("Company:"), 1, 0)
        self.from_company_edit = QLineEdit()
        self.from_company_edit.setText("The Spine Hospital Louisiana")
        sender_layout.addWidget(self.from_company_edit, 1, 1)
        
        # From Phone
        sender_layout.addWidget(QLabel("Phone:"), 2, 0)
        self.from_phone_edit = QLineEdit()
        self.from_phone_edit.setText("(225) 906-4805")
        sender_layout.addWidget(self.from_phone_edit, 2, 1)
        
        # From Fax
        sender_layout.addWidget(QLabel("Fax Number:"), 3, 0)
        self.from_fax_edit = QLineEdit()
        self.from_fax_edit.setText("(225) 763-2085")
        sender_layout.addWidget(self.from_fax_edit, 3, 1)
        
        layout.addWidget(sender_group)
        
        # Help text
        help_group = QGroupBox("Information")
        help_layout = QVBoxLayout(help_group)
        
        help_text = QLabel("""
<b>Sender Information:</b><br>
This information will be used as defaults when creating new fax jobs and cover pages.<br>
You can override these values for individual fax jobs if needed.<br><br>

<b>Note:</b> Changes to sender information will only affect new fax jobs.<br>
Existing fax jobs will retain their original sender information.
        """)
        help_text.setWordWrap(True)
        help_text.setStyleSheet("QLabel { color: #444; font-size: 11px; }")
        help_layout.addWidget(help_text)
        
        layout.addWidget(help_group)
        
        layout.addStretch()
        
        self.tab_widget.addTab(tab, "Sender Info")
    
    def load_current_settings(self):
        """Load current settings into the form"""
        try:
            # Load FaxFinder settings
            faxfinder_settings = self.settings.get_faxfinder_settings()
            self.host_edit.setText(faxfinder_settings.get('host', ''))
            self.username_edit.setText(faxfinder_settings.get('username', ''))
            self.password_edit.setText(faxfinder_settings.get('password', ''))
            self.use_https_checkbox.setChecked(faxfinder_settings.get('use_https', False))
            self.auto_submit_checkbox.setChecked(faxfinder_settings.get('auto_submit', False))
            
            # Load general settings
            self.refresh_interval_spin.setValue(self.settings.get_auto_refresh_interval())
            self.folder_monitoring_checkbox.setChecked(self.settings.is_folder_monitoring_enabled())
            
            # Load PDF settings
            pdf_settings = self.settings.get_pdf_settings()
            zoom_percent = int(pdf_settings.get('default_zoom_level', 1.0) * 100)
            self.zoom_level_spin.setValue(zoom_percent)
            self.auto_save_checkbox.setChecked(pdf_settings.get('auto_save_edits', True))
            self.preview_quality_combo.setCurrentText(pdf_settings.get('preview_quality', 'high'))
            
            # Load fax defaults
            fax_defaults = self.settings.get_fax_defaults()
            self.priority_combo.setCurrentText(fax_defaults.get('priority', 'Medium'))
            self.max_attempts_spin.setValue(fax_defaults.get('max_attempts', 3))
            self.retry_interval_spin.setValue(fax_defaults.get('retry_interval', 5))
            self.include_cover_checkbox.setChecked(fax_defaults.get('include_cover_page', True))
            
            # Load database settings
            database_settings = self.settings.get("database", {})
            self.db_server_edit.setText(database_settings.get('server', '10.70.1.251'))
            self.db_database_edit.setText(database_settings.get('database', 'MCFAX'))
            self.db_username_edit.setText(database_settings.get('username', 'SA'))
            self.db_password_edit.setText(database_settings.get('password', ''))
            
            # Load sender info
            sender_info = self.settings.get_sender_info()
            self.from_name_edit.setText(sender_info.get('from_name', ''))
            self.from_company_edit.setText(sender_info.get('from_company', 'The Spine Hospital Louisiana'))
            self.from_phone_edit.setText(sender_info.get('from_phone', '(225) 906-4805'))
            self.from_fax_edit.setText(sender_info.get('from_fax', '(225) 763-2085'))
            
            self.logger.info("Settings loaded into form")
            
        except Exception as e:
            self.logger.error(f"Error loading settings: {e}")
            QMessageBox.warning(self, "Settings Error", f"Error loading settings: {str(e)}")
    
    def save_settings(self):
        """Save settings from the form"""
        try:
            # Save FaxFinder settings
            self.settings.set_faxfinder_settings(
                host=self.host_edit.text().strip(),
                username=self.username_edit.text().strip(),
                password=self.password_edit.text(),
                use_https=self.use_https_checkbox.isChecked(),
                auto_submit=self.auto_submit_checkbox.isChecked()
            )
            
            # Save general settings
            self.settings.set_auto_refresh_interval(self.refresh_interval_spin.value())
            self.settings.set_folder_monitoring_enabled(self.folder_monitoring_checkbox.isChecked())
            
            # Save PDF settings
            zoom_level = self.zoom_level_spin.value() / 100.0
            self.settings.set_pdf_setting('default_zoom_level', zoom_level)
            self.settings.set_pdf_setting('auto_save_edits', self.auto_save_checkbox.isChecked())
            self.settings.set_pdf_setting('preview_quality', self.preview_quality_combo.currentText())
            
            # Save fax defaults
            self.settings.set_fax_default('priority', self.priority_combo.currentText())
            self.settings.set_fax_default('max_attempts', self.max_attempts_spin.value())
            self.settings.set_fax_default('retry_interval', self.retry_interval_spin.value())
            self.settings.set_fax_default('include_cover_page', self.include_cover_checkbox.isChecked())
            
            # Save database settings
            self.settings.set("database.server", self.db_server_edit.text().strip())
            self.settings.set("database.database", self.db_database_edit.text().strip())
            self.settings.set("database.username", self.db_username_edit.text().strip())
            self.settings.set("database.password", self.db_password_edit.text())
            
            # Save sender info
            self.settings.set_sender_info(
                from_name=self.from_name_edit.text().strip(),
                from_company=self.from_company_edit.text().strip(),
                from_phone=self.from_phone_edit.text().strip(),
                from_fax=self.from_fax_edit.text().strip()
            )
            
            # Save to file
            if self.settings.save_settings():
                QMessageBox.information(self, "Settings Saved", "Settings have been saved successfully!")
                self.logger.info("Settings saved successfully")
                self.accept()
            else:
                QMessageBox.warning(self, "Save Error", "Failed to save settings to file.")
                
        except Exception as e:
            self.logger.error(f"Error saving settings: {e}")
            QMessageBox.critical(self, "Save Error", f"Error saving settings: {str(e)}")
    
    def test_faxfinder_connection(self):
        """Test the FaxFinder connection"""
        try:
            # Get connection details from form
            host = self.host_edit.text().strip()
            username = self.username_edit.text().strip()
            password = self.password_edit.text()
            use_https = self.use_https_checkbox.isChecked()
            
            # Validate required fields
            if not host:
                QMessageBox.warning(self, "Missing Information", "Please enter the FaxFinder host/IP address.")
                self.host_edit.setFocus()
                return
            
            if not username:
                QMessageBox.warning(self, "Missing Information", "Please enter the username.")
                self.username_edit.setFocus()
                return
            
            if not password:
                QMessageBox.warning(self, "Missing Information", "Please enter the password.")
                self.password_edit.setFocus()
                return
            
            # Update status
            self.connection_status_label.setText("Status: Testing connection...")
            self.connection_status_label.setStyleSheet("QLabel { color: orange; }")
            self.test_btn.setEnabled(False)
            
            # Test connection
            api = FaxFinderAPI(host, username, password, use_https)
            result = api.test_connection()
            
            if result['success']:
                self.connection_status_label.setText("Status: ✅ Connection successful!")
                self.connection_status_label.setStyleSheet("QLabel { color: green; }")
                QMessageBox.information(
                    self, 
                    "Connection Test", 
                    f"Successfully connected to FaxFinder!\n\n"
                    f"Host: {host}\n"
                    f"Protocol: {'HTTPS' if use_https else 'HTTP'}\n"
                    f"Response: {result.get('message', 'Connection OK')}"
                )
            else:
                error_msg = result.get('error', 'Unknown error')
                self.connection_status_label.setText(f"Status: ❌ Connection failed")
                self.connection_status_label.setStyleSheet("QLabel { color: red; }")
                QMessageBox.warning(
                    self, 
                    "Connection Test Failed", 
                    f"Failed to connect to FaxFinder:\n\n{error_msg}\n\n"
                    f"Please check:\n"
                    f"• Host/IP address is correct\n"
                    f"• Username and password are correct\n"
                    f"• FaxFinder is powered on and accessible\n"
                    f"• Network connectivity"
                )
            
        except Exception as e:
            self.connection_status_label.setText("Status: ❌ Test error")
            self.connection_status_label.setStyleSheet("QLabel { color: red; }")
            self.logger.error(f"Error testing FaxFinder connection: {e}")
            QMessageBox.critical(
                self, 
                "Connection Test Error", 
                f"An error occurred while testing the connection:\n\n{str(e)}"
            )
        
        finally:
            self.test_btn.setEnabled(True)
    
    def test_database_connection(self):
        """Test the database connection"""
        try:
            # Get connection details from form
            server = self.db_server_edit.text().strip()
            database = self.db_database_edit.text().strip()
            username = self.db_username_edit.text().strip()
            password = self.db_password_edit.text()
            
            # Validate required fields
            if not server:
                QMessageBox.warning(self, "Missing Information", "Please enter the database server/IP address.")
                self.db_server_edit.setFocus()
                return
            
            if not database:
                QMessageBox.warning(self, "Missing Information", "Please enter the database name.")
                self.db_database_edit.setFocus()
                return
            
            if not username:
                QMessageBox.warning(self, "Missing Information", "Please enter the database username.")
                self.db_username_edit.setFocus()
                return
            
            if not password:
                QMessageBox.warning(self, "Missing Information", "Please enter the database password.")
                self.db_password_edit.setFocus()
                return
            
            # Update status
            self.db_connection_status_label.setText("Status: Testing connection...")
            self.db_connection_status_label.setStyleSheet("QLabel { color: orange; }")
            self.test_db_btn.setEnabled(False)
            
            # Test connection
            from database.connection import DatabaseConnection
            db_conn = DatabaseConnection(server, database, username, password)
            result = db_conn.test_connection()
            
            if result['connected']:
                self.db_connection_status_label.setText("Status: ✅ Connection successful!")
                self.db_connection_status_label.setStyleSheet("QLabel { color: green; }")
                QMessageBox.information(
                    self, 
                    "Database Connection Test", 
                    f"Successfully connected to database!\n\n"
                    f"Server: {result.get('server')}\n"
                    f"Database: {result.get('database')}\n"
                    f"Server Time: {result.get('server_time')}\n"
                    f"SQL Server Version: {result.get('version', 'Unknown')[:50]}..."
                )
            else:
                error_msg = result.get('error', 'Unknown error')
                self.db_connection_status_label.setText(f"Status: ❌ Connection failed")
                self.db_connection_status_label.setStyleSheet("QLabel { color: red; }")
                QMessageBox.warning(
                    self, 
                    "Database Connection Test Failed", 
                    f"Failed to connect to database:\n\n{error_msg}\n\n"
                    f"Please check:\n"
                    f"• Server/IP address is correct\n"
                    f"• Database name is correct\n"
                    f"• Username and password are correct\n"
                    f"• SQL Server is running and accessible\n"
                    f"• ODBC Driver 17 for SQL Server is installed\n"
                    f"• Network connectivity and firewall settings"
                )
            
        except Exception as e:
            self.db_connection_status_label.setText("Status: ❌ Test error")
            self.db_connection_status_label.setStyleSheet("QLabel { color: red; }")
            self.logger.error(f"Error testing database connection: {e}")
            QMessageBox.critical(
                self, 
                "Database Connection Test Error", 
                f"An error occurred while testing the database connection:\n\n{str(e)}\n\n"
                f"Please ensure:\n"
                f"• ODBC Driver 17 for SQL Server is installed\n"
                f"• SQL Server is accessible from this machine\n"
                f"• Connection parameters are correct"
            )
        
        finally:
            self.test_db_btn.setEnabled(True)
