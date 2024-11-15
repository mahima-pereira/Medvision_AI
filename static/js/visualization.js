// static/js/visualization.js
class AdvancedVisualization {
    constructor(canvas) {
        this.canvas = canvas;
        this.ctx = canvas.getContext('2d');
        this.canvas.width = 512;
        this.canvas.height = 512;
    }

    drawHeatmap(predictions) {
        const width = this.canvas.width;
        const height = this.canvas.height;
        
        // Clear canvas
        this.ctx.clearRect(0, 0, width, height);
        
        // Create heatmap data
        const heatmapData = this.generateHeatmapData(predictions, width, height);
        
        // Draw heatmap
        const imageData = this.ctx.createImageData(width, height);
        
        for (let i = 0; i < heatmapData.length; i++) {
            const value = heatmapData[i];
            const idx = i * 4;
            
            // Convert value to color (red for high probability)
            imageData.data[idx] = Math.floor(value * 255);     // R
            imageData.data[idx + 1] = Math.floor(value * 70);  // G
            imageData.data[idx + 2] = Math.floor(value * 70);  // B
            imageData.data[idx + 3] = Math.floor(value * 255); // A
        }
        
        this.ctx.putImageData(imageData, 0, 0);
    }

    generateHeatmapData(predictions, width, height) {
        const heatmapData = new Array(width * height).fill(0);
        
        predictions.forEach(prediction => {
            const intensity = prediction.probability / 100;
            // Generate multiple points for each prediction
            const numPoints = Math.floor(intensity * 10);
            
            for (let i = 0; i < numPoints; i++) {
                const centerX = Math.floor((0.2 + Math.random() * 0.6) * width);
                const centerY = Math.floor((0.2 + Math.random() * 0.6) * height);
                const radius = Math.floor(width * 0.15);
                
                // Generate Gaussian distribution around center
                for (let x = -radius; x < radius; x++) {
                    for (let y = -radius; y < radius; y++) {
                        const px = centerX + x;
                        const py = centerY + y;
                        
                        if (px >= 0 && px < width && py >= 0 && py < height) {
                            const distance = Math.sqrt(x * x + y * y);
                            const value = intensity * Math.exp(-(distance * distance) / (2 * radius * radius));
                            const idx = py * width + px;
                            heatmapData[idx] = Math.max(heatmapData[idx], value);
                        }
                    }
                }
            }
        });
        
        return heatmapData;
    }
}