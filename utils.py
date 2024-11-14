# utils.py
import torch
import torchvision
import torchxrayvision as xrv
import tensorflow as tf
import tensorflow_hub as hub
import torchvision.transforms as transforms
from PIL import Image
import numpy as np
import scipy.special

class XRayModel:
    def __init__(self):
        self.model = xrv.models.DenseNet(weights="densenet121-res224-all")
        self.model.eval()
        self.pathologies = self.model.pathologies
        
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
            probabilities = scipy.special.expit(pred.cpu().numpy())
        
        results = []
        for i, pathology in enumerate(self.pathologies):
            prob = float(probabilities[0][i])
            severity = self._get_severity(prob)
            results.append({
                'condition': pathology,
                'probability': prob * 100,
                'severity': severity,
                'present': prob > 0.5
            })
        
        print("XRayModel predictions:", results)  # Debug print
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
        self.model = hub.load('https://tfhub.dev/google/imagenet/resnet_v2_50/classification/5')
        self.conditions = {
            'tumor': {'index': 1, 'thresholds': {0.7: 'High', 0.4: 'Moderate', 0: 'Low'}},
            'normal': {'index': 0, 'thresholds': {0.7: 'High', 0.4: 'Moderate', 0: 'Low'}}
        }
        
    def predict(self, image):
        img = tf.image.resize(image, (224, 224))
        img = tf.cast(img, tf.float32)
        img = tf.expand_dims(img, 0)
        img = tf.keras.applications.resnet_v2.preprocess_input(img)
        
        predictions = self.model(img)
        probabilities = tf.nn.softmax(predictions).numpy()[0]
        
        results = []
        for condition, params in self.conditions.items():
            prob = float(probabilities[params['index']])
            severity = self._get_severity(prob, params['thresholds'])
            results.append({
                'condition': condition.capitalize(),
                'probability': prob * 100,
                'severity': severity,
                'present': prob > 0.5
            })
        
        print("MRIModel predictions:", results)  # Debug print
        return results
    
    def _get_severity(self, prob, thresholds):
        for threshold, label in thresholds.items():
            if prob >= threshold:
                return label
        return "Low"

# Export the classes
__all__ = ['XRayModel', 'MRIModel']