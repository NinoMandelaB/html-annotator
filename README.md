# HTML Email Template Annotator

A sophisticated web application for automatically detecting and annotating form fields and hyperlinks in HTML email templates, with an interactive editor and PDF export functionality.

## Live Demo

- **Production**: [html-annotator-production.up.railway.app](https://html-annotator-production.up.railway.app)

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
- **Redis-based session management** for reliable multi-instance deployment
- Professional UI with drag-and-drop support

## Quick Start

### Local Development

1. **Clone the repository**:
   ```bash
   git clone https://github.com/NinoMandelaB/html-annotator.git
   cd html-annotator
   ```

2. **Install Redis** (for session storage):
   
   **macOS:**
   ```bash
   brew install redis
   brew services start redis
   ```
   
   **Ubuntu/Debian:**
   ```bash
   sudo apt-get install redis-server
   sudo systemctl start redis
   ```
   
   **Windows:**
   - Download from [Redis Windows](https://github.com/microsoftarchive/redis/releases)
   - Or use WSL2 with Ubuntu installation

3. **Install Python dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the application**:
   ```bash
   python app.py
   ```

5. **Open your browser**:
   ```
   http://localhost:5000
   ```

### Railway Deployment

1. **Add Redis to your Railway project**:
   - Go to your Railway dashboard
   - Click "+ New" → "Database" → "Add Redis"
   - Railway automatically creates the `REDIS_URL` environment variable

2. **Push to GitHub**:
   ```bash
   git add .
   git commit -m "Deploy with Redis session support"
   git push origin main
   ```

3. **Railway Configuration**:
   - Railway automatically detects your Flask app
   - Redis connection is established via `REDIS_URL` environment variable
   - The app uses the `PORT` environment variable for web binding
   - Sessions persist across container restarts using Redis

4. **Deploy**:
   - Railway deploys automatically on push
   - Your app will be available at: `https://your-app.up.railway.app`

## Architecture

### Session Management

The application uses **Redis for distributed session storage**, which provides:

- ✅ **Persistent sessions** across container restarts
- ✅ **Horizontal scalability** with multiple app instances
- ✅ **Fast in-memory access** for session data
- ✅ **Automatic expiration** (2-hour session lifetime)
- ✅ **Production-ready** for cloud deployments

Session data (uploaded files, annotations) is stored in Redis instead of filesystem, making the app compatible with ephemeral container environments like Railway.

## Project Structure

```
html-annotator/
├── app.py                  # Main Flask application with Redis session config
├── html_parser.py          # HTML parsing and annotation detection
├── pdf_generator.py        # HTML to PDF conversion
├── requirements.txt        # Python dependencies (includes Redis)
├── templates/
│   ├── index.html         # Upload page
│   └── editor.html        # Annotation editor
├── static/
│   ├── css/
│   │   └── editor.css     # Editor styling
│   └── js/
│       └── editor.js      # Editor JavaScript logic
└── README.md              # This file
```

## Dependencies

- **Flask 2.3.2**: Web framework
- **Flask-Session 0.6.0**: Server-side session management
- **Redis 5.0.1**: In-memory data store for sessions
- **BeautifulSoup4 4.12.2**: HTML parsing
- **lxml 5.3.0**: XML/HTML parser backend
- **pdfkit 1.0.0**: HTML to PDF conversion
- **Werkzeug 2.3.6**: WSGI utilities

## Configuration

### Environment Variables

```bash
SECRET_KEY=your_secret_key_here      # Flask secret key for sessions
PORT=5000                            # Port to run the application
REDIS_URL=redis://localhost:6379     # Redis connection URL (auto-set on Railway)
```

### Session Configuration

The app is configured with secure session settings:
- **Session Type**: Redis-backed
- **Session Lifetime**: 2 hours
- **Cookie Security**: HTTPS-only (in production)
- **Cookie HttpOnly**: Yes
- **Cookie SameSite**: Lax

## Troubleshooting

### Redis Connection Issues

**Local Development:**
```bash
# Check if Redis is running
redis-cli ping
# Should return: PONG

# Start Redis if not running
# macOS: brew services start redis
# Linux: sudo systemctl start redis
```

**Railway Deployment:**
- Ensure Redis service is added to your Railway project
- Check that `REDIS_URL` environment variable is set
- View Railway logs for connection errors

### Session Not Persisting

If sessions are lost between requests:
1. Verify Redis is running and accessible
2. Check `REDIS_URL` environment variable is correct
3. Ensure Flask-Session is properly initialized
4. Check Railway logs for Redis connection errors

## Changelog

### Version 2.1.0 (Current)
- ✨ Switched to Redis-based session storage for production reliability
- ✨ Added support for horizontal scaling with multiple app instances
- ✨ Implemented automatic session expiration (2-hour TTL)
- 🐛 Fixed session persistence issues on Railway deployment
- 📝 Updated documentation with Redis setup instructions

### Version 2.0.0
- Complete rewrite from PDF to HTML processing
- Added interactive annotation editor
- Implemented drag-and-drop annotation management
- Added click-to-add annotation feature
- Improved UI with three-panel layout
- Added zoom controls for preview
- Enhanced annotation detection algorithm
- PDF export with margin notes (original style preserved)

### Version 1.0.0
- PDF link annotator with automatic URL detection
- Red box annotations with margin text

## Technical Details

### Why Redis for Sessions?

Traditional filesystem-based sessions don't work on cloud platforms with ephemeral storage (like Railway). Redis solves this by:

1. **Persistence**: Data survives container restarts
2. **Speed**: In-memory storage provides microsecond latency
3. **Scalability**: Multiple app instances can share session data
4. **TTL Support**: Automatic cleanup of expired sessions
5. **Production-Ready**: Used by major companies for session management

### Session Data Flow

```
User uploads files → Flask processes → Stores in Redis
                                            ↓
                                    Session ID in cookie
                                            ↓
User navigates to editor → Flask reads session ID → Retrieves data from Redis
```

All session management is transparent to the application code - Flask-Session handles the Redis interaction automatically.

## License

This project is open source and available under the MIT License.

## Credits

Developed by [NinoMandelaB](https://github.com/NinoMandelaB)
