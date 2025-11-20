"""
HTML Parser Module
Detects form fields, hyperlinks, and template variables in HTML email templates.
OPTIMIZED FOR EMAIL TEMPLATES with special handling for nested variables and conditional blocks.
"""

from bs4 import BeautifulSoup
import re
import uuid


def parse_html_and_detect_elements(html_content):
    """
    Parse HTML EMAIL TEMPLATE content and detect annotatable elements.
    
    Email-specific logic:
    - Recognizes customText blocks as single units
    - Handles variables inside links correctly
    - Avoids duplicate annotations for nested structures
    
    Args:
        html_content (str): The HTML content to parse
        
    Returns:
        list: List of annotation dictionaries
    """
    soup = BeautifulSoup(html_content, 'html.parser')
    annotations = []
    annotated_elements = set()  # Track what we've already annotated
    
    

    # Step 1: Detect ##variable## and [text] patterns (for blue highlighting)
    # These patterns are used in email templates to mark dynamic content
    
    # Pattern 1: ##variableName## format  
    # CREATE ANNOTATION FOR EVERY INSTANCE (no deduplication)
    hash_variable_pattern = re.compile(r'##([^#]+)##')
    hash_matches = hash_variable_pattern.finditer(str(soup))
    
    instance_counter = {}  # Track instances for unique IDs
    for match in hash_matches:
        var_content = match.group(1)
        full_text = match.group(0)  # ##variableName##
        
        # Create unique instance ID
        if var_content not in instance_counter:
            instance_counter[var_content] = 0
        instance_counter[var_content] += 1
        instance_id = f"{var_content}_inst{instance_counter[var_content]}"
        
        annotation = {
            "id": str(uuid.uuid4()),
            "type": "element",
            "element_type": "hashVariable",
            "input_type": "variable",
            "selector": f':textvariable("{full_text}")',  # Custom selector for JS
            "name": var_content,
            "element_id": "",
            "label": f"Variable: {var_content}",
            "text": full_text,
            "variable_name": var_content,
            "url": None,
            "comments": ""
        }
        annotations.append(annotation)

    
    # Pattern 2: [text] format (square brackets)
    # CREATE ANNOTATION FOR EVERY INSTANCE (no deduplication)
    # IMPORTANT: Remove HTML comments first to avoid matching [if mso], [endif], etc.
    
    # Remove HTML comments from the content before searching
    html_without_comments = re.sub(r'<!--.*?-->', '', str(soup), flags=re.DOTALL)
    
    bracket_pattern = re.compile(r'\[([^\]]+)\]')
    bracket_matches = bracket_pattern.finditer(html_without_comments)
    
    bracket_counter = {}  # Track instances for unique IDs
    for match in bracket_matches:
        bracket_content = match.group(1)
        full_text = match.group(0)  # [text]
        
        # Skip if it looks like HTML attribute or contains HTML tags
        if '=' in bracket_content or '<' in bracket_content or '>' in bracket_content:
            continue
        
        # Enhanced filter for ALL Outlook conditional comment patterns
            lower_content = bracket_content.lower()
            outlook_patterns = ['if', 'endif', 'else', 'owa', '!owa', 'mso', '!mso', 'vml', 'gte']
            if any(pattern in lower_content for pattern in outlook_patterns):
                continue
            
        # Create unique instance ID
        if bracket_content not in bracket_counter:
            bracket_counter[bracket_content] = 0
        bracket_counter[bracket_content] += 1
        
        annotation = {
            "id": str(uuid.uuid4()),
            "type": "element",
            "element_type": "bracketVariable",
            "input_type": "variable",
            "selector": f':textvariable("{full_text}")',  # Custom selector for JS
            "name": bracket_content,
            "element_id": "",
            "label": f"Placeholder: {bracket_content}",
            "text": full_text,
            "variable_name": bracket_content,
            "url": None,
            "comments": ""
        }
        annotations.append(annotation)


    
   
    
    # Step 3: Detect hyperlinks (LAST, to capture everything including variables in href)
    links = soup.find_all('a', href=True)
    
    for link in links:
        href = link.get('href', '')
        link_text = link.get_text(strip=True)
        
        # Skip empty or anchor-only links
        if not href or href.startswith('#'):
            continue
        
        # Generate unique key for this link
        link_key = f"link_{href}_{link_text}"
        if link_key in annotated_elements:
            continue
        annotated_elements.add(link_key)
        
        # Generate CSS selector
        selector = generate_css_selector(link)
        
        # Determine if it's an email link
        is_email = href.startswith('mailto:')
        
        # Check if href or link text contains template variables
        href_has_var = '{{' in href and '}}' in href
        text_has_var = '{{' in link_text and '}}' in link_text
        
        # Create detailed label
        if href_has_var and text_has_var:
            label = f"Link: {link_text[:50]} (dynamic URL and text)"
        elif href_has_var:
            label = f"Link: {link_text[:50] or 'Link'} (dynamic URL)"
        elif text_has_var:
            label = f"Link: {link_text[:50]} (dynamic text)"
        else:
            label = f"Link: {link_text[:50] or href[:50]}"
        
        annotation = {
            "id": str(uuid.uuid4()),
            "type": "link",
            "element_type": "a",
            "input_type": "email" if is_email else "url",
            "selector": selector,
            "name": link_text or href,
            "element_id": link.get('id', ''),
            "label": label,
            "text": link_text,
            "url": href,
            "is_email": is_email,
            "contains_variable": href_has_var or text_has_var,
            "comments": ""  # New field for user comments   
        }
        annotations.append(annotation)
    
    return annotations


211
def generate_css_selector(element):
    """
    Generate a unique CSS selector for an element.
    Prioritizes ID, then combination of tag + class, then tag + attributes.
    
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
    
    # Add name attribute if available and no class
    elif element.get('name'):
        selector += f'[name="{element.get("name")}"]'
    
    # Add href for links if no other identifier - IMPROVED FOR EMAIL TEMPLATES
    elif element.name == 'a':
        link_text = element.get_text(strip=True)
        # Priority 1: Use link text if it's unique and not too long
        if link_text and len(link_text) <= 50:
            # Use special notation for JS text matching
            selector += f':linktext("{link_text}")'
        elif element.get('href'):
            # Priority 2: Use partial href matching (extract domain or safe part)
            href = element.get('href')
            # Extract domain or first part before template variables
            if '{{' in href:
                # Get the part before the first variable
                safe_part = href.split('{{')[0].rstrip('?&=')
                if len(safe_part) > 10:  # Only use if meaningful
                    selector += f'[href^="{safe_part}"]'
            else:
                # No variables, use normal href matching
                selector += f'[href="{href[:100]}"]'
    
    return selector


def inject_visual_annotations(html_content, annotations):
    """
    Inject visual annotations into HTML for preview in the editor.
    Adds CSS and data attributes to highlight annotated elements.
    
    For email templates, only highlights DOM elements (not text-level annotations).
    
    Args:
        html_content (str): Original HTML content
        annotations (list): List of annotation dictionaries
211

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
            position: relative !important;
            box-shadow: 0 0 10px rgba(52, 152, 219, 0.5) !important;
            background-color: rgba(52, 152, 219, 0.05) !important;
        }
        
        .annotation-highlight-link {
            outline: 3px solid #e74c3c !important;
            outline-offset: 2px;
            position: relative !important;
            box-shadow: 0 0 10px rgba(231, 76, 60, 0.5) !important;
            background-color: rgba(231, 76, 60, 0.05) !important;
        }
        
        .annotation-badge {
            position: absolute;
            background: #2c3e50;
            color: white;
            padding: 2px 6px;
211
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
        
        # Skip text-level annotations (customText, standalone variables)
        if not selector or annotation.get('element_type') in ['customText', 'variable']:
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
    Create visual overlays for PDF generation (email template style).
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
        
        # Add annotations to margin
        annotation_counter = 1
        for annotation in annotations:
            # Determine color based on type
            if annotation['type'] == 'link':
                badge_color = '#e74c3c'
                type_label = 'Link'
            else:  # element
                badge_color = '#3498db'
                type_label = 'Element'
            
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
            
            # Additional details based on type
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
        
        # Assemble the layout
        container.append(content_area)
        container.append(margin_area)
        soup.body.clear()
        soup.body.append(container)
    
    return str(soup)

