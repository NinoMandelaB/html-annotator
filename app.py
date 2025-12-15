# Import required libraries
from flask import Flask, render_template, request, send_file, flash, redirect, url_for, jsonify, session
import os
import tempfile
import zipfile
import io
import json
import uuid
from werkzeug.utils import secure_filename
from html_parser import parse_html_and_detect_elements, inject_visual_annotations
from pdf_generator import convert_annotated_html_to_pdf
from datetime import timedelta
from flask_session import Session
import redis
from bs4 import BeautifulSoup, NavigableString

# Initialize the Flask application
app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "your_secret_key_change_in_production_" + str(uuid.uuid4()))

# Session configuration for Railway with Redis
app.config['SESSION_TYPE'] = 'redis'
app.config['SESSION_PERMANENT'] = True
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=2)
app.config['SESSION_COOKIE_SECURE'] = True
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'

# Configure Redis connection
redis_url = os.environ.get('REDIS_URL', 'redis://localhost:6379')
app.config['SESSION_REDIS'] = redis.from_url(redis_url)

# Initialize session
Session(app)

# Configuration
ALLOWED_EXTENSIONS = {'html', 'htm'}
MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size


def allowed_file(filename):
    """Check if the file has an allowed extension."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def wrap_text_with_style(soup, text_to_find, bg_color, border_color):
    """Wrap all occurrences of text with styled span"""
    for element in soup.find_all(text=lambda t: t and text_to_find in str(t)):
        if isinstance(element, NavigableString):
            parent = element.parent
            if parent.name in ['script', 'style']:
                continue
            
            # Split text and wrap matches
            text = str(element)
            if text_to_find not in text:
                continue
                
            parts = text.split(text_to_find)
            parent.clear()
            
            for i, part in enumerate(parts):
                if part:
                    parent.append(NavigableString(part))
                if i < len(parts) - 1:
                    span = soup.new_tag('span', style=f'background-color: {bg_color}; border: 1px solid {border_color}; padding: 2px;')
                    span.string = text_to_find
                    parent.append(span)


def wrap_text_occurrence(soup, text_to_find, occurrence_index, custom_color):
    """Wrap a specific occurrence of text with custom color"""
    current_occurrence = 0
    
    for element in soup.find_all(text=lambda t: t and text_to_find in str(t)):
        if isinstance(element, NavigableString):
            parent = element.parent
            if parent.name in ['script', 'style']:
                continue
            
            text = str(element)
            index = 0
            
            while index < len(text):
                pos = text.find(text_to_find, index)
                if pos == -1:
                    break
                
                if current_occurrence == occurrence_index:
                    # Found the right occurrence - wrap it
                    before = text[:pos]
                    match = text[pos:pos + len(text_to_find)]
                    after = text[pos + len(text_to_find):]
                    
                    parent.clear()
                    if before:
                        parent.append(NavigableString(before))
                    
                    # Convert hex to rgba with transparency
                    span = soup.new_tag('span', style=f'background-color: {custom_color}; border: 1px solid {custom_color}; padding: 2px; opacity: 0.6;')
                    span.string = match
                    parent.append(span)
                    
                    if after:
                        parent.append(NavigableString(after))
                    
                    return  # Done
                
                current_occurrence += 1
                index = pos + 1


@app.route("/", methods=["GET"])
def index():
    """
    Main route - displays the upload form.
    """
    # Clear any error messages from session
    session.pop('_flashes', None)
    return render_template("index.html")


@app.route("/upload", methods=["POST"])
def upload():
    """
    Handle file upload and initial annotation detection.
    Returns a session ID and redirects to the editor.
    """
    print("Upload endpoint called")  # Debug
    print(f"request.files: {request.files}")  # Debug
    print(f"request.files keys: {list(request.files.keys())}")  # Debug
    
    # Check if files were included in the request
    if "files" not in request.files:
        print("No 'files' in request.files")  # Debug
        flash("No files selected")
        return redirect(url_for('index'))
    
    # Get list of all uploaded files
    files = request.files.getlist("files")
    print(f"Number of files: {len(files)}")  # Debug
    
    # Check if no files were selected or all files are empty
    if not files or all(file.filename == "" for file in files):
        print("Files list is empty or all filenames are empty")  # Debug
        flash("No files selected")
        return redirect(url_for('index'))
    
    # Validate that all uploaded files are HTML
    for file in files:
        print(f"Processing file: {file.filename}")  # Debug
        if not allowed_file(file.filename):
            flash(f"File {file.filename} is not an HTML file")
            return redirect(url_for('index'))
    
    try:
        # Generate a unique session ID for this upload batch
        session_id = str(uuid.uuid4())
        
        # Process each HTML file and store annotations
        all_files_data = []
        
        for file in files:
            # Read HTML content
            html_content = file.read().decode('utf-8', errors='ignore')
            original_filename = secure_filename(file.filename)
            print(f"Read {len(html_content)} characters from {original_filename}")  # Debug
            
            # NEW: Parse HTML directly - the new parser handles everything internally
            annotations = parse_html_and_detect_elements(html_content)
            print(f"Detected {len(annotations)} annotations in {original_filename}")  # Debug
            
            # Store file data - only need one copy of HTML now
            file_data = {
                "id": str(uuid.uuid4()),
                "filename": original_filename,
                "html_content": html_content,  # Store original HTML
                "annotations": annotations
            }
            
            all_files_data.append(file_data)
        
        # Store in session
        session['files_data'] = all_files_data
        session['session_id'] = session_id
        session.permanent = True
        print(f"Stored {len(all_files_data)} files in session")  # Debug
        print(f"Session ID: {session_id}")  # Debug
        
        # Redirect to editor
        return redirect(url_for('editor'))
    
    except Exception as e:
        print(f"Error in upload: {str(e)}")  # Debug
        import traceback
        traceback.print_exc()
        flash(f"Error processing files: {str(e)}")
        return redirect(url_for('index'))


@app.route("/editor", methods=["GET"])
def editor():
    """
    Display the annotation editor interface.
    """
    print("Editor endpoint called")  # Debug
    print(f"Session keys: {list(session.keys())}")  # Debug
    print(f"'files_data' in session: {'files_data' in session}")  # Debug
    
    # Check if we have files in session
    if 'files_data' not in session:
        print("No files_data in session, redirecting to index")  # Debug
        flash("No files to edit. Please upload files first.")
        return redirect(url_for('index'))
    
    files_data = session['files_data']
    print(f"Rendering editor with {len(files_data)} files")  # Debug
    
    return render_template("editor.html", files_data=files_data)


@app.route("/api/get_file/<file_id>", methods=["GET"])
def get_file(file_id):
    """
    API endpoint to get a specific file's HTML content with annotations injected.
    """
    if 'files_data' not in session:
        return jsonify({"error": "No files in session"}), 404
    
    files_data = session['files_data']
    
    # Find the file
    file_data = next((f for f in files_data if f['id'] == file_id), None)
    
    if not file_data:
        return jsonify({"error": "File not found"}), 404
    
    # FIXED: Return ORIGINAL HTML without server-side injection
    # Let JavaScript handle ALL visual highlights in the iframe
    return jsonify({
        "html": file_data['html_content'],  # Changed from inject_visual_annotations()
        "annotations": file_data['annotations']
    })


@app.route("/api/update_annotations", methods=["POST"])
def update_annotations():
    """
    API endpoint to update annotations for a specific file.
    """
    if 'files_data' not in session:
        return jsonify({"error": "No files in session"}), 404
    
    data = request.get_json()
    file_id = data.get('file_id')
    updated_annotations = data.get('annotations')
    
    if not file_id or updated_annotations is None:
        return jsonify({"error": "Missing file_id or annotations"}), 400
    
    files_data = session['files_data']
    
    # Find and update the file
    for file_data in files_data:
        if file_data['id'] == file_id:
            file_data['annotations'] = updated_annotations
            session['files_data'] = files_data
            session.modified = True
            return jsonify({"success": True})
    
    return jsonify({"error": "File not found"}), 404


@app.route("/api/add_annotation", methods=["POST"])
def add_annotation():
    """
    API endpoint to add a new annotation manually.
    """
    if 'files_data' not in session:
        return jsonify({"error": "No files in session"}), 404
    
    data = request.get_json()
    file_id = data.get('file_id')
    new_annotation = data.get('annotation')
    
    if not file_id or not new_annotation:
        return jsonify({"error": "Missing file_id or annotation"}), 400
    
    files_data = session['files_data']
    
    # Find the file and add annotation
    for file_data in files_data:
        if file_data['id'] == file_id:
            # Generate unique ID for new annotation
            new_annotation['id'] = str(uuid.uuid4())
            file_data['annotations'].append(new_annotation)
            session['files_data'] = files_data
            session.modified = True
            return jsonify({"success": True, "annotation": new_annotation})
    
    return jsonify({"error": "File not found"}), 404


@app.route("/api/delete_annotation", methods=["POST"])
def delete_annotation():
    """
    API endpoint to delete an annotation.
    """
    if 'files_data' not in session:
        return jsonify({"error": "No files in session"}), 404
    
    data = request.get_json()
    file_id = data.get('file_id')
    annotation_id = data.get('annotation_id')
    
    if not file_id or not annotation_id:
        return jsonify({"error": "Missing file_id or annotation_id"}), 400
    
    files_data = session['files_data']
    
    # Find the file and remove annotation
    for file_data in files_data:
        if file_data['id'] == file_id:
            file_data['annotations'] = [
                a for a in file_data['annotations']
                if a['id'] != annotation_id
            ]
            session['files_data'] = files_data
            session.modified = True
            return jsonify({"success": True})
    
    return jsonify({"error": "File not found"}), 404


@app.route('/generate_pdfs', methods=['POST'])
def generate_pdfs():
    """
    Generate PDFs from selected files with their annotations.
    Returns a ZIP file containing all annotated PDFs.
    """
    if 'files_data' not in session:
        return jsonify({'error': 'No files to process'}), 404
    
    data = request.get_json()
    selected_file_ids = data.get('selected_files', [])
    
    if not selected_file_ids:
        return jsonify({'error': 'No files selected'}), 400
    
    files_data = session['files_data']
    
    try:
        # Create a ZIP file in memory
        zip_buffer = io.BytesIO()
        
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED, False) as zip_file:
            for file_data in files_data:
                if file_data['id'] in selected_file_ids:
                    try:
                        print(f"📄 Processing '{file_data['filename']}' for PDF generation")
                        
                        # Parse the HTML
                        soup = BeautifulSoup(file_data['html_content'], 'html.parser')
                        
                        # Apply highlights directly to the HTML
                        for annotation in file_data['annotations']:
                            selector = annotation.get('selector', '')
                            
                            # Handle linktext: selectors
                            if 'linktext:' in selector:
                                link_text = selector.split('linktext:')[1].strip('"\'')
                                for link in soup.find_all('a'):
                                    if link.get_text(strip=True) == link_text:
                                        link['style'] = 'background-color: #ffebee; border: 1px solid #e74c3c; padding: 2px;'
                                        print(f"  ✓ Highlighted link: {link_text}")
                            
                            # Handle textvariable: selectors (e.g., {{var}} or #var#)
                            elif 'textvariable:' in selector:
                                variable_text = selector.split('textvariable:')[1].strip('"\'')
                                element_type = annotation.get('elementtype', 'hashVariable')
                                
                                # Choose color based on variable type
                                if element_type == 'bracketVariable':
                                    bg_color = '#e8f5e9'
                                    border_color = '#4caf50'
                                else:  # hashVariable
                                    bg_color = '#e3f2fd'
                                    border_color = '#2196f3'
                                
                                # Find and wrap all occurrences
                                wrap_text_with_style(soup, variable_text, bg_color, border_color)
                                print(f"  ✓ Highlighted variable: {variable_text}")
                            
                            # Handle textselection: custom highlights
                            elif 'textselection:' in selector:
                                selected_text = selector.split('textselection:')[1].strip('"\'')
                                custom_color = annotation.get('customColor', '#9b59b6')
                                occurrence_index = annotation.get('occurrenceIndex', 0)
                                
                                # Wrap specific occurrence with custom color
                                wrap_text_occurrence(soup, selected_text, occurrence_index, custom_color)
                                print(f"  ✓ Highlighted text selection: {selected_text[:30]}...")
                            
                            # Handle regular CSS selectors
                            elif selector:
                                try:
                                    elements = soup.select(selector)
                                    if elements:
                                        elements[0]['style'] = 'background-color: #e3f2fd; border: 1px solid #2196f3; padding: 2px;'
                                        print(f"  ✓ Highlighted element: {selector}")
                                except Exception as selector_error:
                                    print(f"  ⚠️ Could not apply selector: {selector} - {selector_error}")
                        
                        # Convert modified HTML to PDF
                        modified_html = str(soup)
                        pdf_bytes = convert_annotated_html_to_pdf(modified_html, [])
                        
                        # Create filename
                        original_name = os.path.splitext(file_data['filename'])[0]
                        pdf_filename = f"annotated_{original_name}.pdf"
                        
                        # Add to ZIP
                        zip_file.writestr(pdf_filename, pdf_bytes)
                        print(f"✅ Successfully added '{pdf_filename}' to ZIP")
                    
                    except Exception as file_error:
                        # Log the error but continue processing other files
                        print(f"❌ Error processing file '{file_data['filename']}': {str(file_error)}")
                        import traceback
                        traceback.print_exc()
                        
                        # Create an error file in the ZIP
                        error_message = f"Error generating PDF for {file_data['filename']}:\n{str(file_error)}"
                        error_filename = f"ERROR_{file_data['filename']}.txt"
                        zip_file.writestr(error_filename, error_message)
        
        zip_buffer.seek(0)
        return send_file(
            zip_buffer,
            as_attachment=True,
            download_name='annotated_email_templates.zip',
            mimetype='application/zip'
        )
    
    except Exception as e:
        print(f"❌ Error generating PDFs: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'Error generating PDFs: {str(e)}'}), 500


@app.route("/clear_session", methods=["POST"])
def clear_session():
    """
    Clear the current session and start over.
    """
    session.clear()
    return jsonify({"success": True})


# Run the application
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=False)
