// static/js/progressive-image.js
class ImageLoader {
    static async loadProgressively(file, previewElement) {
        // Create low quality preview
        const lowQualityUrl = await this.createLowQualityPreview(file);
        previewElement.src = lowQualityUrl;
        previewElement.classList.add('loading');

        // Load full quality image
        const fullQualityUrl = URL.createObjectURL(file);
        const img = new Image();
        img.onload = () => {
            previewElement.src = fullQualityUrl;
            previewElement.classList.remove('loading');
        };
        img.src = fullQualityUrl;
    }

    static async createLowQualityPreview(file) {
        return new Promise((resolve) => {
            const reader = new FileReader();
            reader.onload = (e) => {
                const img = new Image();
                img.onload = () => {
                    const canvas = document.createElement('canvas');
                    canvas.width = img.width * 0.1;
                    canvas.height = img.height * 0.1;
                    const ctx = canvas.getContext('2d');
                    ctx.drawImage(img, 0, 0, canvas.width, canvas.height);
                    resolve(canvas.toDataURL('image/jpeg', 0.1));
                };
                img.src = e.target.result;
            };
            reader.readAsDataURL(file);
        });
    }
}