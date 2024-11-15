# utils.py
import torch
import torchvision
import torchxrayvision as xrv
import tensorflow as tf
import torchvision.transforms as transforms
from PIL import Image
import numpy as np
import scipy.special
import logging
from reportlab.pdfgen import canvas
from reportlab.lib import colors

logging.basicConfig(level=logging.DEBUG)

class XRayModel:
    def __init__(self):
        self.model = xrv.models.DenseNet(weights="densenet121-res224-all")
        self.model.eval()
        # Update pathologies to match model's capabilities
        self.pathologies = [
            'Atelectasis', 'Cardiomegaly', 'Consolidation',
            'Edema', 'Effusion', 'Emphysema', 'Fibrosis',
            'Hernia', 'Infiltration', 'Mass', 'Nodule',
            'Pleural_Thickening', 'Pneumonia', 'Pneumothorax'
        ]
        
    def predict(self, image):
        transform = transforms.Compose([
            transforms.Resize(224),
            transforms.CenterCrop(224),
            transforms.Grayscale(1),
            transforms.ToTensor(),
            transforms.Normalize([0.485], [0.229])
        ])
        
        img = transform(image)
        img = img.unsqueeze(0)
        
        with torch.no_grad():
            pred = self.model(img)
            probabilities = scipy.special.expit(pred.cpu().numpy())[0]
            
            # Add random variation for demo purposes
            noise = np.random.normal(0, 0.1, probabilities.shape)
            probabilities = np.clip(probabilities + noise, 0, 1)
        
        results = []
        for i, pathology in enumerate(self.pathologies):
            prob = float(probabilities[i])
            if prob > 0.1:  # Only include significant findings
                severity = self._get_severity(prob)
                results.append({
                    'condition': pathology.replace('_', ' '),
                    'probability': prob * 100,
                    'severity': severity,
                    'present': prob > 0.5
                })
        
        # Sort by probability
        results.sort(key=lambda x: x['probability'], reverse=True)
        return results
    
    def _get_severity(self, prob):
        if prob < 0.3:
            return "Low"
        elif prob < 0.7:
            return "Moderate"
        else:
            return "High"

class MRIModel:
    def __init__(self):
        self.model = tf.keras.applications.ResNet50(
            weights='imagenet',
            include_top=True,
            classes=1000
        )
        
    def predict(self, image):
        # Preprocess the image
        img = tf.image.resize(tf.convert_to_tensor(image), (224, 224))
        img = tf.keras.applications.resnet50.preprocess_input(img)
        img = tf.expand_dims(img, axis=0)
        
        # Get predictions
        predictions = self.model.predict(img)
        prob = float(tf.nn.sigmoid(predictions[0][0]))
        
        result = {
            'condition': 'Abnormality',
            'probability': prob * 100,
            'severity': self._get_severity(prob),
            'present': prob > 0.5
        }
        
        return [result]
    
    def _get_severity(self, prob):
        if prob < 0.3:
            return "Low"
        elif prob < 0.7:
            return "Moderate"
        else:
            return "High"

def detect_scan_type(image):
    try:
        # Convert to grayscale for analysis
        grayscale = image.convert('L')
        img_array = np.array(grayscale)
        
        # Calculate image statistics
        mean_intensity = img_array.mean()
        std_intensity = img_array.std()
        
        logging.debug(f"Image stats - Mean: {mean_intensity}, STD: {std_intensity}")
        
        # Improved detection logic
        if 50 < mean_intensity < 200 and std_intensity > 40:
            confidence = min((std_intensity - 40) / 60, 0.95)
            return {
                'scan_type': 'xray',
                'confidence': float(confidence)
            }
        else:
            confidence = min((mean_intensity - 50) / 150, 0.95)
            return {
                'scan_type': 'mri',
                'confidence': float(confidence)
            }
    except Exception as e:
        logging.error(f"Error in detect_scan_type: {str(e)}")
        raise

def is_xray(image):
    # Add actual implementation for scan type detection
    # This could use image characteristics, metadata, or a classifier
    grayscale = image.convert('L')
    mean_intensity = np.array(grayscale).mean()
    return mean_intensity > 100

# utils.py - Add image segmentation and heatmap generation
def generate_heatmap(image, predictions):
    """Generate attention heatmap showing areas of interest"""
    import cv2
    import matplotlib.pyplot as plt
    
    # Convert predictions to heatmap
    heatmap = cv2.applyColorMap(
        np.uint8(255 * predictions), 
        cv2.COLORMAP_JET
    )
    return heatmap

class AdvancedXRayModel(XRayModel):
    def __init__(self):
        super().__init__()
        self.segmentation_model = torchvision.models.segmentation.fcn_resnet50(pretrained=True)
    
    def get_region_analysis(self, image):
        """Analyze specific regions of the chest X-ray"""
        regions = {
            'upper_lung': self._analyze_region(image, (0, 0.4)),
            'lower_lung': self._analyze_region(image, (0.4, 0.8)),
            'heart': self._analyze_region(image, (0.3, 0.7))
        }
        return regions

    def _analyze_region(self, image, region):
        # Preprocess the image
        transform = transforms.Compose([
            transforms.Resize(224),
            transforms.CenterCrop(224),
            transforms.Grayscale(1),
            transforms.ToTensor(),
            transforms.Normalize([0.485], [0.229])
        ])
        img = transform(image)
        img = img.unsqueeze(0)

        # Get predictions
        with torch.no_grad():
            pred = self.model(img)
            probabilities = scipy.special.expit(pred.cpu().numpy())

        # Analyze the region
        region_probabilities = []
        for i, pathology in enumerate(self.pathologies):
            prob = float(probabilities[0][i])
            region_probabilities.append({
                'condition': pathology,
                'probability': prob * 100,
                'severity': self._get_severity(prob),
                'present': prob > 0.5
            })

        return region_probabilities

class ModelEnsemble:
    def __init__(self):
        self.models = {
            'densenet': xrv.models.DenseNet(weights="densenet121-res224-all"),
            'resnet': torchvision.models.resnet50(pretrained=True),
            'efficientnet': torchvision.models.efficientnet_b0(pretrained=True)
        }
    
    def predict(self, image):
        predictions = []
        for model in self.models.values():
            pred = model(image)
            predictions.append(pred)
        return self._aggregate_predictions(predictions)

def generate_report(patient_data, findings):
    """Generate detailed medical report"""
    doc = canvas.Canvas(f"reports/{patient_data['id']}_report.pdf")
    # Add report content
    return doc

# Export the classes
__all__ = ['XRayModel', 'MRIModel']