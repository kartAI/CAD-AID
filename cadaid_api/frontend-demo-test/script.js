const API_URL = 'http://localhost:8000'; // Change when deploying
const FEEDBACK_URL = 'http://localhost:8001'; // Change when deploying
const API_KEY = 'your-api-key-here';


document.addEventListener('DOMContentLoaded', function() {
    const detectButton = document.getElementById('detectButton');
    detectButton.addEventListener('click', detectDrawings);
    
    // Test connection on page load
    testConnection();
});

async function testConnection() {
    try {
        const response = await fetch(`${API_URL}/detect/health`);
        console.log('Health check status:', response.status);
        const data = await response.json();
        console.log('Health check response:', data);
    } catch (error) {
        console.error('Health check failed:', error);
    }
}

let currentResults = null;
let currentFileIndex = 0;

async function detectDrawings() {
    console.log('Button clicked');
    const files = document.getElementById('files').files;
    if (files.length === 0) {
        showError('Please select at least one file');
        return;
    }

    const loader = document.getElementById('loader');
    const processingStatus = document.getElementById('processingStatus');
    const progressFill = document.querySelector('.progress-fill');
    
    loader.style.display = 'block';
    
    const formData = new FormData();
    for (let file of files) {
        formData.append('uploaded_files', file);
        console.log('Adding file:', file.name);
    }

    try {
        // Show initial processing status
        processingStatus.textContent = `Processing ${files.length} file(s)...`;
        progressFill.style.width = '0%';

        // Simulate progress updates while waiting for response
        let progress = 0;
        const progressInterval = setInterval(() => {
            progress += 1;
            if (progress <= 90) {  // Max 90% until we get actual response
                progressFill.style.width = `${progress}%`;
                processingStatus.textContent = 
                    `Processing ${files.length} file(s)... Estimated time remaining: ${Math.round((100-progress) * 0.88)}s`;
            }
        }, 880);  // Update every 880ms (88 seconds total)

        const response = await fetch(`${API_URL}/detect/`, {
            method: 'POST',
            headers: { 'X-API-KEY': API_KEY },
            body: formData
        });

        clearInterval(progressInterval);

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        // Show completion
        progressFill.style.width = '100%';
        processingStatus.textContent = 'Processing complete!';

        const data = await response.json();
        currentResults = data;
        
        // Initialize file viewer
        initializeFileViewer(files, data);
        
    } catch (error) {
        showError(`Error: ${error.message}`);
    } finally {
        setTimeout(() => {
            loader.style.display = 'none';
        }, 1000);
    }
}

function initializeFileViewer(files, results) {
    const fileList = document.querySelector('.file-list');
    const viewerContainer = document.querySelector('.file-viewer-container');
    
    fileList.innerHTML = '';
    
    // Create thumbnails for each file
    files.forEach((file, index) => {
        const thumbnail = document.createElement('img');
        thumbnail.className = 'file-thumbnail';
        thumbnail.onclick = () => showFile(index);
        
        const reader = new FileReader();
        reader.onload = (e) => {
            thumbnail.src = e.target.result;
        };
        reader.readAsDataURL(file);
        
        fileList.appendChild(thumbnail);
    });
    
    viewerContainer.style.display = 'block';
    showFile(0);  // Show first file by default
}

function showFile(index) {
    currentFileIndex = index;
    const result = currentResults[index];
    const file = document.getElementById('files').files[index];
    
    // Update thumbnail selection
    document.querySelectorAll('.file-thumbnail').forEach((thumb, i) => {
        thumb.classList.toggle('active', i === index);
    });
    
    // Load file into canvas
    const canvas = document.getElementById('viewerCanvas');
    const ctx = canvas.getContext('2d');
    
    const reader = new FileReader();
    reader.onload = (e) => {
        const img = new Image();
        img.onload = () => {
            // Set canvas size to match image
            canvas.width = img.width;
            canvas.height = img.height;
            ctx.drawImage(img, 0, 0);
            
            // Draw detections if checkbox is checked
            if (document.getElementById('toggleBboxes').checked) {
                drawDetections(result, canvas);
            }
        };
        img.src = e.target.result;
    };
    reader.readAsDataURL(file);
    
    // Update detection details
    showDetectionDetails(result);
}

function drawDetections(result, canvas) {
    const overlay = document.querySelector('.detection-overlay');
    overlay.innerHTML = '';
    
    result.detections.forEach((detection, index) => {
        // Draw bounding box
        const bbox = document.createElement('div');
        bbox.className = 'bbox-overlay';
        bbox.style.left = `${detection.bbox[0]}px`;
        bbox.style.top = `${detection.bbox[1]}px`;
        bbox.style.width = `${detection.bbox[2] - detection.bbox[0]}px`;
        bbox.style.height = `${detection.bbox[3] - detection.bbox[1]}px`;
        
        // Add type label
        const label = document.createElement('div');
        label.className = 'field-overlay';
        label.textContent = `${detection.drawing_type} (${Math.round(detection.confidence * 100)}%)`;
        label.style.left = `${detection.bbox[0]}px`;
        label.style.top = `${detection.bbox[1] - 20}px`;
        
        overlay.appendChild(bbox);
        overlay.appendChild(label);
        
        // Add field overlays if enabled
        if (document.getElementById('toggleFields').checked) {
            drawFieldOverlays(detection, overlay);
        }
    });
}

function drawFieldOverlays(detection, overlay) {
    const fields = [];
    
    switch(detection.drawing_type.toLowerCase()) {
        case 'situasjonskart':
        case 'fasade':
            if (detection.cardinal_direction) fields.push(`Direction: ${detection.cardinal_direction}`);
            if (detection.scale) fields.push(`Scale: ${detection.scale}`);
            if (detection.gnr_bnr) fields.push(`Gnr/Bnr: ${detection.gnr_bnr}`);
            break;
        case 'snitt':
            if (detection.scale) fields.push(`Scale: ${detection.scale}`);
            break;
        case 'plantegning':
            if (detection.scale) fields.push(`Scale: ${detection.scale}`);
            if (detection.gnr_bnr) fields.push(`Gnr/Bnr: ${detection.gnr_bnr}`);
            if (detection.room_names) {
                fields.push('Rooms: ' + detection.room_names.map(r => 
                    `${r.name}${r.size ? ` (${r.size}m²)` : ''}`).join(', '));
            }
            break;
    }
    
    fields.forEach((field, index) => {
        const fieldOverlay = document.createElement('div');
        fieldOverlay.className = 'field-overlay';
        fieldOverlay.textContent = field;
        fieldOverlay.style.left = `${detection.bbox[0]}px`;
        fieldOverlay.style.top = `${detection.bbox[1] - 20 - index * 20}px`;
        overlay.appendChild(fieldOverlay);
    });
}

// Add keyboard shortcuts for navigation
document.addEventListener('keydown', (e) => {
    if (e.key === 'ArrowLeft') {
        showPreviousFile();
    } else if (e.key === 'ArrowRight') {
        showNextFile();
    } else if (e.key === 'b') {
        document.getElementById('toggleBboxes').click();
    } else if (e.key === 'f') {
        document.getElementById('toggleFields').click();
    }
});

// Add zoom functionality to viewer
function setupZoom() {
    const canvas = document.getElementById('viewerCanvas');
    let scale = 1;
    let panning = false;
    let pointX = 0;
    let pointY = 0;
    let start = { x: 0, y: 0 };

    canvas.addEventListener('mousewheel', (e) => {
        e.preventDefault();
        const xs = (e.clientX - pointX) / scale;
        const ys = (e.clientY - pointY) / scale;
        scale += e.deltaY * -0.01;
        scale = Math.min(Math.max(0.1, scale), 4);
        pointX = e.clientX - xs * scale;
        pointY = e.clientY - ys * scale;
        applyTransform();
    });

    function applyTransform() {
        canvas.style.transform = `translate(${pointX}px, ${pointY}px) scale(${scale})`;
    }
}