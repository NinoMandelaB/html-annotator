"""
HTML Parser Module
Detects form fields, hyperlinks, and template variables in HTML email templates.
"""

from bs4 import BeautifulSoup
import re
import uuid

def parse_html_and_detect_elements(html_content):
    """
    Parse HTML content and detect form fields, hyperlinks, and template variables.
    
    Args:
        html_content (str): The HTML content to parse
        
    Returns:
        list: List of annotation dictionaries
    """
    # First, wrap all template variables in spans for detection
    html_content = wrap_template_variables(html_content)
    
    soup = BeautifulSoup(html_content, 'html.parser')
    annotations = []
    
    # Detect form fields
    form_elements = soup.find_all(['input', 'textarea', 'select', 'button'])
    
    for idx, element in enumerate(form_elements):
        # Skip hidden inputs
        input_type = element.get('type', 'text')
        if input_type == 'hidden':
            continue
            
        # Extract element information
        element_name = element.get('name', '')
        element_id = element.get('id', '')
        element_placeholder = element.get('placeholder', '')
        element_value = element.get('value', '')
        
        # Create a label for the annotation
        if element.name == 'button' or input_type == 'submit':
            label = f"Button: {element.get_text(strip=True) or element_value or 'Submit'}"
        elif element.name == 'select':
            options = element.find_all('option')
            option_text = f" ({len(options)} options)" if options else ""
            label = f"Dropdown: {element_name or element_id or 'unnamed'}{option_text}"
        elif element.name == 'textarea':
            label = f"Textarea: {element_name or element_id or element_placeholder or 'unnamed'}"
        else:
            label = f"Input ({input_type}): {element_name or element_id or element_placeholder or 'unnamed'}"
        
        # Generate CSS selector for the element
        selector = generate_css_selector(element)
        
        annotation = {
            "id": str(uuid.uuid4()),
            "type": "form_field",
            "element_type": element.name,
            "input_type": input_type,
            "selector": selector,
            "name": element_name,
            "element_id": element_id,
            "label": label,
            "placeholder": element_placeholder,
            "value": element_value,
            "required": element.has_attr('required'),
            "url": None
        }
        annotations.append(annotation)
    
    # Detect hyperlinks
    links = soup.find_all('a', href=True)
    
    for idx, link in enumerate(links):
        href = link.get('href', '')
        link_text = link.get_text(strip=True)
        
        # Skip empty or anchor-only links
        if not href or href.startswith('#'):
            continue
        
        # Generate CSS selector
        selector = generate_css_selector(link)
        
        # Determine if it's an email link
        is_email = href.startswith('mailto:')
        
        annotation = {
            "id": str(uuid.uuid4()),
            "type": "hyperlink",
            "element_type": "a",
            "input_type": "email" if is_email else "url",
            "selector": selector,
            "name": link_text or href,
            "element_id": link.get('id', ''),
            "label": f"Link: {link_text or href[:50]}",
            "text": link_text,
            "url": href,
            "is_email": is_email
        }
        annotations.append(annotation)
    
    # Detect template variables (now wrapped in spans)
    variable_spans = soup.find_all('span', {'data-template-var': True})
    
    for span in variable_spans:
        var_name = span.get('data-template-var', '')
        var_type = span.get('data-var-type', 'variable')
        var_text = span.get_text(strip=True)
        
        # Generate CSS selector
        selector = generate_css_selector(span)
        
        # Create label based on type
        if var_type == 'customText':
            label = f"Custom Text Block: {var_name}"
        else:
            label = f"Variable: {var_name}"
        
        annotation = {
            "id": str(uuid.uuid4()),
            "type": "template_variable",
            "element_type": "span",
            "input_type": var_type,
            "selector": selector,
            "name": var_name,
            "element_id": span.get('id', ''),
            "label": label,
            "text": var_text,
            "variable_name": var_name,
            "url": None
        }
        annotations.append(annotation)
    
    return annotations

def wrap_template_variables(html_content):
    """
    Wrap all template variables ({{...}}) in span tags for easy detection.
    
    Args:
        html_content (str): Original HTML content
        
    Returns:
        str: HTML with variables wrapped in spans
    """
    # Pattern for customText blocks: {{customText[...]}}
    custom_text_pattern = r'\{\{customText\[(.*?)\]\}\}'
    
    def replace_custom_text(match):
        content = match.group(1)
        var_id = f"custom-text-{uuid.uuid4().hex[:8]}"
        # Create a descriptive name from the content
        var_name = content[:50] + "..." if len(content) > 50 else content
        return f'<span class="template-var" data-template-var="{var_name}" data-var-type="customText" id="{var_id}">{match.group(0)}</span>'
    
    html_content = re.sub(custom_text_pattern, replace_custom_text, html_content, flags=re.DOTALL)
    
    # Pattern for regular variables: {{variableName}}
    variable_pattern = r'\{\{([a-zA-Z0-9_.]+)\}\}'
    
    def replace_variable(match):
        var_name = match.group(1)
        var_id = f"var-{var_name.replace('.', '-')}-{uuid.uuid4().hex[:8]}"
        return f'<span class="template-var" data-template-var="{var_name}" data-var-type="variable" id="{var_id}">{match.group(0)}</span>'
    
    html_content = re.sub(variable_pattern, replace_variable, html_content)
    
    return html_content

def generate_css_selector(element):
    """
    Generate a unique CSS selector for an element.
    Prioritizes ID, then combination of tag + class, then tag + data attributes.
    
    Args:
        element: BeautifulSoup element
        
    Returns:
        str: CSS selector string
    """
    # If element has ID, use it (most specific)
    if element.get('id'):
        return f"#{element.get('id')}"
    
    # Build selector with tag name
    selector = element.name
    
    # Add class if available
    if element.get('class'):
        classes = element.get('class')
        if isinstance(classes, list):
            # Use first class to keep selector simple
            selector += f'.{classes[0]}'
        else:
            selector += f'.{classes}'
    
    # Add data-template-var if it's a template variable
    elif element.get('data-template-var'):
        var_name = element.get('data-template-var')
        selector += f'[data-template-var="{var_name}"]'
    
    # Add name attribute if available and no class
    elif element.get('name'):
        selector += f'[name="{element.get("name")}"]'
    
    # If still not unique enough, add nth-of-type
    # This helps when there are multiple similar elements
    if selector == element.name:
        # Find position among siblings of same type
        siblings = [sib for sib in element.parent.find_all(element.name) if sib == element]
        if len(siblings) > 1:
            index = list(element.parent.find_all(element.name)).index(element) + 1
            selector += f':nth-of-type({index})'
    
    return selector

def inject_visual_annotations(html_content, annotations):
    """
    Inject visual annotations into HTML for preview in the editor.
    Adds CSS and data attributes to highlight annotated elements.
    
    Args:
        html_content (str): Original HTML content
        annotations (list): List of annotation dictionaries
        
    Returns:
        str: HTML with injected annotations
    """
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Add annotation CSS to the head
    if not soup.head:
        head = soup.new_tag('head')
        if soup.html:
            soup.html.insert(0, head)
        else:
            soup.insert(0, head)
    
    style_tag = soup.new_tag('style')
    style_tag.string = """
        /* Annotation Styles */
        .annotation-highlight-form {
            outline: 3px solid #3498db !important;
            outline-offset: 2px;
            position: relative;
            box-shadow: 0 0 10px rgba(52, 152, 219, 0.5) !important;
        }
        
        .annotation-highlight-link {
            outline: 3px solid #e74c3c !important;
            outline-offset: 2px;
            position: relative;
            box-shadow: 0 0 10px rgba(231, 76, 60, 0.5) !important;
        }
        
        .annotation-highlight-variable {
            background-color: #fff3cd !important;
            outline: 2px solid #f39c12 !important;
            outline-offset: 1px;
            padding: 2px 4px;
            border-radius: 3px;
            position: relative;
            box-shadow: 0 0 8px rgba(243, 156, 18, 0.4) !important;
        }
        
        .annotation-badge {
            position: absolute;
            background: #2c3e50;
            color: white;
            padding: 2px 6px;
            font-size: 10px;
            border-radius: 3px;
            top: -12px;
            left: -2px;
            z-index: 1000;
            font-family: Arial, sans-serif;
            white-space: nowrap;
        }
        
        .annotation-highlight-form .annotation-badge {
            background: #3498db;
        }
        
        .annotation-highlight-link .annotation-badge {
            background: #e74c3c;
        }
        
        .annotation-highlight-variable .annotation-badge {
            background: #f39c12;
        }
    """
    soup.head.append(style_tag)
    
    # Add data attributes and classes to annotated elements
    for annotation in annotations:
        selector = annotation.get('selector', '')
        if not selector:
            continue
        
        try:
            # Find element using CSS selector
            element = soup.select_one(selector)
            
            if element:
                # Add annotation ID as data attribute
                element['data-annotation-id'] = annotation['id']
                
                # Add highlight class based on type
                if annotation['type'] == 'form_field':
                    element['class'] = element.get('class', []) + ['annotation-highlight-form']
                elif annotation['type'] == 'hyperlink':
                    element['class'] = element.get('class', []) + ['annotation-highlight-link']
                elif annotation['type'] == 'template_variable':
                    element['class'] = element.get('class', []) + ['annotation-highlight-variable']
                
                # Make element position relative if not already positioned
                style = element.get('style', '')
                if 'position' not in style:
                    element['style'] = (style + '; position: relative;').strip()
        
        except Exception as e:
            # If selector fails, skip this annotation
            print(f"Could not find element for selector: {selector}, Error: {e}")
            continue
    
    return str(soup)

def create_annotation_overlays_for_pdf(html_content, annotations):
    """
    Create visual overlays for PDF generation (similar to original PDF style).
    Adds red boxes and margin text boxes.
    
    Args:
        html_content (str): Original HTML content
        annotations (list): List of annotation dictionaries
        
    Returns:
        str: HTML with PDF-ready annotations
    """
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Wrap the entire body content in a container
    if soup.body:
        # Create main container
        container = soup.new_tag('div', style='display: flex; position: relative;')
        
        # Create content area (original HTML)
        content_area = soup.new_tag('div', style='flex: 1; padding-right: 20px; max-width: 70%;')
        
        # Move all body children to content area
        body_children = list(soup.body.children)
        for child in body_children:
            content_area.append(child.extract())
        
        # Create margin area for annotations
        margin_area = soup.new_tag('div', style='''
            width: 30%;
            min-width: 250px;
            border-left: 2px solid #ccc;
            padding: 20px 10px;
            background: #f9f9f9;
            font-size: 10px;
            font-family: Arial, sans-serif;
        ''')
        
        # Add annotations to content and margin
        annotation_counter = 1
        for annotation in annotations:
            selector = annotation.get('selector', '')
            if not selector:
                continue
            
            try:
                element = soup.select_one(selector)
                
                if element:
                    # Determine color based on type
                    if annotation['type'] == 'template_variable':
                        border_color = '#f39c12'
                        badge_color = '#f39c12'
                    elif annotation['type'] == 'hyperlink':
                        border_color = '#e74c3c'
                        badge_color = '#e74c3c'
                    else:
                        border_color = '#3498db'
                        badge_color = '#3498db'
                    
                    # Add colored box around element
                    current_style = element.get('style', '')
                    element['style'] = f"{current_style}; border: 2px solid {border_color}; position: relative;"
                    
                    # Add number badge
                    badge = soup.new_tag('span', style=f'''
                        position: absolute;
                        top: -10px;
                        right: -10px;
                        background: {badge_color};
                        color: white;
                        border-radius: 50%;
                        width: 20px;
                        height: 20px;
                        display: inline-flex;
                        align-items: center;
                        justify-content: center;
                        font-size: 12px;
                        font-weight: bold;
                        z-index: 100;
                    ''')
                    badge.string = str(annotation_counter)
                    element.append(badge)
                    
                    # Add annotation text to margin
                    margin_item = soup.new_tag('div', style=f'''
                        margin-bottom: 15px;
                        padding: 10px;
                        background: white;
                        border: 1px solid #ddd;
                        border-left: 4px solid {badge_color};
                        border-radius: 4px;
                    ''')
                    
                    # Number
                    number_span = soup.new_tag('span', style=f'font-weight: bold; color: {badge_color};')
                    number_span.string = f"{annotation_counter}. "
                    margin_item.append(number_span)
                    
                    # Type and label
                    type_span = soup.new_tag('div', style='margin-top: 5px; font-weight: 600;')
                    type_map = {
                        'form_field': 'Form Field',
                        'hyperlink': 'Hyperlink',
                        'template_variable': 'Template Variable'
                    }
                    type_text = type_map.get(annotation['type'], 'Unknown')
                    type_span.string = f"{type_text}: {annotation['label']}"
                    margin_item.append(type_span)
                    
                    # Additional details
                    if annotation['type'] == 'hyperlink' and annotation.get('url'):
                        url_span = soup.new_tag('div', style='margin-top: 3px; color: #3498db; word-break: break-all; font-size: 9px;')
                        url_span.string = f"URL: {annotation['url']}"
                        margin_item.append(url_span)
                    
                    elif annotation['type'] == 'form_field':
                        if annotation.get('name'):
                            name_span = soup.new_tag('div', style='margin-top: 3px; color: #666;')
                            name_span.string = f"Name: {annotation['name']}"
                            margin_item.append(name_span)
                        if annotation.get('input_type'):
                            type_info_span = soup.new_tag('div', style='margin-top: 3px; color: #666;')
                            type_info_span.string = f"Type: {annotation['input_type']}"
                            margin_item.append(type_info_span)
                    
                    elif annotation['type'] == 'template_variable':
                        var_span = soup.new_tag('div', style='margin-top: 3px; color: #666; font-family: monospace;')
                        var_span.string = f"Variable: {annotation.get('variable_name', '')}"
                        margin_item.append(var_span)
                    
                    margin_area.append(margin_item)
                    annotation_counter += 1
                    
            except Exception as e:
                print(f"Error adding overlay for selector {selector}: {e}")
                continue
        
        # Assemble the layout
        container.append(content_area)
        container.append(margin_area)
        soup.body.clear()
        soup.body.append(container)
    
    return str(soup)
