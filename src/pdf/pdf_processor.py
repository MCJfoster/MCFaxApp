"""
PDF Processor Module
Handles PDF combining, page exclusion, and basic editing
"""

import os
import logging
from pathlib import Path
from typing import List, Optional, Dict, Any, Tuple
import PyPDF2
from PyPDF2 import PdfWriter, PdfReader

try:
    import fitz  # PyMuPDF
    PYMUPDF_AVAILABLE = True
except ImportError:
    PYMUPDF_AVAILABLE = False

class PDFProcessor:
    """
    PDF processor for combining and basic editing operations
    """
    
    def __init__(self):
        """Initialize PDF processor"""
        self.logger = logging.getLogger(__name__)
    
    def combine_pdfs(self, pdf_files: List[str], output_path: str, 
                    excluded_pages: Dict[str, List[int]] = None) -> bool:
        """
        Combine multiple PDF files into one, optionally excluding specific pages
        
        Args:
            pdf_files: List of PDF file paths to combine
            output_path: Path for the combined PDF output
            excluded_pages: Dict mapping file paths to lists of page numbers to exclude (0-based)
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            if not pdf_files:
                self.logger.error("No PDF files provided for combining")
                return False
            
            # Create output directory if needed
            output_dir = Path(output_path).parent
            output_dir.mkdir(parents=True, exist_ok=True)
            
            # Initialize PDF writer
            pdf_writer = PdfWriter()
            
            # Process each PDF file
            for pdf_path in pdf_files:
                try:
                    if not Path(pdf_path).exists():
                        self.logger.warning(f"PDF file not found: {pdf_path}")
                        continue
                    
                    # Get excluded pages for this file
                    excluded = excluded_pages.get(pdf_path, []) if excluded_pages else []
                    
                    # Read PDF
                    with open(pdf_path, 'rb') as file:
                        pdf_reader = PdfReader(file)
                        
                        # Add pages (excluding specified ones)
                        for page_num in range(len(pdf_reader.pages)):
                            if page_num not in excluded:
                                page = pdf_reader.pages[page_num]
                                pdf_writer.add_page(page)
                            else:
                                self.logger.info(f"Excluding page {page_num + 1} from {Path(pdf_path).name}")
                
                except Exception as e:
                    self.logger.error(f"Error processing PDF {pdf_path}: {e}")
                    continue
            
            # Write combined PDF
            with open(output_path, 'wb') as output_file:
                pdf_writer.write(output_file)
            
            self.logger.info(f"Successfully combined {len(pdf_files)} PDFs into {output_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error combining PDFs: {e}")
            return False
    
    def get_pdf_info(self, pdf_path: str) -> Dict[str, Any]:
        """
        Get information about a PDF file
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            dict: PDF information including page count, size, etc.
        """
        try:
            file_path = Path(pdf_path)
            
            if not file_path.exists():
                return {'error': 'File not found'}
            
            # Get file stats
            stat = file_path.stat()
            size_mb = stat.st_size / (1024 * 1024)
            
            # Read PDF
            with open(pdf_path, 'rb') as file:
                pdf_reader = PdfReader(file)
                page_count = len(pdf_reader.pages)
                
                # Try to get metadata
                metadata = pdf_reader.metadata
                
                return {
                    'file_path': str(file_path),
                    'file_name': file_path.name,
                    'size_bytes': stat.st_size,
                    'size_mb': round(size_mb, 2),
                    'page_count': page_count,
                    'title': metadata.title if metadata and metadata.title else None,
                    'author': metadata.author if metadata and metadata.author else None,
                    'subject': metadata.subject if metadata and metadata.subject else None,
                    'creator': metadata.creator if metadata and metadata.creator else None,
                    'producer': metadata.producer if metadata and metadata.producer else None,
                    'creation_date': str(metadata.creation_date) if metadata and metadata.creation_date else None,
                    'modification_date': str(metadata.modification_date) if metadata and metadata.modification_date else None
                }
                
        except Exception as e:
            self.logger.error(f"Error getting PDF info for {pdf_path}: {e}")
            return {'error': str(e)}
    
    def validate_pdf_combination(self, pdf_files: List[str], 
                               excluded_pages: Dict[str, List[int]] = None,
                               max_size_mb: float = 36.0) -> Dict[str, Any]:
        """
        Validate a PDF combination before processing
        
        Args:
            pdf_files: List of PDF file paths
            excluded_pages: Dict of excluded pages per file
            max_size_mb: Maximum allowed size in MB
            
        Returns:
            dict: Validation results
        """
        result = {
            'is_valid': True,
            'errors': [],
            'warnings': [],
            'total_size_mb': 0.0,
            'total_pages': 0,
            'file_count': len(pdf_files),
            'files_info': []
        }
        
        if not pdf_files:
            result['is_valid'] = False
            result['errors'].append("No PDF files provided")
            return result
        
        total_size = 0.0
        total_pages = 0
        
        for pdf_path in pdf_files:
            file_info = self.get_pdf_info(pdf_path)
            
            if 'error' in file_info:
                result['errors'].append(f"Error with {Path(pdf_path).name}: {file_info['error']}")
                result['is_valid'] = False
                continue
            
            # Calculate pages after exclusions
            excluded = excluded_pages.get(pdf_path, []) if excluded_pages else []
            included_pages = file_info['page_count'] - len(excluded)
            
            if included_pages <= 0:
                result['warnings'].append(f"All pages excluded from {file_info['file_name']}")
            
            total_size += file_info['size_mb']
            total_pages += included_pages
            
            file_info['excluded_pages'] = excluded
            file_info['included_pages'] = included_pages
            result['files_info'].append(file_info)
        
        result['total_size_mb'] = round(total_size, 2)
        result['total_pages'] = total_pages
        
        # Check size limit
        if total_size > max_size_mb:
            result['errors'].append(f"Total size ({total_size:.1f} MB) exceeds limit ({max_size_mb} MB)")
            result['is_valid'] = False
        
        # Size warning
        if total_size > max_size_mb * 0.8:
            result['warnings'].append(f"Total size ({total_size:.1f} MB) is close to limit ({max_size_mb} MB)")
        
        # Page count warning
        if total_pages == 0:
            result['errors'].append("No pages will be included in the final PDF")
            result['is_valid'] = False
        elif total_pages > 100:
            result['warnings'].append(f"Large number of pages ({total_pages}) may cause processing delays")
        
        return result
    
    def extract_pages(self, pdf_path: str, page_numbers: List[int], 
                     output_path: str) -> bool:
        """
        Extract specific pages from a PDF
        
        Args:
            pdf_path: Source PDF file path
            page_numbers: List of page numbers to extract (0-based)
            output_path: Output file path
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            if not Path(pdf_path).exists():
                self.logger.error(f"Source PDF not found: {pdf_path}")
                return False
            
            # Create output directory
            output_dir = Path(output_path).parent
            output_dir.mkdir(parents=True, exist_ok=True)
            
            # Read source PDF
            with open(pdf_path, 'rb') as file:
                pdf_reader = PdfReader(file)
                pdf_writer = PdfWriter()
                
                # Validate page numbers
                max_pages = len(pdf_reader.pages)
                valid_pages = [p for p in page_numbers if 0 <= p < max_pages]
                
                if not valid_pages:
                    self.logger.error("No valid page numbers provided")
                    return False
                
                # Extract pages
                for page_num in sorted(valid_pages):
                    page = pdf_reader.pages[page_num]
                    pdf_writer.add_page(page)
                
                # Write output
                with open(output_path, 'wb') as output_file:
                    pdf_writer.write(output_file)
            
            self.logger.info(f"Extracted {len(valid_pages)} pages to {output_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error extracting pages: {e}")
            return False
    
    def get_page_count(self, pdf_path: str) -> int:
        """
        Get the number of pages in a PDF
        
        Args:
            pdf_path: Path to PDF file
            
        Returns:
            int: Number of pages, or 0 if error
        """
        try:
            with open(pdf_path, 'rb') as file:
                pdf_reader = PdfReader(file)
                return len(pdf_reader.pages)
        except Exception as e:
            self.logger.error(f"Error getting page count for {pdf_path}: {e}")
            return 0
    
    def split_pdf(self, pdf_path: str, output_dir: str, 
                  pages_per_file: int = 1) -> List[str]:
        """
        Split a PDF into multiple files
        
        Args:
            pdf_path: Source PDF file path
            output_dir: Directory to save split files
            pages_per_file: Number of pages per output file
            
        Returns:
            list: List of created file paths
        """
        try:
            if not Path(pdf_path).exists():
                self.logger.error(f"Source PDF not found: {pdf_path}")
                return []
            
            # Create output directory
            output_path = Path(output_dir)
            output_path.mkdir(parents=True, exist_ok=True)
            
            # Read source PDF
            with open(pdf_path, 'rb') as file:
                pdf_reader = PdfReader(file)
                total_pages = len(pdf_reader.pages)
                
                created_files = []
                base_name = Path(pdf_path).stem
                
                # Split into chunks
                for start_page in range(0, total_pages, pages_per_file):
                    end_page = min(start_page + pages_per_file, total_pages)
                    
                    # Create output filename
                    if pages_per_file == 1:
                        output_filename = f"{base_name}_page_{start_page + 1}.pdf"
                    else:
                        output_filename = f"{base_name}_pages_{start_page + 1}-{end_page}.pdf"
                    
                    output_file_path = output_path / output_filename
                    
                    # Create PDF writer for this chunk
                    pdf_writer = PdfWriter()
                    
                    # Add pages to this chunk
                    for page_num in range(start_page, end_page):
                        page = pdf_reader.pages[page_num]
                        pdf_writer.add_page(page)
                    
                    # Write chunk
                    with open(output_file_path, 'wb') as output_file:
                        pdf_writer.write(output_file)
                    
                    created_files.append(str(output_file_path))
                
                self.logger.info(f"Split PDF into {len(created_files)} files")
                return created_files
                
        except Exception as e:
            self.logger.error(f"Error splitting PDF: {e}")
            return []
    
    def add_cover_page(self, cover_pdf_path: str, content_pdf_path: str, 
                      output_path: str) -> bool:
        """
        Add a cover page to the beginning of a PDF
        
        Args:
            cover_pdf_path: Path to cover page PDF
            content_pdf_path: Path to content PDF
            output_path: Path for combined output
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            if not Path(cover_pdf_path).exists():
                self.logger.error(f"Cover page PDF not found: {cover_pdf_path}")
                return False
            
            if not Path(content_pdf_path).exists():
                self.logger.error(f"Content PDF not found: {content_pdf_path}")
                return False
            
            # Create output directory
            output_dir = Path(output_path).parent
            output_dir.mkdir(parents=True, exist_ok=True)
            
            # Combine PDFs
            pdf_writer = PdfWriter()
            
            # Add cover page
            with open(cover_pdf_path, 'rb') as cover_file:
                cover_reader = PdfReader(cover_file)
                for page in cover_reader.pages:
                    pdf_writer.add_page(page)
            
            # Add content pages
            with open(content_pdf_path, 'rb') as content_file:
                content_reader = PdfReader(content_file)
                for page in content_reader.pages:
                    pdf_writer.add_page(page)
            
            # Write combined PDF
            with open(output_path, 'wb') as output_file:
                pdf_writer.write(output_file)
            
            self.logger.info(f"Added cover page to PDF: {output_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error adding cover page: {e}")
            return False
    
    def apply_edits_to_pdf(self, pdf_path: str, edit_data: Dict[str, Any], 
                          output_path: str) -> bool:
        """
        Apply visual edits (redactions, highlights, annotations) to a PDF
        
        Args:
            pdf_path: Source PDF file path
            edit_data: Edit data from PDF editor containing brush strokes and annotations
            output_path: Path for the edited PDF output
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            if not PYMUPDF_AVAILABLE:
                self.logger.error("PyMuPDF is required for applying PDF edits")
                return False
            
            if not Path(pdf_path).exists():
                self.logger.error(f"Source PDF not found: {pdf_path}")
                return False
            
            # Create output directory
            output_dir = Path(output_path).parent
            output_dir.mkdir(parents=True, exist_ok=True)
            
            # Open PDF with PyMuPDF
            pdf_document = fitz.open(pdf_path)
            
            # Get pages data from edit_data
            pages_data = edit_data.get('pages', [])
            
            # Apply edits to each page
            for page_data in pages_data:
                page_num = page_data.get('page_number', 0)
                
                # Skip if page is excluded
                if page_data.get('excluded', False):
                    continue
                
                # Skip if page number is invalid
                if page_num < 0 or page_num >= len(pdf_document):
                    continue
                
                page = pdf_document[page_num]
                
                # Apply brush strokes (redactions, highlights)
                brush_strokes = page_data.get('brush_strokes', [])
                for stroke in brush_strokes:
                    self._apply_brush_stroke(page, stroke)
                
                # Apply annotations (text, rectangles)
                annotations = page_data.get('annotations', [])
                for annotation in annotations:
                    self._apply_annotation(page, annotation)
            
            # Save the edited PDF
            pdf_document.save(output_path)
            pdf_document.close()
            
            self.logger.info(f"Applied edits to PDF: {output_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error applying edits to PDF: {e}")
            return False
    
    def _apply_brush_stroke(self, page, stroke_data: Dict[str, Any]):
        """Apply a brush stroke (redaction/highlight) to a PDF page"""
        try:
            stroke_type = stroke_data.get('type', 'redaction')
            points = stroke_data.get('points', [])
            brush_size = stroke_data.get('brush_size', 10)
            color_str = stroke_data.get('color', '#000000')
            
            if len(points) < 2:
                return
            
            # Convert color string to RGB tuple
            color = self._hex_to_rgb(color_str)
            
            # Create path from points
            if stroke_type == 'redaction':
                # For redactions, create filled rectangles along the path
                for i in range(len(points) - 1):
                    x1, y1 = points[i]
                    x2, y2 = points[i + 1]
                    
                    # Create rectangle around the line segment
                    rect = fitz.Rect(
                        min(x1, x2) - brush_size/2,
                        min(y1, y2) - brush_size/2,
                        max(x1, x2) + brush_size/2,
                        max(y1, y2) + brush_size/2
                    )
                    
                    # Add redaction annotation
                    redact_annot = page.add_redact_annot(rect)
                    redact_annot.set_colors(stroke=color, fill=color)
                    redact_annot.update()
                
                # Apply redactions
                page.apply_redactions()
                
            else:
                # For highlights and other strokes, draw as shapes
                shape = page.new_shape()
                
                # Set stroke properties
                shape.width = brush_size
                shape.color = color
                
                # Draw path
                shape.draw_line(fitz.Point(points[0][0], points[0][1]), 
                              fitz.Point(points[1][0], points[1][1]))
                
                for i in range(1, len(points) - 1):
                    shape.draw_line(fitz.Point(points[i][0], points[i][1]), 
                                  fitz.Point(points[i+1][0], points[i+1][1]))
                
                # Commit the shape
                shape.commit()
                
        except Exception as e:
            self.logger.error(f"Error applying brush stroke: {e}")
    
    def _apply_annotation(self, page, annotation_data: Dict[str, Any]):
        """Apply an annotation (text, rectangle) to a PDF page"""
        try:
            annotation_type = annotation_data.get('type', 'text')
            color_str = annotation_data.get('color', '#0000FF')
            color = self._hex_to_rgb(color_str)
            
            if annotation_type == 'text':
                x = annotation_data.get('x', 0)
                y = annotation_data.get('y', 0)
                text = annotation_data.get('text', '')
                font_size = annotation_data.get('size', 12)
                
                # Add text annotation
                point = fitz.Point(x, y)
                text_annot = page.add_text_annot(point, text)
                text_annot.set_info(content=text)
                text_annot.update()
                
                # Also add the text directly to the page
                page.insert_text(point, text, fontsize=font_size, color=color)
                
            elif annotation_type == 'rectangle':
                x = annotation_data.get('x', 0)
                y = annotation_data.get('y', 0)
                width = annotation_data.get('width', 100)
                height = annotation_data.get('height', 50)
                
                # Create rectangle
                rect = fitz.Rect(x, y, x + width, y + height)
                
                # Add rectangle annotation
                rect_annot = page.add_rect_annot(rect)
                rect_annot.set_colors(stroke=color)
                rect_annot.update()
                
        except Exception as e:
            self.logger.error(f"Error applying annotation: {e}")
    
    def _hex_to_rgb(self, hex_color: str) -> Tuple[float, float, float]:
        """Convert hex color string to RGB tuple (0-1 range)"""
        try:
            # Remove # if present
            hex_color = hex_color.lstrip('#')
            
            # Convert to RGB (0-255 range)
            r = int(hex_color[0:2], 16)
            g = int(hex_color[2:4], 16)
            b = int(hex_color[4:6], 16)
            
            # Convert to 0-1 range for PyMuPDF
            return (r/255.0, g/255.0, b/255.0)
            
        except Exception:
            # Default to black if conversion fails
            return (0.0, 0.0, 0.0)
    
    def combine_pdfs_with_edits(self, pdf_files: List[str], output_path: str,
                               edit_data_map: Dict[str, Dict[str, Any]] = None,
                               excluded_pages: Dict[str, List[int]] = None) -> bool:
        """
        Combine multiple PDF files with applied edits
        
        Args:
            pdf_files: List of PDF file paths to combine
            output_path: Path for the combined PDF output
            edit_data_map: Dict mapping file paths to their edit data
            excluded_pages: Dict mapping file paths to lists of page numbers to exclude (0-based)
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            if not pdf_files:
                self.logger.error("No PDF files provided for combining")
                return False
            
            # Create temporary directory for edited PDFs
            temp_dir = Path(output_path).parent / "temp_edited_pdfs"
            temp_dir.mkdir(exist_ok=True)
            
            # List to store paths of PDFs to combine (original or edited)
            pdfs_to_combine = []
            temp_files_to_cleanup = []
            
            # Process each PDF file
            for pdf_path in pdf_files:
                if not Path(pdf_path).exists():
                    self.logger.warning(f"PDF file not found: {pdf_path}")
                    continue
                
                # Check if this PDF has edits
                edit_data = edit_data_map.get(pdf_path) if edit_data_map else None
                
                if edit_data and self._has_visual_edits(edit_data):
                    # Apply edits and use edited version
                    temp_edited_path = temp_dir / f"edited_{Path(pdf_path).name}"
                    
                    if self.apply_edits_to_pdf(pdf_path, edit_data, str(temp_edited_path)):
                        pdfs_to_combine.append(str(temp_edited_path))
                        temp_files_to_cleanup.append(str(temp_edited_path))
                        self.logger.info(f"Using edited version of {Path(pdf_path).name}")
                    else:
                        # Fall back to original if edit application fails
                        pdfs_to_combine.append(pdf_path)
                        self.logger.warning(f"Failed to apply edits to {Path(pdf_path).name}, using original")
                else:
                    # Use original PDF
                    pdfs_to_combine.append(pdf_path)
            
            # Combine the PDFs (original or edited versions)
            success = self.combine_pdfs(pdfs_to_combine, output_path, excluded_pages)
            
            # Clean up temporary files
            for temp_file in temp_files_to_cleanup:
                try:
                    Path(temp_file).unlink()
                except Exception as e:
                    self.logger.warning(f"Failed to clean up temp file {temp_file}: {e}")
            
            # Remove temp directory if empty
            try:
                temp_dir.rmdir()
            except Exception:
                pass  # Directory might not be empty or might not exist
            
            return success
            
        except Exception as e:
            self.logger.error(f"Error combining PDFs with edits: {e}")
            return False
    
    def _has_visual_edits(self, edit_data: Dict[str, Any]) -> bool:
        """Check if edit data contains visual edits that need to be applied"""
        pages_data = edit_data.get('pages', [])
        
        for page_data in pages_data:
            # Skip excluded pages
            if page_data.get('excluded', False):
                continue
                
            # Check for brush strokes
            if page_data.get('brush_strokes'):
                return True
                
            # Check for annotations
            if page_data.get('annotations'):
                return True
        
        return False

# Utility functions
def quick_combine_pdfs(pdf_files: List[str], output_path: str) -> bool:
    """
    Quick utility to combine PDFs without exclusions
    
    Args:
        pdf_files: List of PDF file paths
        output_path: Output file path
        
    Returns:
        bool: True if successful, False otherwise
    """
    processor = PDFProcessor()
    return processor.combine_pdfs(pdf_files, output_path)

def get_total_pages(pdf_files: List[str]) -> int:
    """
    Get total page count across multiple PDFs
    
    Args:
        pdf_files: List of PDF file paths
        
    Returns:
        int: Total page count
    """
    processor = PDFProcessor()
    total = 0
    for pdf_path in pdf_files:
        total += processor.get_page_count(pdf_path)
    return total

def validate_pdf_files(pdf_files: List[str]) -> Dict[str, Any]:
    """
    Validate a list of PDF files
    
    Args:
        pdf_files: List of PDF file paths
        
    Returns:
        dict: Validation results
    """
    processor = PDFProcessor()
    return processor.validate_pdf_combination(pdf_files)
