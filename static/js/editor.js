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

// Helper function to convert hex color to RGB
function hexToRgb(hex) {
    const result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex);
    return result ? {
        r: parseInt(result[1], 16),
        g: parseInt(result[2], 16),
        b: parseInt(result[3], 16)
    } : { r: 155, g: 89, b: 182 }; // Default purple if parsing fails
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
        
        // Store annotations FIRST (before iframe loads)
        currentAnnotations = data.annotations;
        console.log(`📦 Loaded ${currentAnnotations.length} annotations`);
        displayAnnotations();
        
        // Load HTML into iframe
        const iframe = document.getElementById('previewFrame');
        
        // CRITICAL FIX: Clear any previous onload handler
        iframe.onload = null;
        
        // Set the HTML content
        iframe.srcdoc = data.html;
        
        // CRITICAL FIX: Setup interaction AFTER iframe loads with delay
        iframe.onload = function() {
            console.log('🔵 Iframe loaded, waiting for DOM...');
            // Add delay to ensure iframe DOM is fully ready
            setTimeout(() => {
                try {
                    setupIframeInteraction();
                    console.log('✅ Visual highlights applied');
                } catch (error) {
                    console.error('❌ Error applying highlights:', error);
                }
            }, 150); // Increased to 150ms for reliability
        };
        
        // Update title
        const fileName = document.querySelector(`[data-file-id="${fileId}"] .file-name`).textContent;
        document.getElementById('previewTitle').textContent = fileName;
        
    } catch (error) {
        console.error('Error loading file:', error);
        showError('Failed to load file');
    }
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
    const occurrenceIndex = e.target.dataset.occurrenceIndex;
    if (annotationId !== undefined) {
        highlightAnnotation(annotationId, occurrenceIndex);
    }
});

iframeDoc.addEventListener('mouseout', function(e) {
    const annotationId = e.target.dataset.annotationId;
    const occurrenceIndex = e.target.dataset.occurrenceIndex;
    if (annotationId !== undefined) {
        unhighlightAnnotation(annotationId, occurrenceIndex);
    }
});


}

//Inject annotation CSS into iframe
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


// Apply visual highlights to annotated elements
function applyVisualHighlights(iframeDoc) {
 let highlightedCount = 0;
 let skippedCount = 0;
 let notFoundCount = 0;
 console.log('Attempting to highlight', currentAnnotations.length, 'annotations...');
 
 currentAnnotations.forEach(annotation => {
   const selector = annotation.selector;
   // Skip annotations without selectors
   if (!selector) {
     console.log('Skipped', annotation.label, '- no selector', annotation.elementtype);
     skippedCount++;
     return;
   }
   try {
     let element = null;
     
     // Custom selector: linktext("...")
     if (selector.includes('linktext')) {
       const match = selector.match(/:linktext\(\"(.+?)\"\)/);
       if (match) {
         const linkText = match[1];
         const links = Array.from(iframeDoc.querySelectorAll('a'));
         element = links.find(a => a.textContent.trim() === linkText.trim());
         
         if (element) {
           element.setAttribute('data-annotation-id', annotation.id);
           element.setAttribute('data-occurrence-index', annotation.occurrenceIndex || 0);
           element.classList.add('annotation-highlight-link');
           if (!element.style.position || element.style.position === 'static') {
             element.style.position = 'relative';
           }
         }
       }
     }
     // Custom selector: textvariable("##accFname##") / "[accFname]"
     else if (selector.includes('textvariable')) {
       const match = selector.match(/:textvariable\(\"(.+?)\"\)/);
       if (match) {
         const variableText = match[1];
         const targetOccurrenceIndex = annotation.occurrenceIndex !== undefined 
           ? annotation.occurrenceIndex 
           : 0;
         
         // Helper: normalize whitespace for comparison
         const normalizeWhitespace = (text) => {
           return text.replace(/\s+/g, ' ').trim();
         };
         
         const normalizedVariableText = normalizeWhitespace(variableText);
         
         // FIRST PASS: Collect all occurrences with their locations
         const occurrences = [];
         const walker = iframeDoc.createTreeWalker(
           iframeDoc.body,
           NodeFilter.SHOW_TEXT,
           null,
           false
         );
         
         let node;
         let globalOccurrenceCount = 0;
         
         while ((node = walker.nextNode())) {
           if (!node.textContent || !node.textContent.includes(variableText.substring(0, 5))) continue;
           
           const parent = node.parentNode;
           if (!parent || parent.nodeName === 'SCRIPT' || parent.nodeName === 'STYLE') continue;
           
           const text = node.textContent;
           
           // For bracket variables, try normalized matching
           if (variableText.includes('[')) {
             const normalizedText = normalizeWhitespace(text);
             let searchPos = 0;
             
             while (searchPos < normalizedText.length) {
               const index = normalizedText.indexOf(normalizedVariableText, searchPos);
               if (index === -1) break;
               
               occurrences.push({
                 node: node,
                 parent: parent,
                 text: text,
                 normalizedIndex: index,
                 normalizedLength: normalizedVariableText.length,
                 occurrenceIndex: globalOccurrenceCount,
                 isNormalized: true
               });
               
               globalOccurrenceCount++;
               searchPos = index + normalizedVariableText.length;
             }
           } else {
             // For other variables, use exact matching
             let searchPos = 0;
             
             while (searchPos < text.length) {
               const index = text.indexOf(variableText, searchPos);
               if (index === -1) break;
               
               occurrences.push({
                 node: node,
                 parent: parent,
                 text: text,
                 exactIndex: index,
                 exactLength: variableText.length,
                 occurrenceIndex: globalOccurrenceCount,
                 isNormalized: false
               });
               
               globalOccurrenceCount++;
               searchPos = index + variableText.length;
             }
           }
         }
         
         console.log(`Found ${occurrences.length} total occurrences of "${variableText}". Looking for occurrence #${targetOccurrenceIndex}`);
         
         // SECOND PASS: Find and wrap the specific target occurrence
         const targetOccurrence = occurrences.find(occ => occ.occurrenceIndex === targetOccurrenceIndex);
         
         if (targetOccurrence) {
           const { node, parent, text } = targetOccurrence;
           
           // If normalized, we need to find the actual character positions in the original text
           let index, length;
           if (targetOccurrence.isNormalized) {
             // For normalized matches, find the substring in the original
             // This is approximate - we search for key parts of the variable
             const firstPart = variableText.substring(0, Math.min(10, variableText.length));
             index = text.indexOf(firstPart);
             length = variableText.length;
             
             if (index === -1) {
               // Fallback: try to find any part
               const cleanedText = normalizeWhitespace(text);
               index = cleanedText.indexOf(normalizedVariableText);
               if (index !== -1) {
                 // Map back to original text (this is approximate)
                 length = variableText.length;
               }
             }
           } else {
             index = targetOccurrence.exactIndex;
             length = targetOccurrence.exactLength;
           }
           
           if (index !== -1 && index !== undefined) {
             const before = text.substring(0, index);
             const varText = text.substring(index, index + length);
             const after = text.substring(index + length);
             
             const span = iframeDoc.createElement('span');
             const isBracketVariable = annotation.elementtype === 'bracketVariable';
             span.className = isBracketVariable 
               ? 'annotation-highlight-bracket'
               : 'annotation-highlight-variable';
             span.setAttribute('data-annotation-id', annotation.id);
             span.setAttribute('data-occurrence-index', targetOccurrence.occurrenceIndex);
             span.textContent = varText;
             
             const fragment = iframeDoc.createDocumentFragment();
             if (before) fragment.appendChild(iframeDoc.createTextNode(before));
             fragment.appendChild(span);
             if (after) fragment.appendChild(iframeDoc.createTextNode(after));
             
             parent.replaceChild(fragment, node);
             element = span;
             
             console.log(
               'Wrapped variable',
               annotation.variableName || annotation.name,
               'occurrence',
               targetOccurrence.occurrenceIndex,
               'with id',
               annotation.id
             );
           }
         } else {
           console.warn(
             'Could not find occurrence',
             targetOccurrenceIndex,
             'of variable',
             variableText,
             'for annotation id',
             annotation.id,
             `(only found ${occurrences.length} occurrences)`
           );
         }
       }
     }
     // Custom selector: textselection("...")
     else if (selector.includes('textselection')) {
       const match = selector.match(/:textselection\(\"(.+?)\"\)/);
       if (match) {
         const selectedText = match[1];
         const customColor = annotation.customColor || '#9b59b6';
         const occurrenceIndex = annotation.occurrenceIndex || 0;
         
         // FIRST PASS: Collect all occurrences
         const occurrences = [];
         const walker = iframeDoc.createTreeWalker(
           iframeDoc.body,
           NodeFilter.SHOW_TEXT,
           null,
           false
         );
         
         let node;
         let currentOccurrence = 0;
         
         while ((node = walker.nextNode())) {
           const text = node.textContent;
           if (!text || !text.includes(selectedText)) continue;
           
           let searchIndex = 0;
           while (searchIndex < text.length) {
             const index = text.indexOf(selectedText, searchIndex);
             if (index === -1) break;
             
             const parent = node.parentNode;
             if (!parent || parent.nodeName === 'SCRIPT' || parent.nodeName === 'STYLE') {
               searchIndex = index + 1;
               continue;
             }
             
             occurrences.push({
               node: node,
               parent: parent,
               index: index,
               occurrenceNum: currentOccurrence
             });
             
             currentOccurrence++;
             searchIndex = index + 1;
           }
         }
         
         // SECOND PASS: Find and wrap the specific target occurrence
         const targetOccurrence = occurrences.find(occ => occ.occurrenceNum === occurrenceIndex);
         
         if (targetOccurrence) {
           const { node, parent, index } = targetOccurrence;
           const text = node.textContent;
           
           const before = text.substring(0, index);
           const matchText = text.substring(index, index + selectedText.length);
           const after = text.substring(index + selectedText.length);
           
           const span = iframeDoc.createElement('span');
           span.className = 'annotation-highlight-custom';
           span.setAttribute('data-annotation-id', annotation.id);
           span.setAttribute('data-occurrence-index', occurrenceIndex);
           span.textContent = matchText;
           
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
           console.log('Highlighted occurrence', occurrenceIndex, 'of selected text');
         } else {
           console.warn(
             'Could not find occurrence',
             occurrenceIndex,
             'of selected text for annotation id',
             annotation.id
           );
         }
       }
     }
     // Standard CSS selector path (form fields, links, etc.)
     else {
       element = iframeDoc.querySelector(selector);
       if (element) {
         element.setAttribute('data-annotation-id', annotation.id);
         element.setAttribute('data-occurrence-index', annotation.occurrenceIndex || 0);
         let highlightClass = 'annotation-highlight-element';
         if (annotation.type === 'link') {
           highlightClass = 'annotation-highlight-link';
         } else if (selector.includes('textvariable')) {
           const isBracketVariable = annotation.elementtype === 'bracketVariable';
           highlightClass = isBracketVariable
             ? 'annotation-highlight-bracket'
             : 'annotation-highlight-variable';
         }
         element.classList.add(highlightClass);
         if (!element.style.position || element.style.position === 'static') {
           element.style.position = 'relative';
         }
       }
     }
     
     if (element) {
       highlightedCount++;
     } else {
       notFoundCount++;
     }
   } catch (error) {
     console.error('Error highlighting selector', annotation.selector, error);
   }
 });
 
 console.log('Highlighting Summary');
 console.log(' Highlighted:', highlightedCount);
 console.log(' Skipped (no selector):', skippedCount);
 console.log(' Not found:', notFoundCount);
 console.log(' Total annotations:', currentAnnotations.length);
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

    // Do NOT group variables; every annotation object is one row
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
 item.dataset.occurrenceIndex = annotation.occurrenceIndex !== undefined ? annotation.occurrenceIndex : 0;
 item.dataset.index = index;
 
 // Determine badge class and text based on type
 let typeClass = 'annotation-type-variable'; // default for variables
 let typeText = 'Variable';
 if (annotation.type === 'link') {
   typeClass = 'annotation-type-link';
   typeText = 'Link';
 } else if (annotation.elementtype === 'bracketVariable') {
   typeClass = 'annotation-type-bracket';
   typeText = 'Bracket';
 } else if (annotation.elementtype === 'textSelection' || annotation.inputtype === 'textSelection') {
   typeClass = 'annotation-type-custom';
   typeText = 'Custom';
 } else if (annotation.type === 'element' && annotation.inputtype && annotation.inputtype !== 'variable') {
   // form fields etc.
   typeClass = 'annotation-type-form';
   typeText = 'Element';
 }
 
 // Build details HTML
 let detailsHTML = '';
 if (annotation.type === 'link') {
   if (annotation.url) {
     detailsHTML += `<div><strong>URL:</strong> ${annotation.url}</div>`;
   }
 } else if (annotation.type === 'element') {
   if (annotation.variablename || annotation.variable_name) {
     const varName = annotation.variablename || annotation.variable_name;
     detailsHTML += `<div><strong>Variable:</strong> ${varName}</div>`;
   } else if (annotation.name) {
     detailsHTML += `<div><strong>Name:</strong> ${annotation.name}</div>`;
   }
   if (annotation.inputtype) {
     detailsHTML += `<div><strong>Type:</strong> ${annotation.inputtype}</div>`;
   }
   if (typeof annotation.occurrenceIndex === 'number') {
     detailsHTML += `<div><strong>Occurrence:</strong> ${annotation.occurrenceIndex + 1}</div>`;
   } else if (typeof annotation.occurrence_index === 'number') {
     // from Python parser
     detailsHTML += `<div><strong>Occurrence:</strong> ${annotation.occurrence_index + 1}</div>`;
   }
 }
 
 // NEW: Add comments if present
 let commentsHTML = '';
 if (annotation.comments && annotation.comments.trim().length > 0) {
   commentsHTML = `
     <div class="annotation-comments" style="
       margin-top: 8px;
       padding: 8px;
       background-color: #f0f4f8;
       border-left: 3px solid #3498db;
       border-radius: 3px;
       font-size: 12px;
       color: #2c3e50;
       line-height: 1.4;
       max-height: 60px;
       overflow-y: auto;
     ">
       <strong style="display: block; margin-bottom: 4px; font-size: 11px; color: #7f8c8d; text-transform: uppercase;">Comments</strong>
       <div style="white-space: pre-wrap; word-break: break-word;">${annotation.comments}</div>
     </div>
   `;
 }
 
 // NEW: Apply custom color inline for custom text selections
 let badgeStyle = '';
 if (annotation.customColor) {
   typeClass = 'annotation-type-custom';
   badgeStyle = `style="background-color: ${annotation.customColor};"`;
 }
 
 item.innerHTML = `
   <div class="annotation-item-header">
     <span class="annotation-type-badge ${typeClass}" ${badgeStyle}>${typeText}</span>
     <div class="annotation-actions">
       <button class="annotation-action-btn edit" onclick="editAnnotation('${annotation.id}')" title="Edit">
         <i class="fas fa-edit"></i>
       </button>
       <button class="annotation-action-btn delete" onclick="deleteAnnotation('${annotation.id}')" title="Delete">
         <i class="fas fa-trash"></i>
       </button>
     </div>
   </div>
   <div class="annotation-label">${annotation.label || 'Unnamed annotation'}</div>
   <div class="annotation-details">
     ${detailsHTML}
   </div>
   ${commentsHTML}
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
        
        // ⭐ CRITICAL FIX: Calculate which occurrence this is
        const occurrenceIndex = findOccurrenceIndex(iframeDoc, selectedText, range);
        
        // Store selection info with occurrence index
        currentTextSelection = {
            text: selectedText,
            startContainer: range.startContainer,
            endContainer: range.endContainer,
            startOffset: range.startOffset,
            endOffset: range.endOffset,
            occurrenceIndex: occurrenceIndex  // ⭐ NEW: Store which occurrence
        };
        
        // Pre-fill the modal
        document.getElementById('addLabel').value = selectedText.substring(0, 50) + (selectedText.length > 50 ? '...' : '');
        document.getElementById('addSelector').value = `:textselection("${selectedText.substring(0, 100).replace(/"/g, '\\"')}")`;
        document.getElementById('addType').value = 'element';
        document.getElementById('addName').value = 'custom-text-selection';
        
        // Set default color (purple) - ONLY if the field exists
        const colorField = document.getElementById('addColor');
        if (colorField) {
            colorField.value = '#9b59b6';
        }
        
        // Show color picker for custom selections - ONLY if the group exists
        const colorGroup = document.getElementById('addColorGroup');
        if (colorGroup) {
            colorGroup.style.display = 'block';
        }
        
        toggleAddFields();
        
        // Show modal
        const modal = new bootstrap.Modal(document.getElementById('addModal'));
        modal.show();
    } else {
        // No text selected - show message
        alert('Please select some text in the preview first, then click "Add Annotation".');
    }
}

// ⭐ NEW FUNCTION: Find which occurrence of the text was selected
function findOccurrenceIndex(iframeDoc, selectedText, range) {
    const walker = iframeDoc.createTreeWalker(
        iframeDoc.body,
        NodeFilter.SHOW_TEXT,
        null,
        false
    );
    
    let node;
    let occurrenceIndex = 0;
    const selectionStartContainer = range.startContainer;
    const selectionStartOffset = range.startOffset;
    
    while (node = walker.nextNode()) {
        const text = node.textContent;
        let searchIndex = 0;
        
        while (searchIndex < text.length) {
            const index = text.indexOf(selectedText, searchIndex);
            if (index === -1) break;
            
            // Check if this is the selected occurrence
            if (node === selectionStartContainer && index === selectionStartOffset) {
                console.log(`Found selected text at occurrence #${occurrenceIndex}`);
                return occurrenceIndex;
            }
            
            // Also check if the selection starts within this occurrence
            if (node === selectionStartContainer && 
                selectionStartOffset >= index && 
                selectionStartOffset <= index + selectedText.length) {
                console.log(`Found selected text at occurrence #${occurrenceIndex} (within match)`);
                return occurrenceIndex;
            }
            
            occurrenceIndex++;
            searchIndex = index + 1;
        }
    }
    
    console.log(`Could not find exact occurrence, defaulting to 0`);
    return 0;
}



// Edit annotation
function editAnnotation(annotationId) {
    const annotation = currentAnnotations.find(a => a.id === annotationId);
    if (!annotation) return;
    
    editingAnnotationId = annotationId;
    
    // Fill form
    document.getElementById('editLabel').value = annotation.label;
    document.getElementById('editType').value = annotation.type;
    
    if (annotation.type === 'link') {
        document.getElementById('urlFieldGroup').style.display = 'block';
        document.getElementById('nameFieldGroup').style.display = 'none';
        document.getElementById('editUrl').value = annotation.url || '';
    } else {
        document.getElementById('urlFieldGroup').style.display = 'none';
        document.getElementById('nameFieldGroup').style.display = 'block';
        document.getElementById('editName').value = annotation.name || '';
    }
    
    // Load comments
    const commentsField = document.getElementById('annotationComments');
    if (commentsField) {
        commentsField.value = annotation.comments || '';
    }
    
    // Show modal
    const modal = new bootstrap.Modal(document.getElementById('editModal'));
    modal.show();
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
    
    if (type === 'link') {
        document.getElementById('addUrlGroup').style.display = 'block';
        document.getElementById('addNameGroup').style.display = 'none';
    } else {
        document.getElementById('addUrlGroup').style.display = 'none';
        document.getElementById('addNameGroup').style.display = 'block';
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


// Save new annotation
async function saveNewAnnotation() {
  const type = document.getElementById('addType').value;      // should be "element" for text selections
  const label = document.getElementById('addLabel').value;
  const selector = document.getElementById('addSelector').value;

  const colorField = document.getElementById('addColor');
  const customColor = colorField ? colorField.value : '#9b59b6';

  if (!label || !selector) {
    alert('Please fill in all required fields');
    return;
  }

  const occurrenceIndex = currentTextSelection
    ? currentTextSelection.occurrenceIndex
    : 0;  // fall back to 0 if something went wrong

  const newAnnotation = {
    id: Date.now().toString(),
    type: 'element',                 // match existing custom annotations
    label,
    selector,                        // must start with "textselection"
    elementtype: 'textSelection',    // critical for the textSelection branch
    inputtype: 'textSelection',
    customColor,
    occurrenceIndex
  };

  currentAnnotations.push(newAnnotation);
  await saveAnnotations();
  displayAnnotations();
  loadFile(currentFileId);           // reload to re-apply highlights

  const modalEl = document.getElementById('addModal');
  const modal = bootstrap.Modal.getInstance(modalEl);
  if (modal) modal.hide();
}


// Highlight annotation
function highlightAnnotation(annotationId, occurrenceIndex) {
    const selector = occurrenceIndex !== undefined
        ? `[data-annotation-id="${annotationId}"][data-occurrence-index="${occurrenceIndex}"]`
        : `[data-annotation-id="${annotationId}"]`;
    const item = document.querySelector(selector);
    if (item) {
        item.style.backgroundColor = '#fff3cd';
        item.style.borderColor = '#ffc107';
    }
}

// Unhighlight annotation
function unhighlightAnnotation(annotationId, occurrenceIndex) {
    const selector = occurrenceIndex !== undefined
        ? `[data-annotation-id="${annotationId}"][data-occurrence-index="${occurrenceIndex}"]`
        : `[data-annotation-id="${annotationId}"]`;
    const item = document.querySelector(selector);
    if (item) {
        item.style.backgroundColor = '';
        item.style.borderColor = '';
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