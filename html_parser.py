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
    CRITICAL: Count text node occurrences only (not in HTML tags/attributes)
    """
    soup = BeautifulSoup(html_content, 'html.parser')
    annotations = []
    annotated_elements = set()
    
    # Pattern 1: ##variableName## format (TEXT NODES ONLY)
    # Extract all text content and count occurrences there
    def count_text_occurrences(html_string):
        """Count occurrences of patterns in text nodes only, not HTML tags"""
        # Remove all HTML tags to get clean text
        clean_text = re.sub(r'<[^>]+>', '', html_string)
        return clean_text
    
    clean_text_content = count_text_occurrences(str(soup))
    hash_variable_pattern = re.compile(r'##([^#]+)##')
    instance_counter = {}
    
    for match in hash_variable_pattern.finditer(clean_text_content):
        var_content = match.group(1)
        full_text = match.group(0)  # ##variableName##
        
        # Track which occurrence this is (0-indexed)
        if var_content not in instance_counter:
            instance_counter[var_content] = 0
        else:
            instance_counter[var_content] += 1
        
        occurrence_index = instance_counter[var_content]
        
        annotation = {
            "id": str(uuid.uuid4()),
            "type": "element",
            "elementtype": "hashVariable",
            "element_type": "hashVariable",
            "inputtype": "variable",
            "input_type": "variable",
            "selector": f':textvariable("{full_text}")',
            "occurrenceIndex": occurrence_index,
            "occurrence_index": occurrence_index,
            "name": var_content,
            "element_id": "",
            "label": f"Variable: {var_content} (occurrence {occurrence_index + 1})",
            "text": full_text,
            "variable_name": var_content,
            "variableName": var_content,
            "url": None,
            "comments": ""
        }
        
        annotations.append(annotation)
    
    # Pattern 2: [text] format (square brackets - TEXT NODES ONLY)
    html_without_comments = re.sub(r'<!--.*?-->', '', str(soup), flags=re.DOTALL)
    clean_bracket_text = count_text_occurrences(html_without_comments)
    bracket_pattern = re.compile(r'\[([^\]]+)\]')
    bracket_matches = bracket_pattern.finditer(clean_bracket_text)
    bracket_counter = {}
    
    for match in bracket_matches:
        bracket_content = match.group(1)
        full_text = match.group(0)
        
        # Skip HTML-like patterns
        if '=' in bracket_content or '<' in bracket_content or '>' in bracket_content:
            continue
        
        # Enhanced filter for Outlook patterns
        lower_content = bracket_content.lower()
        outlook_patterns = ['if', 'endif', 'else', 'owa', '!owa', 'mso', '!mso', 'vml', 'gte']
        if any(pattern in lower_content for pattern in outlook_patterns):
            continue
        
        # Track which occurrence this is
        if bracket_content not in bracket_counter:
            bracket_counter[bracket_content] = 0
        else:
            bracket_counter[bracket_content] += 1
        
        occurrence_index = bracket_counter[bracket_content]
        
        annotation = {
            "id": str(uuid.uuid4()),
            "type": "element",
            "elementtype": "bracketVariable",
            "element_type": "bracketVariable",
            "inputtype": "variable",
            "input_type": "variable",
            "selector": f':textvariable("{full_text}")',
            "occurrenceIndex": occurrence_index,
            "occurrence_index": occurrence_index,
            "name": bracket_content,
            "element_id": "",
            "label": f"Placeholder: {bracket_content} (occurrence {occurrence_index + 1})",
            "text": full_text,
            "variable_name": bracket_content,
            "variableName": bracket_content,
            "url": None,
            "comments": ""
        }
        
        annotations.append(annotation)
    
    # Links remain the same (no duplicates expected)
    links = soup.find_all('a', href=True)
    for link in links:
        href = link.get('href', '')
        link_text = link.get_text(strip=True)
        
        if not href or href.startswith('#'):
            continue
        
        link_key = f"link_{href}_{link_text}"
        if link_key in annotated_elements:
            continue
        
        annotated_elements.add(link_key)
        selector = generate_css_selector(link)
        is_email = href.startswith('mailto:')
        href_has_var = '{{' in href and '}}' in href
        text_has_var = '{{' in link_text and '}}' in link_text
        
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
            "elementtype": "a",
            "element_type": "a",
            "inputtype": "email" if is_email else "url",
            "input_type": "email" if is_email else "url",
            "selector": selector,
            "name": link_text or href,
            "element_id": link.get('id', ''),
            "label": label,
            "text": link_text,
            "url": href,
            "is_email": is_email,
            "contains_variable": href_has_var or text_has_var,
            "comments": ""
        }
        
        annotations.append(annotation)
    
    return annotations





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
    
    Color scheme:
    - Links: RED (#e74c3c)
    - Bracket variables [[var]]: GREEN (#4caf50)
    - Hash variables ##var## / {{var}}: BLUE (#2196f3)
    
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
            # Determine color based on type AND elementtype
            if annotation.get('type') == 'link':
                # Links = RED
                badge_color = '#e74c3c'
                type_label = 'Link'
            elif annotation.get('elementtype') == 'bracketVariable':
                # Bracket variables [[var]] = GREEN
                badge_color = '#4caf50'
                type_label = 'Placeholder'
            elif annotation.get('elementtype') == 'hashVariable':
                # Hash variables ##var## and {{var}} = BLUE
                badge_color = '#2196f3'
                type_label = 'Variable'
            else:
                # Default = BLUE
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
            label_span = soup.new_tag("div", style="margin-top: 5px; font-weight: 600;")
            label_span.string = annotation.get("label", "Unnamed")
            margin_item.append(label_span)

            # Add comments if present
            if annotation.get("comments") and annotation.get("comments").strip():
                comments_span = soup.new_tag(
                    "div",
                    style=(
                        "margin-top: 8px; padding: 8px; background-color: #f0f4f8; "
                        "border-left: 3px solid #3498db; border-radius: 3px; "
                        "font-size: 11px; color: #2c3e50; line-height: 1.4; font-style: italic;"
                    ),
                )
                comments_span.string = annotation.get("comments")
                margin_item.append(comments_span)
            
            # Additional details based on type
            if annotation.get('type') == 'link' and annotation.get('url'):
                url_span = soup.new_tag('div', style='margin-top: 3px; color: #3498db; word-break: break-all; font-size: 9px;')
                url_span.string = f"URL: {annotation['url']}"
                margin_item.append(url_span)
            elif annotation.get('variablename'):
                # Note: key is 'variablename' not 'variable_name'
                var_span = soup.new_tag('div', style='margin-top: 3px; color: #666; font-family: monospace; font-size: 9px;')
                var_span.string = f"Variable: {annotation['variablename']}"
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
