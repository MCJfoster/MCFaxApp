"""
Fax package for MCFax Application
Handles fax job XML generation and submission
"""

from .xml_generator import FaxXMLGenerator, create_fax_xml, validate_fax_xml
from .faxfinder_api import FaxFinderAPI, create_api_client, test_api_connection

__all__ = [
    'FaxXMLGenerator',
    'create_fax_xml', 
    'validate_fax_xml',
    'FaxFinderAPI',
    'create_api_client',
    'test_api_connection'
]
