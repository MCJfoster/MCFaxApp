"""
FaxFinder API Integration Module
Handles communication with MultiTech FaxFinder FF240.R1 Web Services API
"""

import os
import logging
import base64
import requests
from typing import Optional, Dict, Any, List
from datetime import datetime
from requests.auth import HTTPBasicAuth
import xml.etree.ElementTree as ET

class FaxFinderAPI:
    """
    API client for FaxFinder FF240.R1 Web Services
    """
    
    def __init__(self, host: str, username: str, password: str, use_https: bool = False):
        """
        Initialize FaxFinder API client
        
        Args:
            host: FaxFinder IP address or hostname
            username: API username
            password: API password
            use_https: Whether to use HTTPS (default: False for FF240.R1)
        """
        self.host = host
        self.username = username
        self.password = password
        self.use_https = use_https
        self.base_url = f"{'https' if use_https else 'http'}://{host}"
        self.auth = HTTPBasicAuth(username, password)
        self.logger = logging.getLogger(__name__)
        
        # API endpoints
        self.endpoints = {
            'send_fax': '/ffws/v1/ofax',
            'fax_status': '/ffws/v1/ofax/{fax_entry_url}',
            'receive_fax': '/ffws/v1/ifax',
            'fax_list': '/ffws/v1/ofax'
        }
    
    def test_connection(self) -> Dict[str, Any]:
        """
        Test connection to FaxFinder API
        
        Returns:
            dict: Connection test results
        """
        try:
            # Try to get fax list to test connection
            url = f"{self.base_url}{self.endpoints['fax_list']}"
            response = requests.get(url, auth=self.auth, timeout=10)
            
            return {
                'success': True,
                'status_code': response.status_code,
                'response_time': response.elapsed.total_seconds(),
                'message': 'Connection successful' if response.status_code == 200 else f'HTTP {response.status_code}'
            }
            
        except requests.exceptions.ConnectionError:
            return {
                'success': False,
                'error': 'Connection failed - check host and network connectivity'
            }
        except requests.exceptions.Timeout:
            return {
                'success': False,
                'error': 'Connection timeout - check host responsiveness'
            }
        except requests.exceptions.RequestException as e:
            return {
                'success': False,
                'error': f'Request error: {str(e)}'
            }
    
    def submit_fax_job(self, fax_job, contact, pdf_path: str) -> Dict[str, Any]:
        """
        Submit a fax job directly using FaxJob and Contact objects
        
        Args:
            fax_job: FaxJob object with job details
            contact: Contact object with recipient details
            pdf_path: Path to PDF file to send
            
        Returns:
            dict: Send fax results
        """
        try:
            # Import here to avoid circular imports
            from .xml_generator import FaxXMLGenerator
            
            # Generate FaxFinder-compatible XML with embedded PDF
            generator = FaxXMLGenerator()
            xml_content = generator.generate_faxfinder_xml(fax_job, contact, pdf_path)
            
            # Log XML details for debugging
            self.logger.info(f"Submitting to FaxFinder:")
            self.logger.info(f"  URL: {self.base_url}{self.endpoints['send_fax']}")
            self.logger.info(f"  XML length: {len(xml_content)} characters")
            
            # Check if XML contains base64 content (using correct format)
            if '<content>' in xml_content and 'base64' in xml_content:
                # Find the base64 content using the correct format
                start_marker = '<content>'
                end_marker = '</content>'
                start_pos = xml_content.find(start_marker)
                end_pos = xml_content.find(end_marker, start_pos)
                if start_pos != -1 and end_pos != -1:
                    start_pos += len(start_marker)
                    base64_content = xml_content[start_pos:end_pos].strip()
                    self.logger.info(f"  Base64 PDF content: {len(base64_content)} characters")
                    if len(base64_content) > 100:
                        self.logger.info(f"  Base64 sample: {base64_content[:50]}...{base64_content[-50:]}")
                    else:
                        self.logger.warning(f"  Base64 content seems too short: {len(base64_content)} chars")
                else:
                    self.logger.error("  Base64 content markers found but content extraction failed")
            else:
                self.logger.warning("  No base64 content found in XML - this may cause submission failure")
            
            # Send to FaxFinder
            url = f"{self.base_url}{self.endpoints['send_fax']}"
            headers = {
                'Content-Type': 'application/xml',
                'Accept': 'application/xml'
            }
            
            response = requests.post(
                url, 
                data=xml_content, 
                headers=headers, 
                auth=self.auth,
                timeout=30
            )
            
            if response.status_code in [200, 201]:
                # Parse response to get fax_entry_url
                fax_entry_url = self._parse_fax_response(response.text)
                
                return {
                    'success': True,
                    'fax_entry_url': fax_entry_url,
                    'status_code': response.status_code,
                    'response': response.text,
                    'message': 'Fax submitted successfully'
                }
            else:
                return {
                    'success': False,
                    'status_code': response.status_code,
                    'response': response.text,
                    'error': f'HTTP {response.status_code}: {response.text}'
                }
                
        except Exception as e:
            self.logger.error(f"Error submitting fax job: {e}")
            return {
                'success': False,
                'error': f'Submit fax error: {str(e)}'
            }

    def send_fax(self, xml_content: str, pdf_path: str) -> Dict[str, Any]:
        """
        Send a fax using the FaxFinder API
        
        Args:
            xml_content: XML content with fax job details
            pdf_path: Path to PDF file to send
            
        Returns:
            dict: Send fax results
        """
        try:
            # Read and encode PDF
            with open(pdf_path, 'rb') as pdf_file:
                pdf_base64 = base64.b64encode(pdf_file.read()).decode('utf-8')
            
            # Insert base64 PDF into XML
            # This is a simplified approach - in production, you'd want more sophisticated XML handling
            xml_with_pdf = self._insert_pdf_into_xml(xml_content, pdf_base64)
            
            # Send request
            url = f"{self.base_url}{self.endpoints['send_fax']}"
            headers = {
                'Content-Type': 'application/xml',
                'Accept': 'application/xml'
            }
            
            response = requests.post(
                url, 
                data=xml_with_pdf, 
                headers=headers, 
                auth=self.auth,
                timeout=30
            )
            
            if response.status_code == 200:
                # Parse response to get fax_entry_url
                fax_entry_url = self._parse_fax_response(response.text)
                
                return {
                    'success': True,
                    'fax_entry_url': fax_entry_url,
                    'status_code': response.status_code,
                    'response': response.text,
                    'message': 'Fax submitted successfully'
                }
            else:
                return {
                    'success': False,
                    'status_code': response.status_code,
                    'response': response.text,
                    'error': f'HTTP {response.status_code}: {response.text}'
                }
                
        except FileNotFoundError:
            return {
                'success': False,
                'error': f'PDF file not found: {pdf_path}'
            }
        except Exception as e:
            self.logger.error(f"Error sending fax: {e}")
            return {
                'success': False,
                'error': f'Send fax error: {str(e)}'
            }
    
    def get_fax_status(self, fax_entry_url: str) -> Dict[str, Any]:
        """
        Get status of a sent fax
        
        Args:
            fax_entry_url: Fax entry URL returned from send_fax
            
        Returns:
            dict: Fax status information
        """
        try:
            url = f"{self.base_url}{self.endpoints['fax_status'].format(fax_entry_url=fax_entry_url)}"
            response = requests.get(url, auth=self.auth, timeout=10)
            
            if response.status_code == 200:
                status_info = self._parse_status_response(response.text)
                return {
                    'success': True,
                    'status_info': status_info,
                    'raw_response': response.text
                }
            else:
                return {
                    'success': False,
                    'status_code': response.status_code,
                    'error': f'HTTP {response.status_code}: {response.text}'
                }
                
        except Exception as e:
            self.logger.error(f"Error getting fax status: {e}")
            return {
                'success': False,
                'error': f'Status check error: {str(e)}'
            }
    
    def get_received_faxes(self) -> Dict[str, Any]:
        """
        Get list of received faxes
        
        Returns:
            dict: Received fax information
        """
        try:
            url = f"{self.base_url}{self.endpoints['receive_fax']}"
            response = requests.get(url, auth=self.auth, timeout=10)
            
            if response.status_code == 200:
                received_faxes = self._parse_received_faxes(response.text)
                return {
                    'success': True,
                    'received_faxes': received_faxes,
                    'count': len(received_faxes),
                    'raw_response': response.text
                }
            else:
                return {
                    'success': False,
                    'status_code': response.status_code,
                    'error': f'HTTP {response.status_code}: {response.text}'
                }
                
        except Exception as e:
            self.logger.error(f"Error getting received faxes: {e}")
            return {
                'success': False,
                'error': f'Receive fax error: {str(e)}'
            }
    
    def download_received_fax(self, fax_url: str, output_path: str) -> Dict[str, Any]:
        """
        Download a received fax PDF
        
        Args:
            fax_url: URL of the received fax
            output_path: Path to save the downloaded PDF
            
        Returns:
            dict: Download results
        """
        try:
            response = requests.get(fax_url, auth=self.auth, timeout=30)
            
            if response.status_code == 200:
                # Create output directory if needed
                os.makedirs(os.path.dirname(output_path), exist_ok=True)
                
                # Save PDF
                with open(output_path, 'wb') as f:
                    f.write(response.content)
                
                return {
                    'success': True,
                    'output_path': output_path,
                    'file_size': len(response.content),
                    'message': 'Fax downloaded successfully'
                }
            else:
                return {
                    'success': False,
                    'status_code': response.status_code,
                    'error': f'HTTP {response.status_code}: Failed to download fax'
                }
                
        except Exception as e:
            self.logger.error(f"Error downloading fax: {e}")
            return {
                'success': False,
                'error': f'Download error: {str(e)}'
            }
    
    def _insert_pdf_into_xml(self, xml_content: str, pdf_base64: str) -> str:
        """
        Insert base64-encoded PDF into XML content
        
        Args:
            xml_content: Original XML content
            pdf_base64: Base64-encoded PDF data
            
        Returns:
            str: XML with embedded PDF
        """
        try:
            # Parse XML
            root = ET.fromstring(xml_content)
            
            # Find Document element and add PDF data
            document = root.find('Document')
            if document is not None:
                # Add PDF data element
                pdf_data = ET.SubElement(document, 'PDFData')
                pdf_data.text = pdf_base64
                
                # Add encoding attribute
                pdf_data.set('encoding', 'base64')
            
            # Convert back to string
            return ET.tostring(root, encoding='unicode')
            
        except Exception as e:
            self.logger.error(f"Error inserting PDF into XML: {e}")
            # Fallback: simple string replacement (not recommended for production)
            return xml_content.replace('</Document>', f'<PDFData encoding="base64">{pdf_base64}</PDFData></Document>')
    
    def _parse_fax_response(self, response_text: str) -> Optional[str]:
        """
        Parse fax submission response to extract fax_entry_url
        
        Args:
            response_text: XML response from FaxFinder
            
        Returns:
            str: Fax entry URL or None if not found
        """
        try:
            root = ET.fromstring(response_text)
            # Look for fax entry URL in response
            # This depends on the actual FaxFinder response format
            fax_entry = root.find('.//fax_entry_url')
            if fax_entry is not None:
                return fax_entry.text
            
            # Alternative: look for ID or other identifier
            fax_id = root.find('.//id')
            if fax_id is not None:
                return fax_id.text
                
            return None
            
        except Exception as e:
            self.logger.error(f"Error parsing fax response: {e}")
            return None
    
    def _parse_status_response(self, response_text: str) -> Dict[str, Any]:
        """
        Parse fax status response
        
        Args:
            response_text: XML response from FaxFinder
            
        Returns:
            dict: Parsed status information
        """
        try:
            root = ET.fromstring(response_text)
            
            status_info = {
                'status': 'Unknown',
                'pages': 0,
                'attempts': 0,
                'last_attempt': None,
                'completion_time': None
            }
            
            # Extract status information based on FaxFinder response format
            status_elem = root.find('.//status')
            if status_elem is not None:
                status_info['status'] = status_elem.text
            
            pages_elem = root.find('.//pages')
            if pages_elem is not None:
                status_info['pages'] = int(pages_elem.text or 0)
            
            attempts_elem = root.find('.//attempts')
            if attempts_elem is not None:
                status_info['attempts'] = int(attempts_elem.text or 0)
            
            return status_info
            
        except Exception as e:
            self.logger.error(f"Error parsing status response: {e}")
            return {'status': 'Parse Error', 'error': str(e)}
    
    def _parse_received_faxes(self, response_text: str) -> List[Dict[str, Any]]:
        """
        Parse received faxes response
        
        Args:
            response_text: XML response from FaxFinder
            
        Returns:
            list: List of received fax information
        """
        try:
            root = ET.fromstring(response_text)
            received_faxes = []
            
            # Find all fax entries
            for fax_elem in root.findall('.//fax'):
                fax_info = {
                    'id': None,
                    'sender': None,
                    'pages': 0,
                    'received_time': None,
                    'url': None
                }
                
                # Extract fax information
                id_elem = fax_elem.find('id')
                if id_elem is not None:
                    fax_info['id'] = id_elem.text
                
                sender_elem = fax_elem.find('sender')
                if sender_elem is not None:
                    fax_info['sender'] = sender_elem.text
                
                pages_elem = fax_elem.find('pages')
                if pages_elem is not None:
                    fax_info['pages'] = int(pages_elem.text or 0)
                
                time_elem = fax_elem.find('received_time')
                if time_elem is not None:
                    fax_info['received_time'] = time_elem.text
                
                url_elem = fax_elem.find('url')
                if url_elem is not None:
                    fax_info['url'] = url_elem.text
                
                received_faxes.append(fax_info)
            
            return received_faxes
            
        except Exception as e:
            self.logger.error(f"Error parsing received faxes: {e}")
            return []

# Utility functions
def create_api_client(host: str, username: str, password: str) -> FaxFinderAPI:
    """
    Create a FaxFinder API client with standard settings
    
    Args:
        host: FaxFinder IP address
        username: API username
        password: API password
        
    Returns:
        FaxFinderAPI: Configured API client
    """
    return FaxFinderAPI(host, username, password, use_https=False)

def test_api_connection(host: str, username: str, password: str) -> bool:
    """
    Quick test of API connection
    
    Args:
        host: FaxFinder IP address
        username: API username
        password: API password
        
    Returns:
        bool: True if connection successful
    """
    api = create_api_client(host, username, password)
    result = api.test_connection()
    return result['success']
