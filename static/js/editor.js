// Editor JavaScript
let currentFileId = null;
let currentAnnotations = [];
let zoomLevel = 1;
let isAddMode = false;
let editingAnnotationId = null;
let currentTextSelection = null;


// Initialize editor on page load
document.addEventListener('DOMContentLoaded', function() {
    // Load the first file automatically
    const firstFile = document.querySelector('.file-item');
    if (firstFile) {
        const fileId = firstFile.dataset.fileId;
        loadFile(fileId);
    }
    
    // Setup event listeners
    setupEventListeners();
});

function setupEventListeners() {
    // File selection checkboxes
    document.querySelectorAll('.file-select').forEach(checkbox => {
        checkbox.addEventListener('click', function(e) {
            e.stopPropagation();
        });
    });
}

// Load a file and its annotations
async function loadFile(fileId) {
    try {
        // Update active state in file list
        document.querySelectorAll('.file-item').forEach(item => {
            item.classList.remove('active');
        });
        document.querySelector(`[data-file-id="${fileId}"]`).classList.add('active');
        
        currentFileId = fileId;
        
        // Show loading state
        document.getElementById('annotationList').innerHTML = '<div class="loading"><i class="fas fa-spinner"></i></div>';
        
        // Fetch file data
        const response = await fetch(`/api/get_file/${fileId}`);
        const data = await response.json();
        
        if (data.error) {
            showError('Failed to load file');
            return;
        }
        
        60
            (before iframe loads)
        currentAnnotations = data.annotations;
        console.log(`📦 Loaded ${currentAnnotations.length} annotations`);
        
        // Load HTML into iframe
        const iframe = document.getElementById('previewFrame');
        
        // CRITICAL FIX: Clear any previous onload handler
        iframe.onload = null;

            // CRITICAL FIX: Setup interaction AFTER iframe loads with delay
    iframe.onload = function() {
        console.log('🔵 Iframe loaded, waiting for DOM...');
        // Add delay to ensure iframe DOM is fully ready
        setTimeout(() => {
            try {
                setupIframeInteraction();
                displayAnnotations();
                console.log('✅ Visual highlights applied');
            } catch (error) {
                console.error('❌ Error applying highlights:', error);
            }
        }, 150); // Increased to 150ms for reliability
    };

        
        // Set the HTML content
        iframe.srcdoc = data.html;
        
        // Update title
        const fileName = document.querySelector(`[data-file-id="${fileId}"] .file-name`).textContent;
        document.getElementById('previewTitle').textContent = fileName;
        
    } catch (error) {
        console.error('Error loading file:', error);
        showError('Failed to load file');
    }
}

// Helper function to convert hex color to RGB
function hexToRgb(hex) {
    const result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex);
    return result ? {
        r: parseInt(result[1], 16),
        g: parseInt(result[2], 16),
        b: parseInt(result[3], 16)
    } : {r: 155, g: 89, b: 182}; // Default purple if parsing fails
}


// Setup click interaction in iframe
function setupIframeInteraction() {
    const iframe = document.getElementById('previewFrame');
    const iframeDoc = iframe.contentDocument || iframe.contentWindow.document;
    
    // CRITICAL: Inject CSS into iframe AFTER it loads
    injectAnnotationCSS(iframeDoc);
    
    // CRITICAL: Apply visual highlights to all annotated elements
    applyVisualHighlights(iframeDoc);
    
    // Add click handler for add mode
    iframeDoc.addEventListener('click', function(e) {
        if (isAddMode) {
            e.preventDefault();
            e.stopPropagation();
            handleElementClick(e.target);
        }
    });
    
    // Highlight annotation on hover
    iframeDoc.addEventListener('mouseover', function(e) {
        const annotationId = e.target.dataset.annotationId;
        if (annotationId) {
            highlightAnnotation(annotationId);
        }
    });
    
    iframeDoc.addEventListener('mouseout', function(e) {
        const annotationId = e.target.dataset.annotationId;
        if (annotationId) {
            unhighlightAnnotation(annotationId);
        }
    });
}

function injectAnnotationCSS(iframeDoc) {
    const style = iframeDoc.createElement('style');
    style.id = 'annotation-styles';
    style.textContent = `
        /* Annotation Highlight Styles */
        .annotation-highlight-element {
            outline: 3px solid #2ecc71 !important;
            outline-offset: 2px !important;
            position: relative !important;
            box-shadow: 0 0 10px rgba(46, 204, 113, 0.5) !important;
            background-color: rgba(46, 204, 113, 0.1) !important;
        }
        
        .annotation-highlight-link {
            outline: 3px solid #e74c3c !important;
            outline-offset: 2px !important;
            position: relative !important;
            box-shadow: 0 0 10px rgba(231, 76, 60, 0.5) !important;
            background-color: rgba(231, 76, 60, 0.1) !important;
        }
        
        .annotation-highlight-variable {
            outline: 3px solid #3498db !important;
            outline-offset: 2px !important;
            position: relative !important;
            box-shadow: 0 0 10px rgba(52, 152, 219, 0.5) !important;
            background-color: rgba(52, 152, 219, 0.15) !important;
            display: inline !important;
            padding: 2px 4px !important;
            border-radius: 3px !important;
        }
        
        .annotation-highlight-bracket {
            outline: 3px solid #2ecc71 !important;
            outline-offset: 2px !important;
            position: relative !important;
            box-shadow: 0 0 10px rgba(46, 204, 113, 0.5) !important;
            background-color: rgba(46, 204, 113, 0.15) !important;
            display: inline !important;
            padding: 2px 4px !important;
            border-radius: 3px !important;
        }
        
        .annotation-highlight-custom {
            outline-offset: 2px !important;
            position: relative !important;
            display: inline !important;
            padding: 2px 4px !important;
            border-radius: 3px !important;
            cursor: pointer;
        }
        
        /* Specific styling for inline template variables */
        span.annotation-highlight-element[data-template-var] {
            display: inline !important;
            padding: 2px 4px !important;
            border-radius: 3px !important;
            background-color: rgba(52, 152, 219, 0.15) !important;
        }
    `;

    // Remove existing annotation styles if any
    const existingStyle = iframeDoc.getElementById('annotation-styles');
    if (existingStyle) {
        existingStyle.remove();
    }

    iframeDoc.head.appendChild(style);
    console.log('✅ Annotation CSS injected into iframe');
}


// NEW FUNCTION: Apply visual highlights to annotated elements
function applyVisualHighlights(iframeDoc) {
    let highlightedCount = 0;
    let skippedCount = 0;
    let notFoundCount = 0;

    // Reset instance tracking for each page load
    window.wrappedInstances = {};

    console.log(`🎨 Attempting to highlight ${currentAnnotations.length} annotations...`);

    currentAnnotations.forEach(annotation => {
        const selector = annotation.selector;

        // CRITICAL FIX: Skip annotations without selectors
        // These are text-level annotations (customText, variables) that cannot be highlighted
        if (!selector) {
            console.log(`⏭️ Skipped "${annotation.label}" - no selector (${annotation.element_type})`);
            skippedCount++;
            return;
        }

        try {
            // Find element in iframe using CSS selector
            // IMPROVED: Handle custom selectors for email templates
            let element = null;

            // Check for custom :linktext() selector
            if (selector.includes(':linktext(')) {
                const match = selector.match(/:linktext\("(.+?)"\)/);
                if (match) {
                    const linkText = match[1];
                    // Find link by text content
                    const links = Array.from(iframeDoc.querySelectorAll('a'));
                    element = links.find(a => a.textContent.trim() === linkText.trim());
                }
            } 
            // Check for custom :textvariable() selector
            else if (selector.includes(':textvariable(')) {
                const match = selector.match(/:textvariable\("(.+?)"\)/);
                if (match) {
                    const variableText = match[1];

                    // Track how many instances of this pattern we've already wrapped
                    if (!window.wrappedInstances) {
                        window.wrappedInstances = {};
                    }
                    if (!window.wrappedInstances[variableText]) {
                        window.wrappedInstances[variableText] = 0;
                    }

                    const targetInstance = window.wrappedInstances[variableText];
                    let foundInstances = 0;

                    // Find all text nodes in the document
                    const walker = iframeDoc.createTreeWalker(
                        iframeDoc.body,
                        NodeFilter.SHOW_TEXT,
                        null,
                        false
                    );

                    let node;
                    let wrapped = false;
                    while (node = walker.nextNode()) {
                        if (wrapped) break; // Stop after wrapping the target instance

                        const text = node.textContent;
                        let searchPos = 0;

                        // Find all instances of the pattern in this text node
                        while (true) {
                            const index = text.indexOf(variableText, searchPos);
                            if (index === -1) break;

                            // Check if this is the instance we want to wrap
                            if (foundInstances === targetInstance) {
                                // Wrap this specific instance
                                const parent = node.parentNode;
                                const before = text.substring(0, index);
                                const match = text.substring(index, index + variableText.length);
                                const after = text.substring(index + variableText.length);

                                const span = iframeDoc.createElement('span');
                    // Determine if this is a bracket variable or hash variable
                    const isBracketVariable = annotation.element_type === 'bracketVariable';
                    span.className = isBracketVariable ? 'annotation-highlight-bracket' : 'annotation-highlight-variable';                                span.setAttribute('data-annotation-id', annotation.id);
                                span.textContent = match;

                                const beforeNode = iframeDoc.createTextNode(before);
                                const afterNode = iframeDoc.createTextNode(after);

                                parent.insertBefore(beforeNode, node);
                                parent.insertBefore(span, node);
                                parent.insertBefore(afterNode, node);
                                parent.removeChild(node);

                                element = span; // Set element for highlighting
                                wrapped = true;
                                window.wrappedInstances[variableText]++;
                                break;
                            }

                            foundInstances++;
                            searchPos = index + variableText.length;
                        }
                    }
                }
                   } else {
            // Use standard querySelector
            element = iframeDoc.querySelector(selector);
        }
        
        // NEW: Add this block BEFORE the "if (element)" check
        // Check for custom :textselection() selector for user-selected text
        if (selector.includes(':textselection(')) {
            const match = selector.match(/:textselection\("(.+?)"\)/);
            if (match) {
                const selectedText = match[1];
                const customColor = annotation.customColor || '#9b59b6'; // Get custom color
                
                // Find and highlight the first occurrence of this text
                const walker = iframeDoc.createTreeWalker(
                    iframeDoc.body,
                    NodeFilter.SHOW_TEXT,
                    null,
                    false
                );

                let node;
                let found = false;
                while (node = walker.nextNode()) {
                    if (found) break;
                    
                    const text = node.textContent;
                    const index = text.indexOf(selectedText);
                    
                    if (index !== -1) {
                        // Found the text - wrap it
                        const parent = node.parentNode;
                        if (parent.nodeName === 'SCRIPT' || parent.nodeName === 'STYLE') continue;
                        
                        const before = text.substring(0, index);
                        const matchText = text.substring(index, index + selectedText.length);
                        const after = text.substring(index + selectedText.length);

                        const span = iframeDoc.createElement('span');
                        span.className = 'annotation-highlight-custom';
                        span.setAttribute('data-annotation-id', annotation.id);
                        span.textContent = matchText;
                        
                        // Apply custom color using inline styles
                        const rgb = hexToRgb(customColor);
                        span.style.cssText = `
                            outline: 3px solid ${customColor} !important;
                            outline-offset: 2px !important;
                            box-shadow: 0 0 10px rgba(${rgb.r}, ${rgb.g}, ${rgb.b}, 0.5) !important;
                            background-color: rgba(${rgb.r}, ${rgb.g}, ${rgb.b}, 0.15) !important;
                            position: relative !important;
                            display: inline !important;
                            padding: 2px 4px !important;
                            border-radius: 3px !important;
                            cursor: pointer;
                        `;

                        const beforeNode = iframeDoc.createTextNode(before);
                        const afterNode = iframeDoc.createTextNode(after);

                        parent.insertBefore(beforeNode, node);
                        parent.insertBefore(span, node);
                        parent.insertBefore(afterNode, node);
                        parent.removeChild(node);

                        element = span;
                        found = true;
                    }
                }
            }
        }

        if (element) {


            if (element) {
                // Add annotation ID
                element.setAttribute('data-annotation-id', annotation.id);

                // Determine highlight class based on type
                let highlightClass = 'annotation-highlight-element';
                if (annotation.type === 'link') {
                    highlightClass = 'annotation-highlight-link';
                } else if (selector.includes(':textvariable(')) {
        // Check if it's a bracket variable or hash variable
        const isBracketVariable = annotation.element_type === 'bracketVariable';
        highlightClass = isBracketVariable ? 'annotation-highlight-bracket' : 'annotation-highlight-variable';                }

                // Add highlight class
                element.classList.add(highlightClass);

                // Ensure position relative for potential badges
                if (!element.style.position || element.style.position === 'static') {
                    element.style.position = 'relative';
                }

                highlightedCount++;
                console.log(`✅ Highlighted ${annotation.type}: ${selector}`);
            } else {
                console.warn(`⚠️ Element not found for selector: ${selector}`);
                notFoundCount++;
            }
        } catch (error) {
            console.error(`❌ Error highlighting ${selector}:`, error);
        }
    });

    console.log(`📊 Highlighting Summary:`);
    console.log(`  ✅ Highlighted: ${highlightedCount}`);
    console.log(`  ⏭️ Skipped (no selector): ${skippedCount}`);
    console.log(`  ⚠️ Not found: ${notFoundCount}`);
    console.log(`  📦 Total annotations: ${currentAnnotations.length}`);
}


// Handle element click in add mode
function handleElementClick(element) {
    // Generate CSS selector for clicked element
    const selector = generateSelectorForElement(element);
    
    // Pre-fill modal with detected information
    document.getElementById('addSelector').value = selector;
    
    // Try to detect type
    const tagName = element.tagName.toLowerCase();
    if (['input', 'textarea', 'select', 'button'].includes(tagName)) {
        document.getElementById('addType').value = 'form_field';
        document.getElementById('addName').value = element.name || element.id || '';
        document.getElementById('addLabel').value = `${tagName}: ${element.name || element.id || 'unnamed'}`;
    } else if (tagName === 'a') {
        document.getElementById('addType').value = 'hyperlink';
        document.getElementById('addUrl').value = element.href || '';
        document.getElementById('addLabel').value = element.textContent.trim() || element.href || '';
    }
    
    toggleAddFields();
    
    // Show modal
    const modal = new bootstrap.Modal(document.getElementById('addModal'));
    modal.show();
    
    // Exit add mode
    toggleAddMode();
}

// Generate CSS selector for an element
function generateSelectorForElement(element) {
    if (element.id) {
        return '#' + element.id;
    }
    
    let selector = element.tagName.toLowerCase();
    
    if (element.className) {
        const classes = element.className.split(' ').filter(c => c.trim());
        if (classes.length > 0) {
            selector += '.' + classes.join('.');
        }
    } else if (element.name) {
        selector += `[name="${element.name}"]`;
    }
    
    return selector;
}

// Display annotations in the sidebar
function displayAnnotations() {
        console.log('🔍 displayAnnotations() called with', currentAnnotations.length, 'annotations');
    const container = document.getElementById('annotationList');
    const count = document.getElementById('annotationCount');
    
    count.textContent = currentAnnotations.length;
    
    if (currentAnnotations.length === 0) {
        container.innerHTML = `
            <div class="empty-state">
                <i class="fas fa-inbox"></i>
                <p>No annotations detected</p>
            </div>
        `;
        return;
    }
    
    container.innerHTML = '';
    
    currentAnnotations.forEach((annotation, index) => {
        const item = createAnnotationItem(annotation, index);
        container.appendChild(item);
    });
    
    // Setup drag and drop
    setupDragAndDrop();
}

// Create annotation item HTML
function createAnnotationItem(annotation, index) {
    const item = document.createElement('div');
    item.className = 'annotation-item';
    item.draggable = true;
    item.dataset.annotationId = annotation.id;
    item.dataset.index = index;
    
    // FIX: Use correct type names
    const typeClass = annotation.type === 'link' ? 'annotation-type-link' : 
                 (annotation.element_type === 'bracketVariable' ? 'annotation-type-bracket' : 'annotation-type-form');
    const typeText = annotation.type === 'link' ? 'Link' : 
                (annotation.element_type === 'bracketVariable' ? 'Bracket' : 'Variable');

    
    let detailsHTML = '';
    if (annotation.type === 'link' && annotation.url) {
        detailsHTML = `<div><strong>URL:</strong> ${annotation.url}</div>`;
    } else if (annotation.type === 'element') {
        if (annotation.variable_name) {
            detailsHTML += `<div><strong>Variable:</strong> ${annotation.variable_name}</div>`;
        } else if (annotation.name) {
            detailsHTML += `<div><strong>Name:</strong> ${annotation.name}</div>`;
        }
        if (annotation.input_type) {
            detailsHTML += `<div><strong>Type:</strong> ${annotation.input_type}</div>`;
        }
    }
    
    item.innerHTML = `
        <div class="annotation-item-header">
            <span class="annotation-type-badge ${typeClass}">${typeText}</span
>
            <div class="annotation-actions">
                <button class="annotation-action-btn edit" onclick="editAnnotation('${annotation.id}')" title="Edit">
                    <i class="fas fa-edit"></i>
                </button>
                <button class="annotation-action-btn delete" onclick="deleteAnnotation('${annotation.id}')" title="Delete">
                    <i class="fas fa-trash"></i>
                </button>
            </div>
        </div>
        <div class="annotation-label">${annotation.label}</div>
        <div class="annotation-details">
            ${detailsHTML}
        </div>
    `;
    
    return item;
}

// Setup drag and drop for reordering annotations
function setupDragAndDrop() {
    const items = document.querySelectorAll('.annotation-item');
    
    items.forEach(item => {
        item.addEventListener('dragstart', handleDragStart);
        item.addEventListener('dragover', handleDragOver);
        item.addEventListener('drop', handleDrop);
        item.addEventListener('dragend', handleDragEnd);
    });
}

let draggedItem = null;

function handleDragStart(e) {
    draggedItem = this;
    this.classList.add('dragging');
    e.dataTransfer.effectAllowed = 'move';
}

function handleDragOver(e) {
    e.preventDefault();
    e.dataTransfer.dropEffect = 'move';
    
    const afterElement = getDragAfterElement(e.clientY);
    if (afterElement == null) {
        this.parentNode.appendChild(draggedItem);
    } else {
        this.parentNode.insertBefore(draggedItem, afterElement);
    }
}

function handleDrop(e) {
    e.stopPropagation();
    return false;
}

function handleDragEnd(e) {
    this.classList.remove('dragging');
    
    // Update annotation order
    const items = document.querySelectorAll('.annotation-item');
    const newOrder = [];
    items.forEach(item => {
        const id = item.dataset.annotationId;
        const annotation = currentAnnotations.find(a => a.id === id);
        if (annotation) {
            newOrder.push(annotation);
        }
    });
    
    currentAnnotations = newOrder;
    saveAnnotations();
}

function getDragAfterElement(y) {
    const draggableElements = [...document.querySelectorAll('.annotation-item:not(.dragging)')];
    
    return draggableElements.reduce((closest, child) => {
        const box = child.getBoundingClientRect();
        const offset = y - box.top - box.height / 2;
        
        if (offset < 0 && offset > closest.offset) {
            return { offset: offset, element: child };
        } else {
            return closest;
        }
    }, { offset: Number.NEGATIVE_INFINITY }).element;
}



// Toggle add annotation mode
function toggleAddMode() {
    const iframe = document.getElementById('previewFrame');
    const iframeDoc = iframe.contentDocument || iframe.contentWindow.document;
    
    // Get current text selection from iframe
    const selection = iframeDoc.getSelection();
    
    if (selection && selection.toString().trim().length > 0) {
        // User has selected text - capture it
        const selectedText = selection.toString();
        const range = selection.getRangeAt(0);
        
        // Store selection info
        currentTextSelection = {
            text: selectedText,
            startContainer: range.startContainer,
            endContainer: range.endContainer,
            startOffset: range.startOffset,
            endOffset: range.endOffset
        };
        
        // Pre-fill the modal
        document.getElementById('addLabel').value = selectedText.substring(0, 50) + (selectedText.length > 50 ? '...' : '');
        document.getElementById('addSelector').value = `:textselection("${selectedText.substring(0, 100).replace(/"/g, '\\"')}")`;
        document.getElementById('addType').value = 'element';
        document.getElementById('addName').value = 'custom-text-selection';
        
        // Set default color (purple)
        document.getElementById('addColor').value = '#9b59b6';
        
        // Show color picker for custom selections
        document.getElementById('addColorGroup').style.display = 'block';
        
        toggleAddFields();
        
        // Show modal
        const modal = new bootstrap.Modal(document.getElementById('addModal'));
        modal.show();
    } else {
        // No text selected - show message
        alert('Please select some text in the preview first, then click "Add Annotation"');
    }
}



// Save annotation edit
async function saveAnnotationEdit() {
    const annotation = currentAnnotations.find(a => a.id === editingAnnotationId);
    if (!annotation) return;
    
    // Update annotation
    annotation.label = document.getElementById('editLabel').value;
    
    if (annotation.type === 'link') {
        annotation.url = document.getElementById('editUrl').value;
    } else {
        annotation.name = document.getElementById('editName').value;
        
    // Save comments
    annotation.comments = document.getElementById('annotationComments').value;
    }
    
    // Save to server
    await saveAnnotations();
    
    // Refresh display
    displayAnnotations();
    
    // Close modal
    bootstrap.Modal.getInstance(document.getElementById('editModal')).hide();
}

// Toggle add modal fields based on type
function toggleAddFields() {
    const type = document.getElementById('addType').value;

    if (type === 'hyperlink' || type === 'link') {
        document.getElementById('addUrlGroup').style.display = 'block';
        document.getElementById('addNameGroup').style.display = 'none';
        document.getElementById('addColorGroup').style.display = 'none'; // Hide color for links
    } else {
        document.getElementById('addUrlGroup').style.display = 'none';
        document.getElementById('addNameGroup').style.display = 'block';
        // Color picker visibility controlled by toggleAddMode
    }
}



// Delete annotation
async function deleteAnnotation(annotationId) {
    if (!confirm('Are you sure you want to delete this annotation?')) {
        return;
    }
    
    try {
        const response = await fetch('/api/delete_annotation', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                file_id: currentFileId,
                annotation_id: annotationId
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            currentAnnotations = currentAnnotations.filter(a => a.id !== annotationId);
            displayAnnotations();
            loadFile(currentFileId); // Reload to update preview
        } else {
            showError('Failed to delete annotation');
        }
    } catch (error) {
        console.error('Error deleting annotation:', error);
        showError('Failed to delete annotation');
    }
}

// Toggle add modal fields based on type
function toggleAddFields() {
    const type = document.getElementById('addType').value;
    
    if (type === 'hyperlink') {
        document.getElementById('addUrlGroup').style.display = 'block';
        document.getElementById('addNameGroup').style.display = 'none';
    } else {
        document.getElementById('addUrlGroup').style.display = 'none';
        document.getElementById('addNameGroup').style.display = 'block';
    }
}

// Save new annotation
async function saveNewAnnotation() {
    const type = document.getElementById('addType').value;
    const label = document.getElementById('addLabel').value;
    const selector = document.getElementById('addSelector').value;
    const customColor = document.getElementById('addColor').value; // Get selected color

    if (!label || !selector) {
        alert('Please fill in all required fields');
        return;
    }

    const newAnnotation = {
        type: type,
        label: label,
        selector: selector,
        element_type: type === 'hyperlink' ? 'a' : 'textSelection',
        text: currentTextSelection ? currentTextSelection.text : '',
        customColor: customColor || '#9b59b6' // Store custom color
    };

    if (type === 'hyperlink' || type === 'link') {
        newAnnotation.url = document.getElementById('addUrl').value;
    } else {
        newAnnotation.name = document.getElementById('addName').value || 'custom-selection';
        newAnnotation.input_type = 'textSelection';
        
        // Store selection data for highlighting
        if (currentTextSelection) {
            newAnnotation.selectionData = {
                text: currentTextSelection.text
            };
        }
    }

    try {
        const response = await fetch('/api/add_annotation', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                file_id: currentFileId,
                annotation: newAnnotation
            })
        });

        const data = await response.json();

        if (data.success) {
            currentAnnotations.push(data.annotation);
            displayAnnotations();
            loadFile(currentFileId); // Reload to update preview

            // Close modal and reset form
            bootstrap.Modal.getInstance(document.getElementById('addModal')).hide();
            document.getElementById('addLabel').value = '';
            document.getElementById('addUrl').value = '';
            document.getElementById('addName').value = '';
            document.getElementById('addSelector').value = '';
            document.getElementById('addColor').value = '#9b59b6';
            
            // Clear selection
            currentTextSelection = null;
        } else {
            showError('Failed to add annotation');
        }
    } catch (error) {
        console.error('Error adding annotation:', error);
        showError('Failed to add annotation');
    }
}


// Save annotations to server
async function saveAnnotations() {
    try {
        await fetch('/api/update_annotations', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                file_id: currentFileId,
                annotations: currentAnnotations
            })
        });
    } catch (error) {
        console.error('Error saving annotations:', error);
    }
}

// Highlight annotation
function highlightAnnotation(annotationId) {
    const item = document.querySelector(`[data-annotation-id="${annotationId}"]`);
    if (item) {
        item.style.backgroundColor = '#fff3cd';
    }
}

// Unhighlight annotation
function unhighlightAnnotation(annotationId) {
    const item = document.querySelector(`[data-annotation-id="${annotationId}"]`);
    if (item) {
        item.style.backgroundColor = '';
    }
}

// Zoom functions
function zoomIn() {
    zoomLevel = Math.min(zoomLevel + 0.1, 2);
    applyZoom();
}

function zoomOut() {
    zoomLevel = Math.max(zoomLevel - 0.1, 0.5);
    applyZoom();
}

function resetZoom() {
    zoomLevel = 1;
    applyZoom();
}

function applyZoom() {
    const iframe = document.getElementById('previewFrame');
    iframe.style.transform = `scale(${zoomLevel})`;
    iframe.style.width = `${100 / zoomLevel}%`;
    iframe.style.height = `${100 / zoomLevel}%`;
}

// Generate PDFs
async function generatePDFs() {
    const selectedFiles = [];
    document.querySelectorAll('.file-select:checked').forEach(checkbox => {
        selectedFiles.push(checkbox.dataset.fileId);
    });
    
    if (selectedFiles.length === 0) {
        alert('Please select at least one file to generate PDFs');
        return;
    }
    
    const btn = document.getElementById('generateBtn');
    btn.disabled = true;
    btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Generating...';
    
    try {
        const response = await fetch('/generate_pdfs', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ selected_files: selectedFiles })
        });
        
        if (response.ok) {
            // Download the ZIP file
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = 'annotated_email_templates.zip';
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            document.body.removeChild(a);
        } else {
            showError('Failed to generate PDFs');
        }
    } catch (error) {
        console.error('Error generating PDFs:', error);
        showError('Failed to generate PDFs');
    } finally {
        btn.disabled = false;
        btn.innerHTML = '<i class="fas fa-file-pdf"></i> Generate PDFs';
    }
}

// Clear session and start over
async function clearSession() {
    if (!confirm('Are you sure you want to cancel and start over?')) {
        return;
    }
    
    try {
        await fetch('/clear_session', { method: 'POST' });
        window.location.href = '/';
    } catch (error) {
        console.error('Error clearing session:', error);
        window.location.href = '/';
    }
}

// Show error message
function showError(message) {
    alert(message);
}
