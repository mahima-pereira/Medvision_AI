# app.py
import os
import logging
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'  # Suppress TF logging
os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'  # Disable oneDNN

from flask import Flask, request, render_template, jsonify
from werkzeug.utils import secure_filename
from utils import AdvancedXRayModel, XRayModel, MRIModel, detect_scan_type
from PIL import Image
from flask_socketio import SocketIO, emit
from flask_swagger_ui import get_swaggerui_blueprint

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0

socketio = SocketIO(app)

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

SWAGGER_URL = '/api/docs'
API_URL = '/static/swagger.json'

swaggerui_blueprint = get_swaggerui_blueprint(
    SWAGGER_URL,
    API_URL,
    config={'app_name': "Medical Imaging API"}
)
app.register_blueprint(swaggerui_blueprint, url_prefix=SWAGGER_URL)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/predict/xray', methods=['POST'])
def predict_xray():
    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400
    
    file = request.files['file']
    if not file or not allowed_file(file.filename):
        return jsonify({'error': 'Invalid file type'}), 400
    
    try:
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        with Image.open(filepath) as image:
            image = image.convert('RGB')
            predictions = xray_model.predict(image)
            
            # Filter significant findings
            significant_findings = [p for p in predictions if p['probability'] > 10]
            
            # Get region analysis
            advanced_model = AdvancedXRayModel()
            regions = advanced_model.get_region_analysis(image)
            
            response = {
                'success': True,
                'findings': significant_findings,
                'summary': {
                    'normal': len(significant_findings) == 0,
                    'conditions_detected': len(significant_findings),
                    'primary_concern': significant_findings[0] if significant_findings else None
                },
                'regions': regions
            }
            
        os.remove(filepath)
        return jsonify(response)
    except Exception as e:
        logging.error(f"Error in predict_xray: {str(e)}")
        return jsonify({'error': 'Error analyzing image'}), 500

@app.route('/predict/mri', methods=['POST'])
def predict_mri():
    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400
    
    file = request.files['file']
    if not file or not allowed_file(file.filename):
        return jsonify({'error': 'Invalid file type'}), 400
    
    try:
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        with Image.open(filepath) as image:
            image = image.convert('RGB')
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
            
        os.remove(filepath)
        return jsonify(response)
    except Exception as e:
        logging.error(f"Error in predict_mri: {str(e)}")
        return jsonify({'error': 'Error analyzing image'}), 500

@app.route('/detect-scan-type', methods=['POST'])
def detect_scan_type_route():
    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400
    
    file = request.files['file']
    if not file or not allowed_file(file.filename):
        return jsonify({'error': 'Invalid file type'}), 400
    
    try:
        # Save file temporarily for debugging
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        # Process image
        with Image.open(filepath) as image:
            image = image.convert('RGB')
            result = detect_scan_type(image)
            
        # Cleanup
        os.remove(filepath)
        return jsonify(result)
    except Exception as e:
        logging.error(f"Error processing file {file.filename}: {str(e)}")
        return jsonify({'error': 'Error analyzing image'}), 500

@socketio.on('analysis_progress')
def handle_progress(data):
    """Emit analysis progress updates"""
    emit('progress_update', {
        'stage': data['stage'],
        'percentage': data['percentage']
    })

if __name__ == '__main__':
    socketio.run(app, debug=True, port=5000, host='0.0.0.0')