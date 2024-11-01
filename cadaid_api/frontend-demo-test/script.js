const API_URL = 'http://cadaid-api.westeurope.azurecontainer.io';
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

async function detectDrawings() {
    console.log('Button clicked');
    const files = document.getElementById('files').files;
    console.log('Files selected:', files.length);
    const loader = document.getElementById('loader');
    const results = document.getElementById('results');
    
    if (files.length === 0) {
        results.innerHTML = '<div class="error">Please select at least one file</div>';
        return;
    }

    const formData = new FormData();
    for (let file of files) {
        formData.append('uploaded_files', file);
        console.log('Adding file:', file.name);
    }

    loader.style.display = 'block';
    results.innerHTML = '';

    try {
        console.log('Making request to:', `${API_URL}/detect/`);
        
        const response = await fetch(`${API_URL}/detect/`, {
            method: 'POST',
            headers: {
                'X-API-KEY': API_KEY
            },
            body: formData
        });

        console.log('Response status:', response.status);
        console.log('Response headers:', Object.fromEntries(response.headers));

        if (!response.ok) {
            const errorText = await response.text();
            console.error('Error response:', errorText);
            throw new Error(`HTTP error! status: ${response.status}, message: ${errorText}`);
        }

        const data = await response.json();
        console.log('Response data:', data);
        displayResults(data);
    } catch (error) {
        console.error('Detailed error:', error);
        results.innerHTML = `<div class="error">Error: ${error.message}</div>`;
    } finally {
        loader.style.display = 'none';
    }
}

function displayResults(data) {
    console.log('Displaying results:', data);
    const results = document.getElementById('results');
    results.innerHTML = '';

    // Handle both array and single object responses
    const items = Array.isArray(data) ? data : [data];

    items.forEach(item => {
        if (!item) return;
        
        const resultDiv = document.createElement('div');
        resultDiv.className = 'result-item';
        
        resultDiv.innerHTML = `
            <h3>File: ${item.filename || 'Unknown'}</h3>
            <p>Drawing Types: ${item.drawing_types ? item.drawing_types.join(', ') : 'None detected'}</p>
            ${item.cardinal_direction ? `<p>Cardinal Direction: ${item.cardinal_direction}</p>` : ''}
            ${item.scale ? `<p>Scale: ${item.scale}</p>` : ''}
            ${item.room_names ? `<p>Room Names: ${item.room_names.join(', ')}</p>` : ''}
        `;
        
        results.appendChild(resultDiv);
    });
}