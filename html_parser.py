"""
HTML Parser Module

Parses HTML email templates and detects annotatable elements:
- Form fields (input, textarea, select, button)
- Links (a tags) - including those with template variables
- Template variables: {{variable}}, [[variable]], ##variable##
- Custom text (placeholders) - manually added by user
"""

from bs4 import BeautifulSoup
import re


def parse_html_and_detect_elements(html_content):
    """
    Parse HTML and automatically detect annotatable elements.
    Detects form fields, links, and template variables.
    
    Args:
        html_content (str): Raw HTML content
        
    Returns:
        list: List of detected annotation dictionaries
    """
    soup = BeautifulSoup(html_content, 'html.parser')
    annotations = []
    
    # 1. Detect form fields (input, textarea, select, button)
    for element in soup.find_all(['input', 'textarea', 'select', 'button']):
        annotation = {
            'type': 'formfield',
            'elementtype': element.name,
            'name': element.get('name', element.get('id', 'unnamed')),
            'inputtype': element.get('type', element.name),
            'label': f"{element.name.capitalize()}: {element.get('name', element.get('id', 'unnamed'))}",
            'selector': generate_selector_for_element(element),
        }
        annotations.append(annotation)
    
    # 2. Detect links (a tags)
    for element in soup.find_all('a'):
        href = element.get('href', '')
        link_text = element.get_text(strip=True)
        
        annotation = {
            'type': 'link',
            'elementtype': 'a',
            'url': href,
            'label': f"Link: {link_text[:50]}" if link_text else f"Link: {href[:50]}",
            'selector': generate_selector_for_element(element),
        }
        annotations.append(annotation)
    
    # 3. Detect template variables in text content
    # Patterns: {{variable}}, [[variable]], ##variable##
    text_content = soup.get_text()
    
    # Pattern for {{variable}}
    for match in re.finditer(r'\{\{([^}]+)\}\}', text_content):
        variable_name = match.group(1).strip()
        annotations.append({
            'type': 'element',
            'elementtype': 'hashVariable',
            'variablename': variable_name,
            'label': f"Variable: {variable_name}",
            'selector': f'textvariable:{{{{{variable_name}}}}}',  # Special selector for JS
        })
    
    # Pattern for [[variable]]
    for match in re.finditer(r'\[\[([^\]]+)\]\]', text_content):
        variable_name = match.group(1).strip()
        annotations.append({
            'type': 'element',
            'elementtype': 'bracketVariable',
            'variablename': variable_name,
            'label': f"Variable: {variable_name}",
            'selector': f'textvariable:[[{variable_name}]]',  # Special selector for JS
        })
    
    # Pattern for ##variable##
    for match in re.finditer(r'##([^#]+)##', text_content):
        variable_name = match.group(1).strip()
        annotations.append({
            'type': 'element',
            'elementtype': 'hashVariable',
            'variablename': variable_name,
            'label': f"Variable: {variable_name}",
            'selector': f'textvariable:#{variable_name}#',  # Special selector for JS
        })
    
    return annotations


def generate_selector_for_element(element):
    """
    Generate a CSS selector for a BeautifulSoup element.
    Priority: id > href (for links) > name > tag + classes
    
    Args:
        element: BeautifulSoup element
        
    Returns:
        str: CSS selector string
    """
    # Priority 1: Use ID if available
    if element.get('id'):
        return f"#{element['id']}"
    
    # Priority 2: For links, try to use text content or href
    if element.name == 'a':
        link_text = element.get_text(strip=True)
        if link_text and len(link_text) < 100 and '{{' not in link_text and '[[' not in link_text:
            # Use special notation for JS text matching
            return f'linktext:{link_text}'
        elif element.get('href'):
            # Use partial href matching (extract domain or safe part)
            href = element.get('href')
            if '{{' in href or '[[' in href:
                # Extract the part before the first variable
                safe_part = href.split('{{')[0].split('[[')[0].rstrip('?')
                if len(safe_part) > 10:  # Only use if meaningful
                    return f'[href*="{safe_part}"]'
            else:
                return f'[href="{href[:100]}"]'
    
    # Priority 3: Use name attribute
    if element.get('name'):
        return f'[name="{element["name"]}"]'
    
    # Priority 4: Tag + classes
    selector = element.name
    if element.get('class'):
        classes = [c for c in element.get('class', []) if c]
        if classes:
            selector += '.' + '.'.join(classes)
    
    return selector


def inject_visual_annotations(html_content, annotations):
    """
    Inject visual annotations into HTML for preview in the editor.
    Adds CSS and data attributes to highlight annotated elements.
    For email templates, only highlights DOM elements (not text-level annotations).
    
    Args:
        html_content (str): Original HTML content
        annotations (list): List of annotation dictionaries
        
    Returns:
        str: HTML with injected annotations
    """
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Add CSS to the head
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
        if not selector or annotation.get('elementtype') in ['customText', 'variable']:
            continue
        
        try:
            # Find element using CSS selector
            elements = soup.select(selector)
            if not elements:
                print(f"Could not find element for selector: {selector}")
                continue
            
            element = elements[0]  # If multiple elements found, use the first one
            
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
            
            existing_classes.append(highlight_class)
            element['class'] = existing_classes
            
            # Make element position: relative if not already positioned (for badge)
            style = element.get('style', '')
            if style and not style.endswith(';'):
                style += ';'
            if 'position' not in style:
                element['style'] = f"{style} position: relative;"
                
        except Exception as e:
            print(f"Error applying annotation for selector {selector}: {e}")
            continue
    
    return str(soup)


def create_annotation_overlays_for_pdf(html_content, annotations):
    """
    Create visual overlays for PDF generation with margin annotations.
    
    Layout:
    - Main content area (70%) with numbered markers on annotated elements
    - Margin area (30%) with annotation details
    - Numbered badges connect content to margin
    
    Args:
        html_content (str): Original HTML content
        annotations (list): List of annotation dictionaries
        
    Returns:
        str: HTML with PDF-ready margin annotations
    """
    soup = BeautifulSoup(html_content, 'html.parser')
    
    if soup.body:
        # Create main container with flexbox layout
        container = soup.new_tag('div', style='display: flex; position: relative; min-height: 100vh;')
        
        # Create content area (original HTML)
        content_area = soup.new_tag('div', style='flex: 1; padding-right: 20px; max-width: 65%;')
        
        # Move all body children to content area
        body_children = list(soup.body.children)
        for child in body_children:
            content_area.append(child.extract())
        
        # Create margin area for annotations
        margin_area = soup.new_tag(
            'div',
            style='width: 35%; min-width: 250px; border-left: 2px solid #ccc; padding: 20px 10px; background: #f9f9f9; font-size: 10px; font-family: Arial, sans-serif;'
        )
        
        # Add title to margin
        margin_title = soup.new_tag('div', style='font-weight: bold; font-size: 12px; margin-bottom: 15px; color: #2c3e50; border-bottom: 2px solid #3498db; padding-bottom: 5px;')
        margin_title.string = 'Annotations'
        margin_area.append(margin_title)
        
        # Process each annotation
        annotation_counter = 1
        for annotation in annotations:
            selector = annotation.get('selector', '')
            
            # Skip annotations without proper selectors
            if not selector:
                continue
            
            # Skip custom selectors that don't work with BeautifulSoup
            if 'linktext:' in selector or 'textvariable:' in selector or 'textselection:' in selector:
                continue
            
            try:
                # Find the element in content area
                elements = content_area.select(selector)
                if not elements:
                    print(f"Element not found for selector: {selector}")
                    continue
                
                element = elements[0]
                
                # Determine color based on type
                if annotation.get('type') == 'link':
                    badge_color = '#e74c3c'
                    type_label = 'Link'
                    bg_color = '#ffebee'
                elif annotation.get('elementtype') == 'bracketVariable':
                    badge_color = '#4caf50'
                    type_label = 'Variable'
                    bg_color = '#e8f5e9'
                elif annotation.get('elementtype') == 'hashVariable':
                    badge_color = '#2196f3'
                    type_label = 'Variable'
                    bg_color = '#e3f2fd'
                else:
                    badge_color = '#3498db'
                    type_label = 'Element'
                    bg_color = '#e3f2fd'
                
                # Add numbered badge to the element in content
                existing_style = element.get('style', '')
                element['style'] = f"{existing_style} background-color: {bg_color}; border-left: 3px solid {badge_color}; padding: 4px; position: relative;"
                
                # Add number badge as superscript
                badge = soup.new_tag('sup', style=f'background: {badge_color}; color: white; padding: 2px 5px; margin-left: 4px; border-radius: 3px; font-size: 9px; font-weight: bold;')
                badge.string = str(annotation_counter)
                element.insert(0, badge)
                
                # Add annotation to margin area
                margin_item = soup.new_tag(
                    'div',
                    style=f'margin-bottom: 15px; padding: 10px; background: white; border: 1px solid #ddd; border-left: 4px solid {badge_color}; border-radius: 4px;'
                )
                
                # Number and type
                header_span = soup.new_tag('div', style=f'font-weight: bold; color: {badge_color}; margin-bottom: 5px;')
                header_span.string = f"{annotation_counter}. {type_label}"
                margin_item.append(header_span)
                
                # Label
                label_span = soup.new_tag('div', style='margin-top: 5px; font-weight: 600;')
                label_span.string = annotation.get('label', 'Unnamed')
                margin_item.append(label_span)
                
                # Additional details based on type
                if annotation.get('type') == 'link' and annotation.get('url'):
                    url_span = soup.new_tag('div', style='margin-top: 3px; color: #3498db; word-break: break-all; font-size: 9px;')
                    url_span.string = f"URL: {annotation['url']}"
                    margin_item.append(url_span)
                elif annotation.get('type') == 'element':
                    if annotation.get('variablename'):
                        var_span = soup.new_tag('div', style='margin-top: 3px; color: #666; font-family: monospace; font-size: 9px;')
                        var_span.string = f"Variable: {annotation['variablename']}"
                        margin_item.append(var_span)
                    elif annotation.get('name'):
                        name_span = soup.new_tag('div', style='margin-top: 3px; color: #666; font-size: 9px;')
                        name_span.string = f"Name: {annotation['name']}"
                        margin_item.append(name_span)
                
                margin_area.append(margin_item)
                annotation_counter += 1
                
            except Exception as e:
                print(f"Error processing annotation for selector {selector}: {e}")
                continue
        
        # Assemble the layout
        container.append(content_area)
        container.append(margin_area)
        soup.body.clear()
        soup.body.append(container)
    
    return str(soup)

