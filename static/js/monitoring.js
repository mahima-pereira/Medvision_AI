// static/js/monitoring.js
class MetricsDisplay {
    constructor() {
        this.metricsContainer = document.getElementById('processing-metrics');
        this.progressBar = document.querySelector('.progress-value');
        this.progressText = document.getElementById('progress-text');
        this.startTime = Date.now();
        this.updateMetrics();
        // Show metrics tab by default
        document.querySelector('[data-tab="metrics"]').click();
    }

    updateMetrics() {
        let progress = 0;
        const updateInterval = setInterval(() => {
            progress += 1;
            const elapsedTime = (Date.now() - this.startTime) / 1000;
            
            this.metricsContainer.innerHTML = `
                <div class="metric-item">
                    <span>Processing Time:</span>
                    <span>${elapsedTime.toFixed(1)}s</span>
                </div>
                <div class="metric-item">
                    <span>Analysis Coverage:</span>
                    <span>${progress}%</span>
                </div>
                <div class="metric-item">
                    <span>Scan Quality:</span>
                    <span>${this.getScanQuality(progress)}%</span>
                </div>
            `;

            this.progressBar.style.width = `${progress}%`;
            this.progressText.textContent = `${progress}%`;

            if (progress >= 100) {
                clearInterval(updateInterval);
            }
        }, 50);
    }

    getScanQuality(progress) {
        // Simulate scan quality assessment
        return Math.min(95, Math.floor(85 + (progress / 10)));
    }
}