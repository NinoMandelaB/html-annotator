"""
PDF Generator Module

Converts annotated HTML templates to PDF format using xhtml2pdf (pure Python).
"""

from xhtml2pdf import pisa
from io import BytesIO
from bs4 import BeautifulSoup


def convert_annotated_html_to_pdf(html_content, annotations):
    """
    Convert HTML with annotations to PDF using xhtml2pdf (pure Python, no system deps).
    
    CRITICAL: Do NOT use inject_visual_annotations() for PDF generation!
    That function creates complex CSS that xhtml2pdf cannot parse.
    
    Instead, we apply MINIMAL inline styles directly to annotated elements.
    
    Args:
        html_content (str): The original HTML content
        annotations (list): List of annotation dictionaries
        
    Returns:
        bytes: PDF file as bytes
    """
    try:
        # Parse HTML
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Apply MINIMAL inline highlighting to each annotation
        # ONLY simple background colors - no outlines, no badges, no complex CSS
        for annotation in annotations:
            selector = annotation.get('selector', '')
            
            # Skip annotations without selectors
            if not selector:
                continue
                
            # Skip custom selectors that don't work with BeautifulSoup
            if 'linktext:' in selector or 'textvariable:' in selector or 'textselection:' in selector:
                print(f"Skipping annotation {annotation.get('label')} - custom selector not supported in PDF")
                continue
            
            try:
                # Find element
                elements = soup.select(selector)
                if not elements:
                    print(f"Element not found for selector: {selector}")
                    continue
                
                element = elements
                
                # Apply ONLY simple background color based on type
                # xhtml2pdf supports basic background-color and border
                if annotation.get('type') == 'link':
                    # Light red for links
                    element['style'] = 'background-color: #ffebee; border: 1px solid #e74c3c; padding: 2px;'
                elif annotation.get('elementtype') == 'bracketVariable':
                    # Light green for bracket variables
                    element['style'] = 'background-color: #e8f5e9; border: 1px solid #4caf50; padding: 2px;'
                elif annotation.get('elementtype') == 'hashVariable':
                    # Light blue for hash variables
                    element['style'] = 'background-color: #e3f2fd; border: 1px solid #2196f3; padding: 2px;'
                else:
                    # Light blue for regular elements
                    element['style'] = 'background-color: #e3f2fd; border: 1px solid #2196f3; padding: 2px;'
                    
            except Exception as e:
                print(f"Error applying annotation for selector {selector}: {e}")
                continue
        
        # Convert to string
        styled_html = str(soup)
        
        # Wrap in minimal HTML structure with ONLY basic CSS
        # CRITICAL: Only use CSS properties that xhtml2pdf supports
        final_html = f"""<!DOCTYPE html>
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
        table {{
            border-collapse: collapse;
            width: 100%;
        }}
        th, td {{
            border: 1px solid #ddd;
            padding: 8px;
            text-align: left;
        }}
        img {{
            max-width: 100%;
            height: auto;
        }}
    </style>
</head>
<body>
{styled_html}
</body>
</html>"""
        
        print("Generating PDF with xhtml2pdf...")
        
        # Generate PDF
        pdf_buffer = BytesIO()
        pisa_status = pisa.CreatePDF(
            final_html,
            dest=pdf_buffer,
            encoding='UTF-8'
        )
        
        if pisa_status.err:
            raise Exception(f"PDF generation had errors: {pisa_status.err}")
        
        # Get the PDF bytes
        pdf_bytes = pdf_buffer.getvalue()
        pdf_buffer.close()
        
        print(f"✓ PDF generated successfully ({len(pdf_bytes)} bytes)")
        return pdf_bytes
        
    except Exception as e:
        print(f"Error generating PDF with xhtml2pdf: {str(e)}")
        import traceback
        traceback.print_exc()
        raise Exception(f"PDF generation failed: {str(e)}")
