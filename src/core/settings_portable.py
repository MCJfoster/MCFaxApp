"""
Portable Settings Management Module
Handles persistent application configuration for MCFax with portable settings
"""

import json
import logging
import sys
from pathlib import Path
from typing import Dict, Any, Optional
from PyQt6.QtCore import QSettings, QStandardPaths

class SettingsManager:
    """Manages application settings with JSON-based persistence in application folder"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Default settings structure
        self.default_settings = {
            "paths": {
                "temp_folder": "",
                "recent_folders": [],
                "last_export_folder": ""
            },
            "ui": {
                "window_geometry": {
                    "x": 100,
                    "y": 100,
                    "width": 1200,
                    "height": 800
                },
                "splitter_sizes": [600, 400],
                "main_window_maximized": False
            },
            "fax_defaults": {
                "priority": "Medium",
                "max_attempts": 3,
                "retry_interval": 5,
                "sender_name": "",
                "sender_email": "",
                "include_cover_page": True
            },
            "sender_info": {
                "from_name": "",
                "from_company": "The Spine Hospital Louisiana",
                "from_phone": "(225) 906-4805",
                "from_fax": "(225) 763-2085"
            },
            "pdf_settings": {
                "default_redaction_color": "#000000",
                "default_brush_size": 10,
                "auto_save_edits": True,
                "preview_quality": "high",
                "default_zoom_level": 1.0
            },
            "system": {
                "auto_refresh_interval": 5000,
                "enable_folder_monitoring": True,
                "log_level": "INFO",
                "backup_settings": True
            },
            "faxfinder": {
                "host": "",
                "username": "",
                "password": "",
                "use_https": False,
                "auto_submit": False
            },
            "database": {
                "server": "10.70.1.251",
                "database": "MCFAX",
                "username": "SA",
                "password": "Blue$8080"
            }
        }
        
        # Settings file path - portable location
        self.settings_file = self._get_settings_file_path()
        self.backup_file = self.settings_file.with_suffix('.bak')
        
        # Current settings
        self.settings = self.default_settings.copy()
        
        # Load existing settings
        self.load_settings()
        
        # Ensure settings file exists with defaults
        self.ensure_settings_file_exists()
        
        # Ensure application folders exist
        self.ensure_app_folders_exist()
    
    def _get_settings_file_path(self) -> Path:
        """Get the settings file path - use application folder for portability"""
        # Check if running from PyInstaller executable
        if getattr(sys, 'frozen', False):
            # Running from PyInstaller executable
            app_dir = Path(sys.executable).parent
        else:
            # Running from source code
            app_dir = Path(__file__).parent.parent.parent
        
        # Ensure the application directory exists
        app_dir.mkdir(parents=True, exist_ok=True)
        
        return app_dir / "settings.json"
    
    def _get_app_directory(self) -> Path:
        """Get the application directory"""
        if getattr(sys, 'frozen', False):
            # Running from PyInstaller executable
            return Path(sys.executable).parent
        else:
            # Running from source code
            return Path(__file__).parent.parent.parent
    
    def ensure_app_folders_exist(self) -> None:
        """Ensure all required application folders exist"""
        app_dir = self._get_app_directory()
        folders = ['xml', 'processed', 'logs', 'temp', 'assets']
        
        for folder in folders:
            folder_path = app_dir / folder
            folder_path.mkdir(exist_ok=True)
            self.logger.debug(f"Ensured folder exists: {folder_path}")
    
    def load_settings(self) -> bool:
        """Load settings from file"""
        try:
            if self.settings_file.exists():
                with open(self.settings_file, 'r', encoding='utf-8') as f:
                    loaded_settings = json.load(f)
                
                # Merge with defaults to ensure all keys exist
                self.settings = self._merge_settings(self.default_settings, loaded_settings)
                
                self.logger.info(f"Settings loaded from: {self.settings_file}")
                return True
            else:
                self.logger.info("No settings file found, using defaults")
                return False
                
        except Exception as e:
            self.logger.error(f"Error loading settings: {e}")
            
            # Try to load backup
            if self.backup_file.exists():
                try:
                    with open(self.backup_file, 'r', encoding='utf-8') as f:
                        loaded_settings = json.load(f)
                    
                    self.settings = self._merge_settings(self.default_settings, loaded_settings)
                    self.logger.info("Settings restored from backup")
                    return True
                except Exception as backup_error:
                    self.logger.error(f"Error loading backup settings: {backup_error}")
            
            # Fall back to defaults
            self.settings = self.default_settings.copy()
            return False
    
    def save_settings(self) -> bool:
        """Save settings to file"""
        try:
            # Create backup if enabled
            if self.get("system.backup_settings", True) and self.settings_file.exists():
                try:
                    import shutil
                    shutil.copy2(self.settings_file, self.backup_file)
                except Exception as e:
                    self.logger.warning(f"Failed to create settings backup: {e}")
            
            # Save current settings
            with open(self.settings_file, 'w', encoding='utf-8') as f:
                json.dump(self.settings, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"Settings saved to: {self.settings_file}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error saving settings: {e}")
            return False
    
    def _merge_settings(self, defaults: Dict[str, Any], loaded: Dict[str, Any]) -> Dict[str, Any]:
        """Recursively merge loaded settings with defaults"""
        result = defaults.copy()
        
        for key, value in loaded.items():
            if key in result:
                if isinstance(result[key], dict) and isinstance(value, dict):
                    result[key] = self._merge_settings(result[key], value)
                else:
                    result[key] = value
            else:
                result[key] = value
        
        return result
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get a setting value using dot notation (e.g., 'paths.temp_folder')"""
        try:
            keys = key.split('.')
            value = self.settings
            
            for k in keys:
                value = value[k]
            
            return value
            
        except (KeyError, TypeError):
            return default
    
    def set(self, key: str, value: Any) -> None:
        """Set a setting value using dot notation"""
        keys = key.split('.')
        setting = self.settings
        
        # Navigate to the parent dictionary
        for k in keys[:-1]:
            if k not in setting:
                setting[k] = {}
            setting = setting[k]
        
        # Set the value
        setting[keys[-1]] = value
    
    def get_temp_folder(self) -> Optional[str]:
        """Get the configured temp folder"""
        folder = self.get("paths.temp_folder")
        return folder if folder else None
    
    def set_temp_folder(self, folder_path: str) -> None:
        """Set the temp folder and add to recent folders"""
        self.set("paths.temp_folder", folder_path)
        
        # Add to recent folders
        recent = self.get("paths.recent_folders", [])
        if folder_path in recent:
            recent.remove(folder_path)
        recent.insert(0, folder_path)
        
        # Keep only last 10 recent folders
        self.set("paths.recent_folders", recent[:10])
    
    def get_recent_folders(self) -> list:
        """Get list of recent folders"""
        return self.get("paths.recent_folders", [])
    
    def get_window_geometry(self) -> Dict[str, int]:
        """Get window geometry settings"""
        return self.get("ui.window_geometry", self.default_settings["ui"]["window_geometry"])
    
    def set_window_geometry(self, x: int, y: int, width: int, height: int) -> None:
        """Set window geometry"""
        self.set("ui.window_geometry", {
            "x": x,
            "y": y,
            "width": width,
            "height": height
        })
    
    def get_splitter_sizes(self) -> list:
        """Get splitter sizes"""
        return self.get("ui.splitter_sizes", [600, 400])
    
    def set_splitter_sizes(self, sizes: list) -> None:
        """Set splitter sizes"""
        self.set("ui.splitter_sizes", sizes)
    
    def is_window_maximized(self) -> bool:
        """Check if window should be maximized"""
        return self.get("ui.main_window_maximized", False)
    
    def set_window_maximized(self, maximized: bool) -> None:
        """Set window maximized state"""
        self.set("ui.main_window_maximized", maximized)
    
    def get_fax_defaults(self) -> Dict[str, Any]:
        """Get default fax settings"""
        return self.get("fax_defaults", self.default_settings["fax_defaults"])
    
    def set_fax_default(self, key: str, value: Any) -> None:
        """Set a fax default setting"""
        self.set(f"fax_defaults.{key}", value)
    
    def get_pdf_settings(self) -> Dict[str, Any]:
        """Get PDF editor settings"""
        return self.get("pdf_settings", self.default_settings["pdf_settings"])
    
    def set_pdf_setting(self, key: str, value: Any) -> None:
        """Set a PDF editor setting"""
        self.set(f"pdf_settings.{key}", value)
    
    def get_auto_refresh_interval(self) -> int:
        """Get auto refresh interval in milliseconds"""
        return self.get("system.auto_refresh_interval", 5000)
    
    def set_auto_refresh_interval(self, interval_ms: int) -> None:
        """Set auto refresh interval"""
        self.set("system.auto_refresh_interval", interval_ms)
    
    def is_folder_monitoring_enabled(self) -> bool:
        """Check if folder monitoring is enabled"""
        return self.get("system.enable_folder_monitoring", True)
    
    def set_folder_monitoring_enabled(self, enabled: bool) -> None:
        """Enable/disable folder monitoring"""
        self.set("system.enable_folder_monitoring", enabled)
    
    def get_sender_info(self) -> Dict[str, str]:
        """Get sender information"""
        return self.get("sender_info", self.default_settings["sender_info"])
    
    def set_sender_info(self, from_name: str = None, from_company: str = None, 
                       from_phone: str = None, from_fax: str = None) -> None:
        """Set sender information"""
        if from_name is not None:
            self.set("sender_info.from_name", from_name)
        if from_company is not None:
            self.set("sender_info.from_company", from_company)
        if from_phone is not None:
            self.set("sender_info.from_phone", from_phone)
        if from_fax is not None:
            self.set("sender_info.from_fax", from_fax)
    
    def get_faxfinder_settings(self) -> Dict[str, Any]:
        """Get FaxFinder connection settings"""
        return self.get("faxfinder", self.default_settings["faxfinder"])
    
    def set_faxfinder_settings(self, host: str = None, username: str = None, 
                              password: str = None, use_https: bool = None, 
                              auto_submit: bool = None) -> None:
        """Set FaxFinder connection settings"""
        if host is not None:
            self.set("faxfinder.host", host)
        if username is not None:
            self.set("faxfinder.username", username)
        if password is not None:
            self.set("faxfinder.password", password)
        if use_https is not None:
            self.set("faxfinder.use_https", use_https)
        if auto_submit is not None:
            self.set("faxfinder.auto_submit", auto_submit)
    
    def reset_to_defaults(self) -> None:
        """Reset all settings to defaults"""
        self.settings = self.default_settings.copy()
        self.logger.info("Settings reset to defaults")
    
    def export_settings(self, file_path: str) -> bool:
        """Export settings to a file"""
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(self.settings, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"Settings exported to: {file_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error exporting settings: {e}")
            return False
    
    def import_settings(self, file_path: str) -> bool:
        """Import settings from a file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                imported_settings = json.load(f)
            
            # Merge with defaults to ensure all keys exist
            self.settings = self._merge_settings(self.default_settings, imported_settings)
            
            self.logger.info(f"Settings imported from: {file_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error importing settings: {e}")
            return False
    
    def ensure_settings_file_exists(self) -> None:
        """Ensure settings file exists with default values"""
        if not self.settings_file.exists():
            self.logger.info("Creating settings file with default values")
            self.save_settings()
    
    def get_settings_file_path(self) -> str:
        """Get the settings file path as string"""
        return str(self.settings_file)
    
    def __enter__(self):
        """Context manager entry"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - auto-save settings"""
        self.save_settings()

# Global settings instance
_settings_instance = None

def get_settings() -> SettingsManager:
    """Get the global settings instance"""
    global _settings_instance
    if _settings_instance is None:
        _settings_instance = SettingsManager()
    return _settings_instance

def save_settings() -> bool:
    """Save the global settings"""
    return get_settings().save_settings()
