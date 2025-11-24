"""
PDF Generator Module
Converts annotated HTML templates to PDF format using xhtml2pdf (pure Python).
"""
from xhtml2pdf import pisa
from io import BytesIO


def convert_annotated_html_to_pdf(html_content, annotations):
    """
    Convert HTML with annotations to PDF using xhtml2pdf (pure Python, no system deps).
    
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
        
        # Add inline CSS for better PDF styling
        styled_html = f'''
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                @page {{
                    size: A4;
                    margin: 2cm;
                }}
                
                body {{
                    font-family: Arial, Helvetica, sans-serif;
                    font-size: 11pt;
                    line-height: 1.6;
                    color: #333;
                }}
                
                /* Annotation highlights */
                [data-annotation-id] {{
                    border: 2px solid #3498db !important;
                    background-color: rgba(52, 152, 219, 0.1) !important;
                    padding: 2px;
                    margin: 2px;
                    display: inline-block;
                }}
                
                /* Variable highlights */
                .annotation-highlight-variable,
                .annotation-highlight-bracket {{
                    background-color: #e3f2fd !important;
                    border: 1px solid #2196F3 !important;
                    padding: 2px 4px;
                    border-radius: 3px;
                    font-family: monospace;
                }}
                
                /* Link highlights */
                .annotation-highlight-link {{
                    border: 2px solid #e74c3c !important;
                    background-color: #ffebee !important;
                    color: #c62828;
                }}
                
                /* Prevent awkward page breaks */
                p, div, li {{
                    page-break-inside: avoid;
                }}
                
                h1, h2, h3, h4, h5, h6 {{
                    page-break-after: avoid;
                }}
                
                /* Make sure images don't break layout */
                img {{
                    max-width: 100%;
                    height: auto;
                }}
                
                /* Table styling */
                table {{
                    border-collapse: collapse;
                    width: 100%;
                }}
                
                th, td {{
                    border: 1px solid #ddd;
                    padding: 8px;
                    text-align: left;
                }}
            </style>
        </head>
        <body>
            {annotated_html}
        </body>
        </html>
        '''
        
        # Generate PDF
        print("📄 Generating PDF with xhtml2pdf...")
        pdf_buffer = BytesIO()
        
        # Convert HTML to PDF
        pisa_status = pisa.CreatePDF(
            styled_html,
            dest=pdf_buffer,
            encoding='UTF-8'
        )
        
        if pisa_status.err:
            raise Exception(f"PDF generation had errors: {pisa_status.err}")
        
        # Get the PDF bytes
        pdf_bytes = pdf_buffer.getvalue()
        pdf_buffer.close()
        
        print(f"✅ PDF generated successfully ({len(pdf_bytes)} bytes)")
        return pdf_bytes
        
    except Exception as e:
        print(f"❌ Error generating PDF with xhtml2pdf: {str(e)}")
        import traceback
        traceback.print_exc()
        raise Exception(f"PDF generation failed: {str(e)}")
