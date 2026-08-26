function scanProduct() {
    // This is a placeholder for future OpenCV + EasyOCR integration
    
    // Simulate a scan delay
    const btn = document.querySelector('.btn-success');
    const originalText = btn.innerText;
    btn.innerText = "Scanning...";
    btn.disabled = true;
    
    setTimeout(() => {
        document.getElementById('extraction-placeholder').style.display = 'none';
        document.getElementById('extraction-results').style.display = 'block';
        
        // Mock data to show the UI works
        document.getElementById('ext-name').innerText = "Sample Scanned Product";
        
        const nextWeek = new Date();
        nextWeek.setDate(nextWeek.getDate() + 7);
        document.getElementById('ext-expiry').innerText = nextWeek.toISOString().split('T')[0];
        
        btn.innerText = originalText;
        btn.disabled = false;
        
    }, 1500);
}
