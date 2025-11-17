"""
PDF Generator Module
Converts HTML email templates with annotations to PDF format.
"""

import pdfkit
from html_parser import create_annotation_overlays_for_pdf

def convert_annotated_html_to_pdf(html_content, annotations):
    """
    Convert HTML content with annotations to PDF.
    
    Args:
        html_content (str): Original HTML content
        annotations (list): List of annotation dictionaries
        
    Returns:
        bytes: PDF file content as bytes
    """
    # Create HTML with annotation overlays (boxes and margin text)
    annotated_html = create_annotation_overlays_for_pdf(html_content, annotations)
    
    # Configure pdfkit options
    options = {
        'page-size': 'A4',
        'orientation': 'Landscape',
        'margin-top': '10mm',
        'margin-right': '10mm',
        'margin-bottom': '10mm',
        'margin-left': '10mm',
        'encoding': "UTF-8",
        'enable-local-file-access': None,
        'no-stop-slow-scripts': None,
        'quiet': ''
    }
    
    try:
        # Create PDF from HTML
        pdf_bytes = pdfkit.from_string(annotated_html, False, options=options)
        return pdf_bytes
    except OSError as e:
        # wkhtmltopdf binary not found or path issue
        print(f"OSError generating PDF (wkhtmltopdf issue): {e}")
        # Try with minimal options
        try:
            pdf_bytes = pdfkit.from_string(annotated_html, False, options={'encoding': 'UTF-8'})
            return pdf_bytes
        except Exception as e2:
            print(f"Fallback PDF generation also failed: {e2}")
            raise Exception(f"PDF generation failed: wkhtmltopdf may not be properly installed. Error: {str(e)}")
    except Exception as e:
        print(f"Error generating PDF: {e}")
        # Try without options as last resort
        try:
            pdf_bytes = pdfkit.from_string(annotated_html, False)
            return pdf_bytes
        except Exception as e2:
            print(f"Final fallback failed: {e2}")
            raise Exception(f"PDF generation failed: {str(e)}")

