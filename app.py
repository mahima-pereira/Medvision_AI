# app.py
import os
import logging
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'  # Suppress TF logging
os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'  # Disable oneDNN

from flask import Flask, request, render_template, jsonify
from werkzeug.utils import secure_filename
from utils import XRayModel, MRIModel
from PIL import Image

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'dcm'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Ensure uploads directory exists
os.makedirs('uploads', exist_ok=True)

# Initialize models with error handling
try:
    xray_model = XRayModel()
    mri_model = MRIModel()
except Exception as e:
    print(f"Error initializing models: {str(e)}")
    raise

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/predict/xray', methods=['POST'])
def predict_xray():
    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400
    
    file = request.files['file']
    if file and allowed_file(file.filename):
        try:
            image = Image.open(file.stream).convert('RGB')
            predictions = xray_model.predict(image)
            
            # Filter significant findings
            significant_findings = [p for p in predictions if p['probability'] > 10]
            
            response = {
                'success': True,
                'findings': significant_findings,
                'summary': {
                    'normal': len(significant_findings) == 0,
                    'conditions_detected': len(significant_findings),
                    'primary_concern': significant_findings[0] if significant_findings else None
                }
            }
            print("XRay response:", response)  # Debug print
            return jsonify(response)
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    return jsonify({'error': 'Invalid file type'}), 400

@app.route('/predict/mri', methods=['POST'])
def predict_mri():
    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400
    
    file = request.files['file']
    if file and allowed_file(file.filename):
        try:
            image = Image.open(file.stream).convert('RGB')
            predictions = mri_model.predict(image)
            
            primary_condition = max(predictions, key=lambda x: x['probability'])
            
            response = {
                'success': True,
                'findings': predictions,
                'summary': {
                    'primary_diagnosis': primary_condition['condition'],
                    'confidence': primary_condition['severity'],
                    'probability': primary_condition['probability']
                }
            }
            print("MRI response:", response)  # Debug print
            return jsonify(response)
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    return jsonify({'error': 'Invalid file type'}), 400

if __name__ == '__main__':
    app.run(debug=True, port=5000, host='0.0.0.0')