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
            "type": "element",
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
            "type": "link",
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
    
    # Detect variables in href attributes (as part of links)
    for link in soup.find_all('a', href=True):
        href = link.get('href', '')
        
        # Check if href contains template variables
        if '{{' in href and '}}' in href:
            # Extract variable names from href
            href_vars = re.findall(r'\{\{([a-zA-Z0-9_.]+)\}\}', href)
            
            for var_name in href_vars:
                # Create annotation for this variable
                annotation = {
                    "id": str(uuid.uuid4()),
                    "type": "element",
                    "element_type": "variable_in_attribute",
                    "input_type": "url_variable",
                    "selector": generate_css_selector(link),
                    "name": var_name,
                    "element_id": link.get('id', ''),
                    "label": f"URL Variable: {var_name}",
                    "text": f"Used in: {link.get_text(strip=True)}",
                    "variable_name": var_name,
                    "url": href
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
            label = f"Custom Text Block: {var_name[:50]}"
        else:
            label = f"Variable: {var_name}"
        
        annotation = {
            "id": str(uuid.uuid4()),
            "type": "element",
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
    The span is invisible and doesn't change the visual appearance.
    
    IMPORTANT: Only wraps variables in TEXT CONTENT, not inside HTML attributes
    to avoid breaking href, src, style, etc.
    
    Args:
        html_content (str): Original HTML content
        
    Returns:
        str: HTML with variables wrapped in spans (only in text nodes)
    """
    from bs4 import BeautifulSoup, NavigableString
    
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Pattern for customText blocks: {{customText[...]}}
    custom_text_pattern = re.compile(r'(\{\{customText\[(.*?)\]\}\})', re.DOTALL)
    
    # Pattern for regular variables: {{variableName}}
    variable_pattern = re.compile(r'(\{\{[a-zA-Z0-9_.]+\}\})')
    
    def wrap_variable_in_span(text):
        """Wrap variables in a text string with span tags."""
        
        def replace_custom_text(match):
            full_match = match.group(1)  # Full {{customText[...]}}
            content = match.group(2)  # Just the content inside brackets
            var_id = f"custom-text-{uuid.uuid4().hex[:8]}"
            var_name = content[:50] + "..." if len(content) > 50 else content
            # Escape any quotes in var_name for HTML attribute
            var_name_escaped = var_name.replace('"', '&quot;')
            return f'<span class="template-var template-var-custom" data-template-var="{var_name_escaped}" data-var-type="customText" id="{var_id}" style="display: inline; background: none; padding: 0; margin: 0;">{full_match}</span>'
        
        def replace_variable(match):
            full_match = match.group(1)  # Full {{variableName}}
            var_name = full_match[2:-2]  # Extract just the name (remove {{ and }})
            var_id = f"var-{var_name.replace('.', '-')}-{uuid.uuid4().hex[:8]}"
            return f'<span class="template-var template-var-simple" data-template-var="{var_name}" data-var-type="variable" id="{var_id}" style="display: inline; background: none; padding: 0; margin: 0;">{full_match}</span>'
        
        # First replace customText blocks
        text = custom_text_pattern.sub(replace_custom_text, text)
        # Then replace regular variables
        text = variable_pattern.sub(replace_variable, text)
        
        return text
    
    # Find all text nodes and wrap variables in them
    # We need to be careful to only process actual text content, not attributes
    for element in soup.find_all(text=True):
        # Skip if this is inside a script or style tag
        if element.parent.name in ['script', 'style']:
            continue
        
        # Check if this text node contains any variables
        if '{{' in element and '}}' in element:
            # Wrap variables in this text
            new_text = wrap_variable_in_span(str(element))
            
            # Replace the text node with parsed HTML
            new_soup = BeautifulSoup(new_text, 'html.parser')
            element.replace_with(new_soup)
    
    return str(soup)


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
    
    # For template variables, use data attribute
    if element.get('data-template-var'):
        var_name = element.get('data-template-var')
        # Escape special characters in attribute selector
        var_name_escaped = var_name.replace('"', '\\"')
        return f'{selector}[data-template-var="{var_name_escaped}"]'
    
    # Add class if available
    if element.get('class'):
        classes = element.get('class')
        if isinstance(classes, list):
            # Use first class to keep selector simple
            selector += f'.{classes[0]}'
        else:
            selector += f'.{classes}'
    
    # Add name attribute if available and no class
    elif element.get('name'):
        selector += f'[name="{element.get("name")}"]'
    
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
        .annotation-highlight-element {
            outline: 3px solid #3498db !important;
            outline-offset: 2px;
            position: relative;
            box-shadow: 0 0 10px rgba(52, 152, 219, 0.5) !important;
            background-color: rgba(52, 152, 219, 0.05) !important;
        }
        
        .annotation-highlight-link {
            outline: 3px solid #e74c3c !important;
            outline-offset: 2px;
            position: relative;
            box-shadow: 0 0 10px rgba(231, 76, 60, 0.5) !important;
            background-color: rgba(231, 76, 60, 0.05) !important;
        }
        
        /* Specific styling for template variables */
        span.annotation-highlight-element.template-var {
            display: inline !important;
            padding: 2px 4px !important;
            border-radius: 3px !important;
            background-color: rgba(52, 152, 219, 0.15) !important;
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
        
        .annotation-highlight-element .annotation-badge {
            background: #3498db;
        }
        
        .annotation-highlight-link .annotation-badge {
            background: #e74c3c;
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
            elements = soup.select(selector)
            
            # If multiple elements found, use the first one
            if not elements:
                print(f"Could not find element for selector: {selector}")
                continue
                
            element = elements[0]
            
            # Add annotation ID as data attribute
            element['data-annotation-id'] = annotation['id']
            
            # Get existing classes
            existing_classes = element.get('class', [])
            if isinstance(existing_classes, str):
                existing_classes = [existing_classes]
            
            # Add highlight class based on type
            if annotation['type'] == 'link':
                highlight_class = 'annotation-highlight-link'
            else:  # element type
                highlight_class = 'annotation-highlight-element'
            
            # Add the highlight class
            existing_classes.append(highlight_class)
            element['class'] = existing_classes
            
            # Make element position relative if not already positioned (for badge)
            style = element.get('style', '')
            if style and not style.endswith(';'):
                style += ';'
            if 'position' not in style:
                element['style'] = f"{style} position: relative;"
        
        except Exception as e:
            # If selector fails, skip this annotation
            print(f"Error applying annotation for selector {selector}: {e}")
            continue
    
    return str(soup)


def create_annotation_overlays_for_pdf(html_content, annotations):
    """
    Create visual overlays for PDF generation (similar to original PDF style).
    Adds colored boxes and margin text boxes.
    
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
                elements = soup.select(selector)
                if not elements:
                    continue
                    
                element = elements[0]
                
                # Determine color based on type
                if annotation['type'] == 'link':
                    border_color = '#e74c3c'
                    badge_color = '#e74c3c'
                    type_label = 'Link'
                else:  # element
                    border_color = '#3498db'
                    badge_color = '#3498db'
                    type_label = 'Element'
                
                # Add colored box around element
                current_style = element.get('style', '')
                if current_style and not current_style.endswith(';'):
                    current_style += ';'
                element['style'] = f"{current_style} border: 2px solid {border_color}; position: relative; display: inline-block; padding: 2px;"
                
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
                
                # Number and type
                header_span = soup.new_tag('div', style=f'font-weight: bold; color: {badge_color}; margin-bottom: 5px;')
                header_span.string = f"{annotation_counter}. {type_label}"
                margin_item.append(header_span)
                
                # Label
                label_span = soup.new_tag('div', style='margin-top: 5px; font-weight: 600;')
                label_span.string = annotation['label']
                margin_item.append(label_span)
                
                # Additional details
                if annotation['type'] == 'link' and annotation.get('url'):
                    url_span = soup.new_tag('div', style='margin-top: 3px; color: #3498db; word-break: break-all; font-size: 9px;')
                    url_span.string = f"URL: {annotation['url']}"
                    margin_item.append(url_span)
                
                elif annotation['type'] == 'element':
                    if annotation.get('variable_name'):
                        var_span = soup.new_tag('div', style='margin-top: 3px; color: #666; font-family: monospace; font-size: 9px;')
                        var_span.string = f"Variable: {annotation['variable_name']}"
                        margin_item.append(var_span)
                    elif annotation.get('name'):
                        name_span = soup.new_tag('div', style='margin-top: 3px; color: #666; font-size: 9px;')
                        name_span.string = f"Name: {annotation['name']}"
                        margin_item.append(name_span)
                
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
