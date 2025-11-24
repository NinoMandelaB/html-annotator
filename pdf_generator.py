"""
PDF Generator Module
Converts annotated HTML templates to PDF format using WeasyPrint.
"""
from weasyprint import HTML, CSS
from io import BytesIO


def convert_annotated_html_to_pdf(html_content, annotations):
    """
    Convert HTML with annotations to PDF using WeasyPrint.
    
    Args:
        html_content (str): The original HTML content
        annotations (list): List of annotation dictionaries
        
    Returns:
        bytes: PDF file as bytes
    """
    try:
        # Import the inject function from html_parser
        from html_parser import inject_visual_annotations
        
        # Inject visual annotations into HTML
        annotated_html = inject_visual_annotations(html_content, annotations)
        
        # Custom CSS for PDF styling
        pdf_css = CSS(string='''
            @page {
                size: A4;
                margin: 2cm;
            }
            
            body {
                font-family: Arial, sans-serif;
                font-size: 11pt;
                line-height: 1.6;
            }
            
            /* Annotation highlights */
            [data-annotation-id] {
                border: 2px solid #3498db !important;
                background-color: rgba(52, 152, 219, 0.1) !important;
                padding: 2px;
                margin: 2px;
            }
            
            /* Variable highlights */
            .annotation-highlight-variable,
            .annotation-highlight-bracket {
                background-color: rgba(52, 152, 219, 0.15) !important;
                border: 1px solid #3498db !important;
                padding: 2px 4px;
                border-radius: 3px;
            }
            
            /* Link highlights */
            .annotation-highlight-link {
                border: 2px solid #e74c3c !important;
                background-color: rgba(231, 76, 60, 0.1) !important;
            }
            
            /* Prevent page breaks inside elements */
            p, div, li {
                page-break-inside: avoid;
            }
            
            /* Make sure images don't break layout */
            img {
                max-width: 100%;
                height: auto;
            }
        ''')
        
        # Generate PDF
        print("📄 Generating PDF with WeasyPrint...")
        html_obj = HTML(string=annotated_html)
        pdf_bytes = html_obj.write_pdf(stylesheets=[pdf_css])
        print("✅ PDF generated successfully")
        
        return pdf_bytes
        
    except Exception as e:
        print(f"❌ Error generating PDF with WeasyPrint: {str(e)}")
        import traceback
        traceback.print_exc()
        raise Exception(f"PDF generation failed: {str(e)}")
