"""
Fax XML Generator Module
Creates FaxFinder-compliant XML files for fax job submission
"""

import os
import logging
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime
import uuid
import base64

from database.models import FaxJob, Contact, CoverPageDetails

class FaxXMLGenerator:
    """
    Generator for FaxFinder XML job files
    """
    
    def __init__(self):
        """Initialize XML generator"""
        self.logger = logging.getLogger(__name__)
    
    def generate_fax_xml(self, fax_job: FaxJob, contact: Contact, 
                        pdf_file_path: str, output_path: str) -> bool:
        """
        Generate FaxFinder-compliant XML for a fax job (for local storage - no base64)
        
        Args:
            fax_job: FaxJob object with job details
            contact: Contact object with recipient details
            pdf_file_path: Path to the PDF file to fax
            output_path: Path to save the XML file
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Create root element - FaxFinder expects "schedule_fax"
            root = ET.Element("schedule_fax")
            
            # Job identification
            job_id = fax_job.fax_id or str(uuid.uuid4())
            ET.SubElement(root, "JobID").text = str(job_id)
            ET.SubElement(root, "SubmissionTime").text = datetime.now().isoformat()
            
            # Sender information
            sender = ET.SubElement(root, "Sender")
            ET.SubElement(sender, "Name").text = fax_job.sender_name or ""
            if fax_job.sender_email:
                ET.SubElement(sender, "Email").text = fax_job.sender_email
            
            # Recipient information
            recipient = ET.SubElement(root, "Recipient")
            ET.SubElement(recipient, "Name").text = contact.name or ""
            ET.SubElement(recipient, "FaxNumber").text = contact.fax_number or ""
            if contact.organization:
                ET.SubElement(recipient, "Organization").text = contact.organization
            if contact.phone_number:
                ET.SubElement(recipient, "Phone").text = contact.phone_number
            if contact.email:
                ET.SubElement(recipient, "Email").text = contact.email
            
            # Fax settings
            settings = ET.SubElement(root, "Settings")
            ET.SubElement(settings, "Priority").text = fax_job.priority or "Medium"
            ET.SubElement(settings, "MaxAttempts").text = str(fax_job.max_attempts or 3)
            ET.SubElement(settings, "RetryInterval").text = str(fax_job.retry_interval or 5)
            
            # Cover page information
            if fax_job.cover_page_details:
                cover_page = ET.SubElement(root, "CoverPage")
                cover = fax_job.cover_page_details
                
                if cover.to:
                    ET.SubElement(cover_page, "To").text = cover.to
                if cover.attn:
                    ET.SubElement(cover_page, "Attention").text = cover.attn
                if cover.from_field:
                    ET.SubElement(cover_page, "From").text = cover.from_field
                if cover.company:
                    ET.SubElement(cover_page, "Company").text = cover.company
                if cover.subject:
                    ET.SubElement(cover_page, "Subject").text = cover.subject
                if cover.re:
                    ET.SubElement(cover_page, "Reference").text = cover.re
                if cover.cc:
                    ET.SubElement(cover_page, "CC").text = cover.cc
                if cover.comments:
                    ET.SubElement(cover_page, "Comments").text = cover.comments
                if cover.msg:
                    ET.SubElement(cover_page, "Message").text = cover.msg
            
            # Document information
            document = ET.SubElement(root, "Document")
            ET.SubElement(document, "FilePath").text = str(Path(pdf_file_path).resolve())
            ET.SubElement(document, "FileName").text = Path(pdf_file_path).name
            
            # File size
            try:
                file_size = Path(pdf_file_path).stat().st_size
                ET.SubElement(document, "FileSize").text = str(file_size)
            except:
                pass
            
            # Status tracking
            status = ET.SubElement(root, "Status")
            ET.SubElement(status, "State").text = "Pending"
            ET.SubElement(status, "CreatedTime").text = datetime.now().isoformat()
            
            # Ensure XML directory exists relative to current working directory
            xml_dir = Path.cwd() / "xml"
            xml_dir.mkdir(parents=True, exist_ok=True)
            
            # If output_path is just a filename, put it in the xml directory
            output_path_obj = Path(output_path)
            if not output_path_obj.is_absolute() and output_path_obj.parent == Path('.'):
                output_path = xml_dir / output_path_obj.name
            else:
                # Create output directory if needed
                output_dir = Path(output_path).parent
                output_dir.mkdir(parents=True, exist_ok=True)
            
            # Write XML file
            tree = ET.ElementTree(root)
            ET.indent(tree, space="  ", level=0)  # Pretty print
            tree.write(output_path, encoding="utf-8", xml_declaration=True)
            
            self.logger.info(f"Generated fax XML: {output_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error generating fax XML: {e}")
            return False
    
    def generate_simple_xml(self, recipient_fax: str, sender_name: str, 
                          pdf_file_path: str, output_path: str,
                          subject: str = "", priority: str = "Medium") -> bool:
        """
        Generate a simple XML file with minimal information
        
        Args:
            recipient_fax: Recipient fax number
            sender_name: Sender name
            pdf_file_path: Path to PDF file
            output_path: Output XML path
            subject: Optional subject
            priority: Fax priority
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Create root element - FaxFinder expects "schedule_fax"
            root = ET.Element("schedule_fax")
            
            # Basic information
            ET.SubElement(root, "JobID").text = str(uuid.uuid4())
            ET.SubElement(root, "SubmissionTime").text = datetime.now().isoformat()
            
            # Sender
            sender = ET.SubElement(root, "Sender")
            ET.SubElement(sender, "Name").text = sender_name
            
            # Recipient
            recipient = ET.SubElement(root, "Recipient")
            ET.SubElement(recipient, "FaxNumber").text = recipient_fax
            
            # Settings
            settings = ET.SubElement(root, "Settings")
            ET.SubElement(settings, "Priority").text = priority
            ET.SubElement(settings, "MaxAttempts").text = "3"
            ET.SubElement(settings, "RetryInterval").text = "5"
            
            # Cover page (if subject provided)
            if subject:
                cover_page = ET.SubElement(root, "CoverPage")
                ET.SubElement(cover_page, "Subject").text = subject
            
            # Document
            document = ET.SubElement(root, "Document")
            ET.SubElement(document, "FilePath").text = str(Path(pdf_file_path).resolve())
            ET.SubElement(document, "FileName").text = Path(pdf_file_path).name
            
            # Status
            status = ET.SubElement(root, "Status")
            ET.SubElement(status, "State").text = "Pending"
            ET.SubElement(status, "CreatedTime").text = datetime.now().isoformat()
            
            # Create output directory
            output_dir = Path(output_path).parent
            output_dir.mkdir(parents=True, exist_ok=True)
            
            # Write XML
            tree = ET.ElementTree(root)
            ET.indent(tree, space="  ", level=0)
            tree.write(output_path, encoding="utf-8", xml_declaration=True)
            
            self.logger.info(f"Generated simple fax XML: {output_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error generating simple XML: {e}")
            return False
    
    def validate_xml(self, xml_path: str) -> Dict[str, Any]:
        """
        Validate a generated XML file
        
        Args:
            xml_path: Path to XML file
            
        Returns:
            dict: Validation results
        """
        result = {
            'is_valid': True,
            'errors': [],
            'warnings': [],
            'job_id': None,
            'recipient_fax': None,
            'document_path': None
        }
        
        try:
            if not Path(xml_path).exists():
                result['is_valid'] = False
                result['errors'].append("XML file does not exist")
                return result
            
            # Parse XML
            tree = ET.parse(xml_path)
            root = tree.getroot()
            
            if root.tag not in ["FaxJob", "schedule_fax"]:
                result['errors'].append("Root element must be 'schedule_fax' or 'FaxJob'")
                result['is_valid'] = False
            
            # Check required elements
            job_id_elem = root.find("JobID")
            if job_id_elem is not None:
                result['job_id'] = job_id_elem.text
            else:
                result['errors'].append("Missing JobID element")
                result['is_valid'] = False
            
            # Check recipient fax
            recipient = root.find("Recipient")
            if recipient is not None:
                fax_elem = recipient.find("FaxNumber")
                if fax_elem is not None:
                    result['recipient_fax'] = fax_elem.text
                    if not fax_elem.text:
                        result['errors'].append("Recipient fax number is empty")
                        result['is_valid'] = False
                else:
                    result['errors'].append("Missing recipient fax number")
                    result['is_valid'] = False
            else:
                result['errors'].append("Missing Recipient element")
                result['is_valid'] = False
            
            # Check document
            document = root.find("Document")
            if document is not None:
                file_path_elem = document.find("FilePath")
                if file_path_elem is not None:
                    result['document_path'] = file_path_elem.text
                    if not Path(file_path_elem.text).exists():
                        result['warnings'].append("Referenced document file does not exist")
                else:
                    result['errors'].append("Missing document file path")
                    result['is_valid'] = False
            else:
                result['errors'].append("Missing Document element")
                result['is_valid'] = False
            
            # Check sender
            sender = root.find("Sender")
            if sender is None:
                result['warnings'].append("Missing Sender information")
            
        except ET.ParseError as e:
            result['is_valid'] = False
            result['errors'].append(f"XML parsing error: {str(e)}")
        except Exception as e:
            result['is_valid'] = False
            result['errors'].append(f"Validation error: {str(e)}")
        
        return result
    
    def generate_faxfinder_xml(self, fax_job: FaxJob, contact: Contact, 
                              pdf_file_path: str) -> str:
        """
        Generate FaxFinder submission XML with embedded base64 PDF content
        Uses the correct FaxFinder FF240.R1 API format
        
        Args:
            fax_job: FaxJob object with job details
            contact: Contact object with recipient details
            pdf_file_path: Path to the PDF file to fax
            
        Returns:
            str: XML content ready for FaxFinder submission
        """
        try:
            # Read and encode PDF
            with open(pdf_file_path, 'rb') as pdf_file:
                pdf_data = pdf_file.read()
                pdf_base64 = base64.b64encode(pdf_data).decode('utf-8')
            
            # Log PDF processing details
            self.logger.info(f"Processing PDF for FaxFinder submission:")
            self.logger.info(f"  File: {pdf_file_path}")
            self.logger.info(f"  Size: {len(pdf_data)} bytes ({len(pdf_data)/1024/1024:.1f} MB)")
            self.logger.info(f"  Base64 length: {len(pdf_base64)} characters")
            
            # Create root element - FaxFinder expects "schedule_fax"
            root = ET.Element("schedule_fax")
            
            # NOTE: No cover_page section - we use our own cover page generation
            # The PDF already contains the complete document with cover page
            
            # Sender information (FaxFinder format)
            sender = ET.SubElement(root, "sender")
            ET.SubElement(sender, "name").text = fax_job.sender_name or ""
            
            # Add optional sender organization
            if fax_job.cover_page_details and fax_job.cover_page_details.company:
                ET.SubElement(sender, "organization").text = fax_job.cover_page_details.company
            elif hasattr(fax_job, 'sender_organization') and fax_job.sender_organization:
                ET.SubElement(sender, "organization").text = fax_job.sender_organization
            
            # Recipient information (FaxFinder format)
            recipient = ET.SubElement(root, "recipient")
            ET.SubElement(recipient, "name").text = contact.name or ""
            ET.SubElement(recipient, "fax_number").text = contact.fax_number or ""
            
            # Add optional recipient organization
            if contact.organization:
                ET.SubElement(recipient, "organization").text = contact.organization
            
            # Convert priority to number (FaxFinder expects 1-5)
            priority_map = {
                "Low": "1",
                "Below Normal": "2", 
                "Medium": "3",
                "Normal": "3",
                "Above Normal": "4",
                "High": "5"
            }
            priority_text = fax_job.priority or "Medium"
            priority_num = priority_map.get(priority_text, "3")
            ET.SubElement(root, "priority").text = priority_num
            
            # Fax settings (FaxFinder format)
            ET.SubElement(root, "max_tries").text = str(fax_job.max_attempts or 3)
            ET.SubElement(root, "try_interval").text = str(fax_job.retry_interval or 5)
            
            # Attachment with embedded PDF content (FaxFinder format)
            attachment = ET.SubElement(root, "attachment")
            ET.SubElement(attachment, "location").text = "inline"
            
            # Add required attachment filename
            pdf_filename = Path(pdf_file_path).name
            ET.SubElement(attachment, "name").text = pdf_filename
            
            ET.SubElement(attachment, "content_type").text = "application/pdf"
            ET.SubElement(attachment, "content_transfer_encoding").text = "base64"
            
            # Embed base64 PDF content
            content = ET.SubElement(attachment, "content")
            content.text = pdf_base64
            
            # Convert to string
            ET.indent(root, space="  ", level=0)
            xml_content = ET.tostring(root, encoding='unicode')
            
            # Add XML declaration
            full_xml = '<?xml version="1.0" encoding="UTF-8"?>\n' + xml_content
            
            self.logger.info(f"Generated FaxFinder XML with {len(pdf_base64)} character PDF using correct FF240.R1 format")
            return full_xml
            
        except Exception as e:
            self.logger.error(f"Error generating FaxFinder XML: {e}")
            raise
    
    def get_xml_template(self) -> str:
        """
        Get a template XML structure
        
        Returns:
            str: XML template as string
        """
        template = '''<?xml version="1.0" encoding="utf-8"?>
<FaxJob>
  <JobID>{job_id}</JobID>
  <SubmissionTime>{submission_time}</SubmissionTime>
  
  <Sender>
    <Name>{sender_name}</Name>
    <Email>{sender_email}</Email>
  </Sender>
  
  <Recipient>
    <Name>{recipient_name}</Name>
    <FaxNumber>{recipient_fax}</FaxNumber>
    <Organization>{recipient_org}</Organization>
    <Phone>{recipient_phone}</Phone>
    <Email>{recipient_email}</Email>
  </Recipient>
  
  <Settings>
    <Priority>{priority}</Priority>
    <MaxAttempts>{max_attempts}</MaxAttempts>
    <RetryInterval>{retry_interval}</RetryInterval>
  </Settings>
  
  <CoverPage>
    <To>{cover_to}</To>
    <Attention>{cover_attn}</Attention>
    <From>{cover_from}</From>
    <Company>{cover_company}</Company>
    <Subject>{cover_subject}</Subject>
    <Reference>{cover_re}</Reference>
    <CC>{cover_cc}</CC>
    <Comments>{cover_comments}</Comments>
    <Message>{cover_message}</Message>
  </CoverPage>
  
  <Document>
    <FilePath>{document_path}</FilePath>
    <FileName>{document_name}</FileName>
    <FileSize>{document_size}</FileSize>
  </Document>
  
  <Status>
    <State>Pending</State>
    <CreatedTime>{created_time}</CreatedTime>
  </Status>
</FaxJob>'''
        
        return template

# Utility functions
def create_fax_xml(recipient_fax: str, sender_name: str, pdf_path: str, 
                  output_dir: str = "xml") -> str:
    """
    Quick utility to create a fax XML file
    
    Args:
        recipient_fax: Recipient fax number
        sender_name: Sender name
        pdf_path: Path to PDF file
        output_dir: Output directory (defaults to "xml")
        
    Returns:
        str: Path to created XML file
    """
    # Ensure XML directory exists relative to current working directory
    xml_dir = Path.cwd() / output_dir
    xml_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate output filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    xml_filename = f"fax_job_{timestamp}.xml"
    xml_path = xml_dir / xml_filename
    
    # Create XML
    generator = FaxXMLGenerator()
    success = generator.generate_simple_xml(
        recipient_fax, sender_name, pdf_path, str(xml_path)
    )
    
    if success:
        return str(xml_path)
    else:
        raise Exception("Failed to generate fax XML")

def validate_fax_xml(xml_path: str) -> bool:
    """
    Quick validation of a fax XML file
    
    Args:
        xml_path: Path to XML file
        
    Returns:
        bool: True if valid, False otherwise
    """
    generator = FaxXMLGenerator()
    result = generator.validate_xml(xml_path)
    return result['is_valid']
