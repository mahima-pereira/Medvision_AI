document.addEventListener('DOMContentLoaded', () => {
    const uploadArea = document.getElementById('upload-area');
    const fileInput = document.getElementById('file-input');
    const previewSection = document.getElementById('preview-section');
    const previewImage = document.getElementById('preview-image');
    const analyzing = document.getElementById('analyzing');
    const results = document.getElementById('results');
    const scanType = document.getElementById('scan-type');
    const findingsList = document.getElementById('findings-list');

    const handleFile = async (file) => {
        if (!file.type.startsWith('image/')) {
            alert('Please upload a valid medical scan image');
            return;
        }

        // Show preview
        previewSection.classList.remove('hidden');
        results.classList.add('hidden');
        analyzing.classList.remove('hidden');
        uploadArea.classList.add('hidden');
        
        const reader = new FileReader();
        reader.onload = (e) => {
            previewImage.src = e.target.result;
        };
        reader.readAsDataURL(file);

        const formData = new FormData();
        formData.append('file', file);

        try {
            const detectResponse = await fetch('/detect-scan-type', {
                method: 'POST',
                body: formData
            });
            
            if (!detectResponse.ok) {
                throw new Error('Failed to detect scan type');
            }
            
            const detectData = await detectResponse.json();
            if (detectData.error) {
                throw new Error(detectData.error);
            }
            
            const analysisResponse = await fetch(`/predict/${detectData.scan_type}`, {
                method: 'POST',
                body: formData
            });
            
            if (!analysisResponse.ok) {
                throw new Error('Failed to analyze scan');
            }
            
            const results = await analysisResponse.json();
            if (results.error) {
                throw new Error(results.error);
            }
            
            displayResults(detectData.scan_type, results);
        } catch (error) {
            console.error('Error:', error);
            alert(`Error: ${error.message || 'Failed to analyze scan. Please try again.'}`);
            uploadArea.classList.remove('hidden');
        } finally {
            analyzing.classList.add('hidden');
        }
    };

    const displayResults = (type, data) => {
        results.classList.remove('hidden');
        scanType.textContent = `Scan Type: ${type.toUpperCase()}`;
        
        findingsList.innerHTML = data.findings.map(finding => `
            <div class="finding-item">
                <div class="finding-header">
                    <span>${finding.condition}</span>
                    <span>${finding.probability.toFixed(1)}%</span>
                </div>
                <div class="progress-bar">
                    <div class="progress-value" style="width: ${finding.probability}%"></div>
                </div>
            </div>
        `).join('');
    };

    // Handle drag and drop
    uploadArea.addEventListener('dragover', (e) => {
        e.preventDefault();
        uploadArea.style.borderColor = 'var(--primary)';
    });

    uploadArea.addEventListener('dragleave', () => {
        uploadArea.style.borderColor = 'var(--border)';
    });

    uploadArea.addEventListener('drop', (e) => {
        e.preventDefault();
        uploadArea.style.borderColor = 'var(--border)';
        const file = e.dataTransfer.files[0];
        handleFile(file);
    });

    // Handle click to upload
    uploadArea.addEventListener('click', () => {
        fileInput.click();
    });

    fileInput.addEventListener('change', (e) => {
        const file = e.target.files[0];
        if (file) handleFile(file);
    });
});