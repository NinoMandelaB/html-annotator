"""
PDF Generator Module
Converts HTML email templates with annotations to PDF format.
"""

from weasyprint import HTML, CSS
from io import BytesIO
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
    
    # Additional CSS for PDF rendering
    pdf_css = CSS(string='''
        @page {
            size: A4 landscape;
            margin: 1cm;
        }
        
        body {
            font-family: Arial, sans-serif;
            font-size: 12px;
        }
        
        /* Ensure proper page breaks */
        .annotation-highlight-form,
        .annotation-highlight-link {
            page-break-inside: avoid;
        }
        
        /* Print-specific styles */
        @media print {
            body {
                background: white;
            }
        }
    ''')
    
    # Create PDF from HTML
    html_obj = HTML(string=annotated_html)
    pdf_bytes = html_obj.write_pdf(stylesheets=[pdf_css])
    
    return pdf_bytes