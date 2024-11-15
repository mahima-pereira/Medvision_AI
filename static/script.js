document.addEventListener('DOMContentLoaded', () => {
    const xrayUpload = document.getElementById('xray-upload');
    const mriUpload = document.getElementById('mri-upload');
    const xrayInput = document.getElementById('xray-input');
    const mriInput = document.getElementById('mri-input');
    const previewSection = document.getElementById('preview-section');
    const previewImage = document.getElementById('preview-image');
    const analyzing = document.getElementById('analyzing');
    const results = document.getElementById('results');
    const scanType = document.getElementById('scan-type');
    const findingsList = document.getElementById('findings-list');

    const handleFile = async (file, scanType) => {
        if (!file.type.startsWith('image/')) {
            alert('Please upload a valid medical scan image');
            return;
        }

        // Show preview with progressive loading
        previewSection.classList.remove('hidden');
        results.classList.add('hidden');
        analyzing.classList.remove('hidden');
        
        await ImageLoader.loadProgressively(file, previewImage);

        const formData = new FormData();
        formData.append('file', file);

        try {
            // Initialize metrics display
            const metrics = new MetricsDisplay();
            
            const response = await fetch(`/predict/${scanType}`, {
                method: 'POST',
                body: formData
            });
            
            if (!response.ok) throw new Error('Failed to analyze scan');
            
            const data = await response.json();
            if (data.error) throw new Error(data.error);
            
            await displayResults(scanType, data);
            
            // Show visualization section
            document.getElementById('visualization-section').classList.remove('hidden');
            
            // Generate and display heatmap
            if (data.findings && data.findings.length > 0) {
                const heatmapCanvas = document.getElementById('heatmap-canvas');
                const visualization = new AdvancedVisualization(heatmapCanvas);
                visualization.drawHeatmap(data.findings);
            }
            
            // Stop metrics animation
            metrics.stop();
            
        } catch (error) {
            console.error('Error:', error);
            alert(`Error: ${error.message || 'Failed to analyze scan. Please try again.'}`);
        } finally {
            analyzing.classList.add('hidden');
        }
    };

    // Handle X-ray upload
    xrayUpload.addEventListener('click', () => xrayInput.click());
    xrayInput.addEventListener('change', (e) => {
        const file = e.target.files[0];
        if (file) handleFile(file, 'xray');
    });

    // Handle MRI upload
    mriUpload.addEventListener('click', () => mriInput.click());
    mriInput.addEventListener('change', (e) => {
        const file = e.target.files[0];
        if (file) handleFile(file, 'mri');
    });

    // Initialize tabs
    const initializeTabs = () => {
        const tabButtons = document.querySelectorAll('.tab-button');
        const tabPanes = document.querySelectorAll('.tab-pane');

        tabButtons.forEach(button => {
            button.addEventListener('click', () => {
                // Remove active class from all buttons and panes
                tabButtons.forEach(btn => btn.classList.remove('active'));
                tabPanes.forEach(pane => pane.classList.remove('active'));

                // Add active class to clicked button and corresponding pane
                button.classList.add('active');
                const tabId = button.dataset.tab + '-tab';
                document.getElementById(tabId).classList.add('active');
            });
        });
    };

    // Update displayResults function to include tab initialization
    const displayResults = (type, data) => {
        results.classList.remove('hidden');
        scanType.textContent = `Scan Type: ${type.toUpperCase()}`;
        
        // Regular findings display
        findingsList.innerHTML = data.findings.map(finding => `
            <div class="finding-item">
                <div class="finding-header">
                    <span>${finding.condition}</span>
                    <span>${finding.probability.toFixed(1)}%</span>
                </div>
                <div class="progress-bar">
                    <div class="progress-value" style="width: ${finding.probability}%"></div>
                </div>
                <div class="severity ${finding.severity.toLowerCase()}">${finding.severity} confidence</div>
            </div>
        `).join('');

        // Display detected issues
        const detectedIssues = document.getElementById('detected-issues');
        const significantFindings = data.findings.filter(f => f.probability > 30);
        
        if (significantFindings.length > 0) {
            detectedIssues.innerHTML = significantFindings.map(finding => `
                <div class="issue-item ${finding.severity.toLowerCase()}">
                    <div class="issue-header">
                        <strong>${finding.condition}</strong>
                        <span class="issue-probability">${finding.probability.toFixed(1)}% probability</span>
                    </div>
                    <div class="issue-description">
                        ${getIssueDescription(finding.condition, finding.severity)}
                    </div>
                </div>
            `).join('');
        } else {
            detectedIssues.innerHTML = `
                <div class="issue-item low">
                    <div class="issue-header">
                        <strong>No Significant Issues Detected</strong>
                    </div>
                    <div class="issue-description">
                        The analysis shows no significant abnormalities requiring immediate attention.
                    </div>
                </div>
            `;
        }

        // Display region findings
        displayRegionFindings(data.regions);

        // Initialize tabs
        initializeTabs();
        
        // Show first tab by default
        document.querySelector('.tab-button').click();
    };

    // Add helper function to generate issue descriptions
    const getIssueDescription = (condition, severity) => {
        const descriptions = {
            'Pneumonia': {
                'High': 'Urgent attention required: Significant infection detected in lung tissue.',
                'Moderate': 'Monitor closely: Signs of potential lung infection present.',
                'Low': 'Minor changes observed: Early signs of possible infection.'
            },
            'Cardiomegaly': {
                'High': 'Urgent evaluation needed: Significant heart enlargement detected.',
                'Moderate': 'Follow-up recommended: Moderate heart size abnormality.',
                'Low': 'Minor finding: Slight deviation in heart size.'
            },
            // Add more conditions as needed
        };

        return descriptions[condition]?.[severity] || 
               `${severity} severity: Further evaluation recommended for ${condition.toLowerCase()}.`;
    };

    // Add function to display region findings
    const displayRegionFindings = (regions) => {
        const regionFindings = document.getElementById('region-findings');
        regionFindings.innerHTML = Object.entries(regions)
            .map(([region, findings]) => `
                <div class="region-item">
                    <h4>${region.replace('_', ' ').toUpperCase()}</h4>
                    ${findings.map(finding => `
                        <div class="finding-item">
                            <div class="finding-header">
                                <span>${finding.condition}</span>
                                <span>${finding.probability.toFixed(1)}%</span>
                            </div>
                            <div class="progress-bar">
                                <div class="progress-value" 
                                     style="width: ${finding.probability}%">
                                </div>
                            </div>
                        </div>
                    `).join('')}
                </div>
            `).join('');
    };
});