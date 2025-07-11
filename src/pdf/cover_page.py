"""
Cover Page Generator Module
Creates cover pages for fax jobs using reportlab
"""

import os
import logging
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT
from reportlab.graphics.shapes import Drawing, Circle, Rect
from reportlab.graphics import renderPDF

from database.models import CoverPageDetails

class CoverPageGenerator:
    """
    Generator for fax cover pages
    """
    
    def __init__(self):
        """Initialize cover page generator"""
        self.logger = logging.getLogger(__name__)
        self.styles = getSampleStyleSheet()
        self.setup_custom_styles()
    
    def setup_custom_styles(self):
        """Setup custom styles for cover page"""
        # Title style
        self.title_style = ParagraphStyle(
            'CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=36,
            spaceAfter=20,
            alignment=TA_LEFT,
            textColor=colors.black,
            fontName='Helvetica-Bold'
        )
        
        # Header info style
        self.header_info_style = ParagraphStyle(
            'HeaderInfo',
            parent=self.styles['Normal'],
            fontSize=10,
            spaceAfter=2,
            alignment=TA_LEFT,
            textColor=colors.black,
            fontName='Helvetica'
        )
        
        # Hospital name style
        self.hospital_name_style = ParagraphStyle(
            'HospitalName',
            parent=self.styles['Heading2'],
            fontSize=18,
            spaceAfter=5,
            alignment=TA_RIGHT,
            textColor=colors.black,
            fontName='Helvetica-Bold'
        )
        
        # Hospital subtitle style
        self.hospital_subtitle_style = ParagraphStyle(
            'HospitalSubtitle',
            parent=self.styles['Normal'],
            fontSize=12,
            spaceAfter=2,
            alignment=TA_RIGHT,
            textColor=colors.black,
            fontName='Helvetica'
        )
        
        # Field label style
        self.label_style = ParagraphStyle(
            'FieldLabel',
            parent=self.styles['Normal'],
            fontSize=11,
            fontName='Helvetica-Bold',
            textColor=colors.black
        )
        
        # Field value style
        self.value_style = ParagraphStyle(
            'FieldValue',
            parent=self.styles['Normal'],
            fontSize=11,
            fontName='Helvetica',
            textColor=colors.black
        )
        
        # Checkbox label style
        self.checkbox_style = ParagraphStyle(
            'CheckboxLabel',
            parent=self.styles['Normal'],
            fontSize=11,
            fontName='Helvetica',
            textColor=colors.black
        )
        
        # Message style
        self.message_style = ParagraphStyle(
            'MessageStyle',
            parent=self.styles['Normal'],
            fontSize=11,
            fontName='Helvetica',
            textColor=colors.black,
            spaceAfter=12
        )
    
    def generate_cover_page(self, cover_details: CoverPageDetails, 
                          output_path: str, page_count: int = 0, 
                          logo_path: Optional[str] = None) -> bool:
        """
        Generate a cover page PDF
        
        Args:
            cover_details: Cover page details
            output_path: Path to save the cover page PDF
            page_count: Number of pages in the fax (excluding cover page)
            logo_path: Path to hospital logo image
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Create output directory if it doesn't exist
            output_dir = Path(output_path).parent
            output_dir.mkdir(parents=True, exist_ok=True)
            
            # Create PDF document
            doc = SimpleDocTemplate(
                output_path,
                pagesize=letter,
                rightMargin=72,
                leftMargin=72,
                topMargin=36,
                bottomMargin=72
            )
            
            # Build content
            story = []
            
            # Header section with hospital info and logo
            story.extend(self._create_header_section(logo_path))
            story.append(Spacer(1, 20))
            
            # Fax title
            title = Paragraph("Fax", self.title_style)
            story.append(title)
            story.append(Spacer(1, 15))
            
            # Main information table
            story.append(self._create_main_info_table(cover_details, page_count))
            story.append(Spacer(1, 15))
            
            # Checkboxes section
            story.append(self._create_checkboxes_section(cover_details))
            story.append(Spacer(1, 20))
            
            # Message section (if any content)
            if cover_details.comments or cover_details.msg:
                story.extend(self._create_message_section(cover_details))
            
            # Build PDF
            doc.build(story)
            
            self.logger.info(f"Cover page generated successfully: {output_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error generating cover page: {e}")
            return False
    
    def _create_header_section(self, logo_path: Optional[str] = None) -> list:
        """Create the header section with hospital info and logo"""
        elements = []
        
        # Create header table with contact info on left and hospital name/logo on right
        header_data = []
        
        # Left side - contact information
        contact_info = [
            "10105 Park Rowe Circle",
            "Baton Rouge, Louisiana  70810",
            "T:  (225) 906-4805",
            "F:  (225) 763-2085"
        ]
        
        contact_paragraphs = []
        for info in contact_info:
            contact_paragraphs.append(Paragraph(info, self.header_info_style))
        
        # Right side - hospital name and logo
        hospital_info = []
        
        # Add logo if available
        if logo_path and os.path.exists(logo_path):
            try:
                # Create logo image with appropriate sizing
                logo = Image(logo_path, width=1.5*inch, height=1.5*inch, kind='proportional')
                hospital_info.append(logo)
            except Exception as e:
                self.logger.warning(f"Could not load logo: {e}")
        
        # Hospital name and subtitle
        hospital_info.append(Paragraph("THE SPINE HOSPITAL", self.hospital_name_style))
        hospital_info.append(Paragraph("LOUISIANA", self.hospital_name_style))
        hospital_info.append(Paragraph("at The NeuroMedical Center", self.hospital_subtitle_style))
        
        # Create the header table
        header_table_data = [[contact_paragraphs, hospital_info]]
        
        header_table = Table(header_table_data, colWidths=[3*inch, 4*inch])
        header_table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('ALIGN', (0, 0), (0, 0), 'LEFT'),
            ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
            ('LEFTPADDING', (0, 0), (-1, -1), 0),
            ('RIGHTPADDING', (0, 0), (-1, -1), 0),
            ('TOPPADDING', (0, 0), (-1, -1), 0),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
        ]))
        
        elements.append(header_table)
        
        # Add decorative red dots (similar to original template)
        elements.append(self._create_decorative_dots())
        
        return elements
    
    def _create_decorative_dots(self):
        """Create decorative red dots similar to the original template"""
        # Create a drawing with red dots
        drawing = Drawing(400, 20)
        
        # Add vertical line of red dots
        dot_color = colors.Color(0.8, 0.2, 0.2)  # Red color
        
        for i in range(8):
            y_pos = 2 + (i * 2)
            circle = Circle(200, y_pos, 2)
            circle.fillColor = dot_color
            circle.strokeColor = dot_color
            drawing.add(circle)
        
        return drawing
    
    def _create_main_info_table(self, cover_details: CoverPageDetails, page_count: int):
        """Create the main information table"""
        # Calculate total pages (including cover page)
        total_pages = page_count + 1
        
        # Create the main table data
        table_data = [
            # Row 1: To and From
            [
                Paragraph("To:", self.label_style),
                Paragraph(cover_details.to or "", self.value_style),
                Paragraph("From:", self.label_style),
                Paragraph(cover_details.from_field or "", self.value_style)
            ],
            # Row 2: Fax and Phone
            [
                Paragraph("Fax:", self.label_style),
                Paragraph(cover_details.fax or "", self.value_style),
                Paragraph("Phone:", self.label_style),
                Paragraph(cover_details.phone or "", self.value_style)
            ],
            # Row 3: Pages and Date
            [
                Paragraph("Pages:", self.label_style),
                Paragraph(f"{total_pages} (including this one)", self.value_style),
                Paragraph("Date:", self.label_style),
                Paragraph(cover_details.date or datetime.now().strftime("%m/%d/%Y"), self.value_style)
            ],
            # Row 4: Re and CC
            [
                Paragraph("Re:", self.label_style),
                Paragraph(cover_details.re or "", self.value_style),
                Paragraph("CC:", self.label_style),
                Paragraph(cover_details.cc or "", self.value_style)
            ]
        ]
        
        # Create table
        main_table = Table(table_data, colWidths=[0.8*inch, 2.7*inch, 0.8*inch, 2.7*inch])
        main_table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('LEFTPADDING', (0, 0), (-1, -1), 6),
            ('RIGHTPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),  # Label columns
            ('BACKGROUND', (2, 0), (2, -1), colors.lightgrey),
        ]))
        
        return main_table
    
    def _create_checkboxes_section(self, cover_details: CoverPageDetails):
        """Create the checkboxes section"""
        # Create checkbox symbols
        checked_box = "☑"
        unchecked_box = "☐"
        
        # Create checkbox data
        checkbox_data = [[
            Paragraph(f"{checked_box if cover_details.urgent else unchecked_box} Urgent", self.checkbox_style),
            Paragraph(f"{checked_box if cover_details.for_review else unchecked_box} For Review", self.checkbox_style),
            Paragraph(f"{checked_box if cover_details.please_comment else unchecked_box} Please Comment", self.checkbox_style),
            Paragraph(f"{checked_box if cover_details.please_reply else unchecked_box} Please Reply", self.checkbox_style)
        ]]
        
        checkbox_table = Table(checkbox_data, colWidths=[1.75*inch, 1.75*inch, 1.75*inch, 1.75*inch])
        checkbox_table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('LEFTPADDING', (0, 0), (-1, -1), 0),
            ('RIGHTPADDING', (0, 0), (-1, -1), 0),
            ('TOPPADDING', (0, 0), (-1, -1), 5),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ]))
        
        return checkbox_table
    
    def _create_message_section(self, cover_details: CoverPageDetails) -> list:
        """Create the message section"""
        elements = []
        
        # Comments section
        if cover_details.comments:
            elements.append(Paragraph("COMMENTS:", self.label_style))
            elements.append(Paragraph(cover_details.comments, self.message_style))
            elements.append(Spacer(1, 10))
        
        # Message section
        if cover_details.msg:
            elements.append(Paragraph("MESSAGE:", self.label_style))
            elements.append(Paragraph(cover_details.msg, self.message_style))
            elements.append(Spacer(1, 10))
        
        return elements
    
    def preview_cover_page(self, cover_details: CoverPageDetails, page_count: int = 0) -> str:
        """
        Generate a text preview of the cover page
        
        Args:
            cover_details: Cover page details
            page_count: Number of pages in the fax
            
        Returns:
            str: Text preview of the cover page
        """
        preview = "THE SPINE HOSPITAL LOUISIANA\n"
        preview += "at The NeuroMedical Center\n"
        preview += "=" * 50 + "\n"
        preview += "FAX TRANSMISSION\n"
        preview += "=" * 50 + "\n\n"
        
        # Main information
        preview += f"TO: {cover_details.to or '':<25} FROM: {cover_details.from_field or ''}\n"
        preview += f"FAX: {cover_details.fax or '':<24} PHONE: {cover_details.phone or ''}\n"
        preview += f"PAGES: {page_count + 1} (including this one)    DATE: {cover_details.date or datetime.now().strftime('%m/%d/%Y')}\n"
        preview += f"RE: {cover_details.re or '':<25} CC: {cover_details.cc or ''}\n\n"
        
        # Checkboxes
        preview += "PRIORITY:\n"
        preview += f"{'[X]' if cover_details.urgent else '[ ]'} Urgent    "
        preview += f"{'[X]' if cover_details.for_review else '[ ]'} For Review    "
        preview += f"{'[X]' if cover_details.please_comment else '[ ]'} Please Comment    "
        preview += f"{'[X]' if cover_details.please_reply else '[ ]'} Please Reply\n\n"
        
        # Comments
        if cover_details.comments:
            preview += "COMMENTS:\n"
            preview += f"{cover_details.comments}\n\n"
        
        # Message
        if cover_details.msg:
            preview += "MESSAGE:\n"
            preview += f"{cover_details.msg}\n\n"
        
        return preview
    
    def get_default_cover_details(self) -> CoverPageDetails:
        """
        Get default cover page details with current date
        
        Returns:
            CoverPageDetails: Default cover page details
        """
        return CoverPageDetails(
            date=datetime.now().strftime("%m/%d/%Y"),
            company="The Spine Hospital Louisiana"
        )
    
    def validate_cover_details(self, cover_details: CoverPageDetails) -> list:
        """
        Validate cover page details
        
        Args:
            cover_details: Cover page details to validate
            
        Returns:
            list: List of validation errors
        """
        errors = []
        
        # Check for required fields (basic validation)
        if not cover_details.to and not cover_details.attn:
            errors.append("Either 'To' or 'Attention' field is required")
        
        if not cover_details.from_field:
            errors.append("'From' field is recommended")
        
        # Validate date format if provided
        if cover_details.date:
            try:
                datetime.strptime(cover_details.date, "%m/%d/%Y")
            except ValueError:
                errors.append("Date must be in MM/DD/YYYY format")
        
        return errors

# Utility functions
def create_simple_cover_page(to: str, from_name: str, subject: str = "", 
                           pages: int = 1, output_path: str = None,
                           logo_path: str = None) -> str:
    """
    Create a simple cover page with minimal information
    
    Args:
        to: Recipient name
        from_name: Sender name
        subject: Subject line
        pages: Number of pages
        output_path: Output file path (auto-generated if None)
        logo_path: Path to logo image
        
    Returns:
        str: Path to generated cover page
    """
    if not output_path:
        output_path = f"cover_page_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    
    cover_details = CoverPageDetails(
        to=to,
        from_field=from_name,
        subject=subject,
        date=datetime.now().strftime("%m/%d/%Y"),
        pages=pages
    )
    
    generator = CoverPageGenerator()
    success = generator.generate_cover_page(cover_details, output_path, pages - 1, logo_path)
    
    if success:
        return output_path
    else:
        raise Exception("Failed to generate cover page")

def get_cover_page_template() -> Dict[str, str]:
    """
    Get a template for cover page fields
    
    Returns:
        dict: Template with field descriptions
    """
    return {
        'to': 'Recipient name or company',
        'attn': 'Attention line (specific person)',
        'from_field': 'Sender name',
        'company': 'Sender company',
        'fax': 'Recipient fax number',
        'phone': 'Sender phone number',
        'date': 'Date (MM/DD/YYYY format)',
        'pages': 'Total number of pages (auto-calculated)',
        'subject': 'Subject line',
        're': 'Reference line',
        'cc': 'Carbon copy recipients',
        'comments': 'Additional comments',
        'msg': 'Main message content',
        'urgent': 'Mark as urgent',
        'for_review': 'Mark for review',
        'please_comment': 'Request comments',
        'please_reply': 'Request reply'
    }
