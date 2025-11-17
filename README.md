# HTML Email Template Annotator

A sophisticated web application for automatically detecting and annotating form fields and hyperlinks in HTML email templates, with an interactive editor and PDF export functionality.

## Live Demo

- **Production**: [Your Railway URL]

## Features

### 🎯 Core Functionality
- **Multi-file Upload**: Process multiple HTML email templates simultaneously
- **Automatic Detection**:
  - Form fields (input, textarea, select, button elements)
  - Hyperlinks (a tags with href attributes)
  - Email links (mailto: links)
- **Interactive Editor**:
  - Real-time HTML preview with highlighted annotations
  - Drag-and-drop annotation reordering
  - Click-to-add new annotations
  - Edit existing annotations
  - Delete unwanted annotations
- **PDF Export**: Generate annotated PDFs with margin notes (similar to your original PDF annotator style)
- **Selective Download**: Choose which files to include in the final ZIP archive

### ✨ Advanced Features
- Visual annotation overlays in preview
- Color-coded annotations (blue for form fields, red for hyperlinks)
- Zoom controls for HTML preview
- Session-based file management
- Professional UI with drag-and-drop support

## Quick Start

### Local Development

1. **Clone the repository**:
   ```bash
   git clone https://github.com/NinoMandelaB/html-annotator.git
   cd pdf_annotator
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the application**:
   ```bash
   python app.py
   ```

4. **Open your browser**:
   ```
   http://localhost:5000
   ```

### Railway Deployment

1. **Push to GitHub**:
   ```bash
   git add .
   git commit -m "Update to HTML annotation app"
   git push origin main
   ```

2. **Railway Configuration**:
   - Railway will automatically detect your Flask app
   - Environment variables are set automatically
   - The app uses the PORT environment variable

3. **Deploy**:
   - Railway will deploy automatically on push
   - Your app will be available at: `https://your-app.up.railway.app`

## Project Structure

```
pdf_annotator/
├── app.py                      # Main Flask application
├── html_parser.py              # HTML parsing and annotation detection
├── pdf_generator.py            # HTML to PDF conversion
├── requirements.txt            # Python dependencies
├── templates/
│   ├── index.html              # Upload page
│   └── editor.html             # Annotation editor
├── static/
│   ├── css/
│   │   └── editor.css          # Editor styling
│   └── js/
│       └── editor.js           # Editor JavaScript logic
└── README.md                   # This file
```

## How It Works

### 1. Upload HTML Files
- Drag and drop or browse to select one or more HTML email template files
- The app validates that all files are HTML format (.html or .htm)

### 2. Automatic Detection
The app parses each HTML file and automatically detects:

**Form Fields:**
- Input elements (text, email, password, number, date, etc.)
- Textarea elements
- Select dropdowns
- Buttons and submit inputs

**Hyperlinks:**
- All `<a>` tags with href attributes
- Email links (mailto:)
- Full URL extraction

### 3. Interactive Editor
The editor provides three main areas:

**Left Sidebar - File List:**
- Shows all uploaded files
- Displays annotation count per file
- Checkbox to select files for PDF export
- Click to switch between files

**Center - HTML Preview:**
- Live preview of your HTML template
- Visual highlights on detected elements
- Click-to-add annotation mode
- Zoom controls for better visibility

**Right Sidebar - Annotation List:**
- Lists all detected annotations
- Drag-and-drop to reorder
- Edit button to modify annotation details
- Delete button to remove annotations
- Color-coded by type (blue=form, red=link)

### 4. Edit Annotations
For each annotation, you can:
- **Edit Label**: Change the display name
- **Edit URL**: Modify hyperlink destinations
- **Edit Field Name**: Change form field identifiers
- **Add New**: Manually add annotations by clicking elements
- **Delete**: Remove false positives or unwanted annotations
- **Reorder**: Drag annotations to change their order

### 5. Generate PDFs
- Select which files to include (checkboxes in file list)
- Click "Generate PDFs" button
- The app creates annotated PDFs with:
  - Red boxes around detected elements
  - Numbered badges on each element
  - Margin area with detailed annotation information
  - Arrows connecting elements to their descriptions
- Downloads all selected files as a ZIP archive

## API Endpoints

### Public Routes
- `GET /` - Upload page
- `POST /upload` - Handle file upload and process annotations
- `GET /editor` - Annotation editor interface

### API Routes
- `GET /api/get_file/<file_id>` - Get file HTML and annotations
- `POST /api/update_annotations` - Update annotations for a file
- `POST /api/add_annotation` - Add a new annotation
- `POST /api/delete_annotation` - Delete an annotation
- `POST /generate_pdfs` - Generate and download PDFs
- `POST /clear_session` - Clear session and start over

## Configuration

### Environment Variables
```bash
SECRET_KEY=your_secret_key_here  # Flask secret key for sessions
PORT=5000                         # Port to run the application
```

### File Size Limits
- Maximum file size: 16MB per file
- Unlimited number of files per upload

## Dependencies

- **Flask 2.3.2**: Web framework
- **BeautifulSoup4 4.12.2**: HTML parsing
- **lxml 4.9.3**: XML/HTML parser backend
- **WeasyPrint 60.1**: HTML to PDF conversion
- **Pillow 10.1.0**: Image processing (required by WeasyPrint)
- **Werkzeug 2.3.6**: WSGI utilities

## Browser Support

- Chrome/Edge (recommended)
- Firefox
- Safari
- Modern browsers with ES6+ support

## Troubleshooting

### WeasyPrint Installation Issues

If you encounter issues installing WeasyPrint:

**On macOS:**
```bash
brew install python cairo pango gdk-pixbuf libffi
```

**On Ubuntu/Debian:**
```bash
sudo apt-get install build-essential python3-dev python3-pip python3-setuptools python3-wheel python3-cffi libcairo2 libpango-1.0-0 libpangocairo-1.0-0 libgdk-pixbuf2.0-0 libffi-dev shared-mime-info
```

**On Windows:**
- Download and install GTK3 runtime from https://github.com/tschoonj/GTK-for-Windows-Runtime-Environment-Installer
- Restart your terminal after installation

### Railway Deployment

WeasyPrint works on Railway with the default Python buildpack. If you encounter issues:
- Ensure all dependencies in requirements.txt are present
- Check Railway logs for specific error messages
- The app automatically uses the PORT environment variable

## Development

### Local Development with Hot Reload
```bash
export FLASK_ENV=development
python app.py
```

### Testing
Upload sample HTML email templates to test:
- Contact forms
- Newsletter templates
- Transactional emails
- Marketing emails

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is open source and available under the MIT License.

## Support

For issues, questions, or contributions, please open an issue on GitHub.

## Changelog

### Version 2.0.0 (Current)
- Complete rewrite from PDF to HTML processing
- Added interactive annotation editor
- Implemented drag-and-drop annotation management
- Added click-to-add annotation feature
- Improved UI with three-panel layout
- Added zoom controls for preview
- Enhanced annotation detection algorithm
- PDF export with margin notes (original style preserved)

### Version 1.0.0 (Previous)
- PDF link annotator with automatic URL detection
- Red box annotations with margin text

## Credits

Developed by [NinoMandelaB](https://github.com/NinoMandelaB)

## Screenshots

### Upload Page
Modern, gradient interface with drag-and-drop file upload support.

### Editor Interface
Three-panel layout with file list, HTML preview, and annotation management.

### PDF Output
Annotated PDFs with numbered elements and margin descriptions, similar to the original PDF annotator style.