document.getElementById('configForm').addEventListener('submit', function(event) {
    event.preventDefault();
    
    const config = {
        chunkSize: document.getElementById('chunkSize').value,
        chunkOverlap: document.getElementById('chunkOverlap').value,
        includeImages: document.getElementById('includeImages').checked,
        inputDir: document.getElementById('inputDir').value,
        outputDir: document.getElementById('outputDir').value,
        proxyPort: document.getElementById('proxyPort').value,
        chainlitPort: document.getElementById('chainlitPort').value
    };
    
    fetch('/save_config', { // Replace with your actual endpoint
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(config)
    })
    .then(response => response.json())
    .then(data => {
        console.log('Success:', data);
        alert('Configuration saved successfully!');
    })
    .catch(error => {
        console.error('Error:', error);
        alert('Failed to save configuration.');
    });
});
