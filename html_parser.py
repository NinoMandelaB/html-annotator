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
    text_content = soup.get_text()
    
    # Track already found variables to avoid duplicates
    found_variables = set()
    
    # Pattern for {{variable}} - BLUE (hashVariable)
    for match in re.finditer(r'\{\{([^}]+)\}\}', text_content):
        variable_name = match.group(1).strip()
        full_variable = '{{' + variable_name + '}}'
        if full_variable not in found_variables:
            found_variables.add(full_variable)
            annotations.append({
                'type': 'element',
                'elementtype': 'hashVariable',
                'variablename': variable_name,
                'label': f"Variable: {variable_name}",
                'selector': f'textvariable:{full_variable}',
            })
    
    # Pattern for [[variable]] - GREEN (bracketVariable)
    for match in re.finditer(r'\[\[([^\]]+)\]\]', text_content):
        variable_name = match.group(1).strip()
        full_variable = '[[' + variable_name + ']]'
        if full_variable not in found_variables:
            found_variables.add(full_variable)
            annotations.append({
                'type': 'element',
                'elementtype': 'bracketVariable',
                'variablename': variable_name,
                'label': f"Variable: {variable_name}",
                'selector': f'textvariable:{full_variable}',
            })
    
    # Pattern for ##variable## - BLUE (hashVariable)
    for match in re.finditer(r'##([^#]+)##', text_content):
        variable_name = match.group(1).strip()
        full_variable = '##' + variable_name + '##'
        if full_variable not in found_variables:
            found_variables.add(full_variable)
            annotations.append({
                'type': 'element',
                'elementtype': 'hashVariable',
                'variablename': variable_name,
                'label': f"Variable: {variable_name}",
                'selector': f'textvariable:{full_variable}',
            })
    
    return annotations


def generate_selector_for_element(element):
    """
    Generate a CSS selector for a BeautifulSoup element.
    """
    if element.get('id'):
        return f"#{element['id']}"
    
    if element.name == 'a':
        link_text = element.get_text(strip=True)
        if link_text and len(link_text) < 100 and '{{' not in link_text and '[[' not in link_text:
            return f'linktext:{link_text}'
        elif element.get('href'):
            href = element.get('href')
            if '{{' in href or '[[' in href:
                safe_part = href.split('{{')[0].split('[[')[0].rstrip('?')
                if len(safe_part) > 10:
                    return f'[href*="{safe_part}"]'
            else:
                return f'[href="{href[:100]}"]'
    
    if element.get('name'):
        return f'[name="{element["name"]}"]'
    
    selector = element.name
    if element.get('class'):
        classes = [c for c in element.get('class', []) if c]
        if classes:
            selector += '.' + '.'.join(classes)
    
    return selector


def inject_visual_annotations(html_content, annotations):
    """
    Inject visual annotations into HTML for preview in the editor.
    NOTE: This does NOT handle text-level variables - JavaScript handles those.
    """
    soup = BeautifulSoup(html_content, 'html.parser')
    
    if not soup.head:
        head = soup.new_tag('head')
        if soup.html:
            soup.html.insert(0, head)
        else:
            soup.insert(0, head)
    
    style_tag = soup.new_tag('style')
    style_tag.string = """
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
    """
    soup.head.append(style_tag)
    
    for annotation in annotations:
        selector = annotation.get('selector', '')
        
        # Skip text-level annotations - handled by JavaScript
        if not selector:
            continue
        if 'textvariable:' in selector or 'linktext:' in selector or 'textselection:' in selector:
            continue
        
        try:
            elements = soup.select(selector)
            if not elements:
                continue
            
            element = elements[0]
            element['data-annotation-id'] = annotation.get('id', '')
            
            existing_classes = element.get('class', [])
            if isinstance(existing_classes, str):
                existing_classes = [existing_classes]
            
            if annotation['type'] == 'link':
                highlight_class = 'annotation-highlight-link'
            else:
                highlight_class = 'annotation-highlight-element'
            
            existing_classes.append(highlight_class)
            element['class'] = existing_classes
                
        except Exception as e:
            print(f"Error applying annotation for selector {selector}: {e}")
            continue
    
    return str(soup)


def create_annotation_overlays_for_pdf(html_content, annotations):
    """
    Create visual overlays for PDF generation with margin annotations.
    """
    soup = BeautifulSoup(html_content, 'html.parser')
    
    if soup.body:
        container = soup.new_tag('div', style='display: flex; position: relative; min-height: 100vh;')
        content_area = soup.new_tag('div', style='flex: 1; padding-right: 20px; max-width: 65%;')
        
        body_children = list(soup.body.children)
        for child in body_children:
            content_area.append(child.extract())
        
        margin_area = soup.new_tag('div', style='width: 35%; min-width: 250px; border-left: 2px solid #ccc; padding: 20px 10px; background: #f9f9f9; font-size: 10px; font-family: Arial, sans-serif;')
        
        margin_title = soup.new_tag('div', style='font-weight: bold; font-size: 12px; margin-bottom: 15px; color: #2c3e50; border-bottom: 2px solid #3498db; padding-bottom: 5px;')
        margin_title.string = 'Annotations'
        margin_area.append(margin_title)
        
        annotation_counter = 1
        for annotation in annotations:
            selector = annotation.get('selector', '')
            
            if not selector:
                continue
            if 'linktext:' in selector or 'textvariable:' in selector or 'textselection:' in selector:
                continue
            
            try:
                elements = content_area.select(selector)
                if not elements:
                    continue
                
                element = elements[0]
                
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
                
                existing_style = element.get('style', '')
                element['style'] = f"{existing_style} background-color: {bg_color}; border-left: 3px solid {badge_color}; padding: 4px; position: relative;"
                
                badge = soup.new_tag('sup', style=f'background: {badge_color}; color: white; padding: 2px 5px; margin-left: 4px; border-radius: 3px; font-size: 9px; font-weight: bold;')
                badge.string = str(annotation_counter)
                element.insert(0, badge)
                
                margin_item = soup.new_tag('div', style=f'margin-bottom: 15px; padding: 10px; background: white; border: 1px solid #ddd; border-left: 4px solid {badge_color}; border-radius: 4px;')
                
                header_span = soup.new_tag('div', style=f'font-weight: bold; color: {badge_color}; margin-bottom: 5px;')
                header_span.string = f"{annotation_counter}. {type_label}"
                margin_item.append(header_span)
                
                label_span = soup.new_tag('div', style='margin-top: 5px; font-weight: 600;')
                label_span.string = annotation.get('label', 'Unnamed')
                margin_item.append(label_span)
                
                if annotation.get('type') == 'link' and annotation.get('url'):
                    url_span = soup.new_tag('div', style='margin-top: 3px; color: #3498db; word-break: break-all; font-size: 9px;')
                    url_span.string = f"URL: {annotation['url']}"
                    margin_item.append(url_span)
                elif annotation.get('variablename'):
                    var_span = soup.new_tag('div', style='margin-top: 3px; color: #666; font-family: monospace; font-size: 9px;')
                    var_span.string = f"Variable: {annotation['variablename']}"
                    margin_item.append(var_span)
                
                margin_area.append(margin_item)
                annotation_counter += 1
                
            except Exception as e:
                print(f"Error processing annotation for selector {selector}: {e}")
                continue
        
        container.append(content_area)
        container.append(margin_area)
        soup.body.clear()
        soup.body.append(container)
    
    return str(soup)
