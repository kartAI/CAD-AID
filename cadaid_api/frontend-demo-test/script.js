const API_URL = 'http://cadaid-api.westeurope.azurecontainerapps.io';
const API_KEY = '[your api key]';

async function detectDrawings() {
    const files = document.getElementById('files').files;
    const loader = document.getElementById('loader');
    const results = document.getElementById('results');

    if (files.length === 0) {
        results.innerHTML = '<div class="error">Please select at least one file to upload.</div>';
        return;
    }

    const formData = new FormData();
    for (let file of files) {
        formData.append('uploaded_files', file);
    }

    loader.style.display = 'block';
    results.innerHTML = '';

    try {
        const response = await fetch(`${API_URL}/detect`, {
            method: 'POST',
            headers: { 'x-api-key': API_KEY },
            body: formData,
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();
        displayResults(data);
    } catch (error) {
        results.innerHTML = `<div class="error">Error: ${error.message}</div>`;
    } finally {
        loader.style.display = 'none';
    }
}

function displayResults(data) {
    const results = document.getElementById('results');
    results.innerHTML = '';

    data.forEach(item => {
        const resultDiv = document.createElement('div');
        resultDiv.className = 'result-item';
        
        const content = `
            <h3>File: ${item.filename}</h3>
            <p>Drawing Types: ${item.drawing_types.join(', ')}</p>
            ${item.cardinal_direction ? `<p>Cardinal Direction: ${item.cardinal_direction}</p>` : ''}
            ${item.scale ? `<p>Scale: ${item.scale}</p>` : ''}
            ${item.room_names ? `<p>Rooms: ${item.room_names.join(', ')}</p>` : ''}
            <p>Confidence: ${item.confidence.map(c => (c * 100).toFixed(1) + '%').join(', ')}</p>
        `;
        
        resultDiv.innerHTML = content;
        results.appendChild(resultDiv);
    });
}