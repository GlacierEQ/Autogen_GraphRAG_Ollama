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
    
    console.log('Configuration saved:', config);
    alert('Configuration saved successfully!');
});
