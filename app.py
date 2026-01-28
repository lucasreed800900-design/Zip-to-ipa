from flask import Flask, request, render_template_string, send_file, jsonify, flash, redirect, url_for
import os
import shutil
import zipfile
import json
from werkzeug.utils import secure_filename
import tempfile

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'supersecretkey')

UPLOAD_FOLDER = tempfile.gettempdir()
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
ALLOWED_EXTENSIONS = {'zip'}

# Xcode project markers
XCODE_MARKERS = {
    '.xcodeproj': 'Xcode Project Bundle',
    '.pbxproj': 'Xcode Project File',
    '.xcworkspace': 'Xcode Workspace',
    'Info.plist': 'iOS App Configuration',
    '.xcassets': 'Asset Catalog',
    '.storyboard': 'Interface Builder File',
    '.xib': 'Interface Builder File',
    'Podfile': 'CocoaPods Dependency',
    'Cartfile': 'Carthage Dependency',
}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def detect_files_in_zip(zip_path):
    """Extract and list all files/folders in a ZIP file."""
    files = []
    directories = set()
    
    try:
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            for name in zip_ref.namelist():
                files.append(name)
                if '/' in name:
                    dir_path = '/'.join(name.split('/')[:-1])
                    directories.add(dir_path)
    except Exception as e:
        raise Exception(f"Error reading ZIP file: {str(e)}")
    
    return {'files': files, 'directories': sorted(list(directories))}

def detect_xcode_files(zip_path):
    """Detect Xcode project files and folders in a ZIP."""
    detected = {
        'has_xcode_project': False,
        'xcode_files': [],
        'validation_status': 'Not an Xcode project',
        'details': {}
    }
    
    try:
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            for name in zip_ref.namelist():
                name_lower = name.lower()
                
                for marker, description in XCODE_MARKERS.items():
                    if marker.lower() in name_lower:
                        detected['has_xcode_project'] = True
                        detected['xcode_files'].append({
                            'path': name,
                            'type': description
                        })
                        if marker not in detected['details']:
                            detected['details'][marker] = []
                        detected['details'][marker].append(name)
                        break
    except Exception as e:
        raise Exception(f"Error detecting Xcode files: {str(e)}")
    
    if detected['has_xcode_project']:
        detected['validation_status'] = 'Valid Xcode project detected'
    
    return detected

def convert_zip_to_ipa(input_path, output_path):
    """Convert ZIP to IPA file."""
    shutil.copyfile(input_path, output_path)

# HTML Template
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>Zip to IPA Converter</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: #f5f5f5; }
        .container { max-width: 800px; margin: 50px auto; padding: 20px; }
        .card { background: white; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); padding: 30px; }
        h1 { color: #333; margin-bottom: 10px; }
        .subtitle { color: #666; margin-bottom: 30px; }
        .upload-area { border: 2px dashed #007AFF; border-radius: 8px; padding: 40px; text-align: center; cursor: pointer; transition: all 0.3s; }
        .upload-area:hover { background: #f0f8ff; border-color: #0051d5; }
        .upload-area.dragover { background: #e3f2fd; border-color: #0051d5; }
        input[type="file"] { display: none; }
        .btn { background: #007AFF; color: white; padding: 12px 30px; border: none; border-radius: 6px; cursor: pointer; font-size: 16px; transition: 0.3s; }
        .btn:hover { background: #0051d5; }
        .result { margin-top: 20px; padding: 20px; border-radius: 6px; display: none; }
        .result.success { background: #d4edda; color: #155724; border: 1px solid #c3e6cb; }
        .result.error { background: #f8d7da; color: #721c24; border: 1px solid #f5c6cb; }
        .file-info { background: #f9f9f9; padding: 15px; border-radius: 6px; margin-top: 15px; }
        .file-info h3 { margin: 10px 0 5px 0; color: #333; }
        .xcode-status { padding: 10px; border-radius: 4px; margin-top: 10px; }
        .xcode-status.found { background: #c8e6c9; color: #2e7d32; }
        .xcode-status.notfound { background: #fff3cd; color: #856404; }
        .details-list { font-size: 14px; color: #666; margin-top: 10px; }
        .details-list li { margin: 5px 0; }
    </style>
</head>
<body>
    <div class="container">
        <div class="card">
            <h1>📱 Zip to IPA Converter</h1>
            <p class="subtitle">Convert your Xcode projects to IPA format with file detection</p>
            
            <form id="uploadForm" enctype="multipart/form-data">
                <div class="upload-area" id="uploadArea" onclick="document.getElementById('fileInput').click()">
                    <p>📁 Click to upload or drag & drop your ZIP file here</p>
                    <p style="font-size: 12px; color: #999; margin-top: 10px;">Only ZIP files are accepted</p>
                </div>
                <input type="file" id="fileInput" name="file" accept=".zip" required>
                <button type="submit" class="btn" style="width: 100%; margin-top: 20px;">Convert to IPA</button>
            </form>
            
            <div id="result" class="result"></div>
        </div>
    </div>

    <script>
        const uploadArea = document.getElementById('uploadArea');
        const fileInput = document.getElementById('fileInput');
        const uploadForm = document.getElementById('uploadForm');
        const resultDiv = document.getElementById('result');

        // Drag and drop
        uploadArea.addEventListener('dragover', (e) => {
            e.preventDefault();
            uploadArea.classList.add('dragover');
        });
        uploadArea.addEventListener('dragleave', () => uploadArea.classList.remove('dragover'));
        uploadArea.addEventListener('drop', (e) => {
            e.preventDefault();
            uploadArea.classList.remove('dragover');
            fileInput.files = e.dataTransfer.files;
        });

        // File upload
        uploadForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const formData = new FormData(uploadForm);
            
            resultDiv.style.display = 'block';
            resultDiv.innerHTML = '<p>Processing...</p>';
            
            try {
                const response = await fetch('/api/convert', {
                    method: 'POST',
                    body: formData
                });
                
                const data = await response.json();
                
                if (data.success) {
                    let html = `<h3>✓ Conversion Successful!</h3>`;
                    html += `<div class="file-info">
                        <p><strong>Files detected:</strong> ${data.file_count}</p>
                        <p><strong>Directories detected:</strong> ${data.directory_count}</p>
                        <h3>Xcode Project Detection</h3>
                        <div class="xcode-status ${data.xcode_detection.has_xcode_project ? 'found' : 'notfound'}">
                            ${data.xcode_detection.has_xcode_project ? '✓ Xcode project files detected!' : '⚠ No Xcode project files found'}
                        </div>`;
                    
                    if (Object.keys(data.xcode_detection.details).length > 0) {
                        html += `<div class="details-list"><strong>Files Found:</strong><ul>`;
                        for (const [type, files] of Object.entries(data.xcode_detection.details)) {
                            html += `<li><strong>${type}:</strong> ${files.length} file(s)</li>`;
                        }
                        html += `</ul></div>`;
                    }
                    
                    html += `</div><p style="margin-top: 20px;"><a href="${data.download_url}" class="btn" style="display: inline-block; text-decoration: none;">⬇️ Download IPA</a></p>`;
                    resultDiv.className = 'result success';
                    resultDiv.innerHTML = html;
                } else {
                    resultDiv.className = 'result error';
                    resultDiv.innerHTML = `<h3>✗ Conversion Failed</h3><p>${data.message}</p>`;
                }
            } catch (error) {
                resultDiv.className = 'result error';
                resultDiv.innerHTML = `<h3>✗ Error</h3><p>${error.message}</p>`;
            }
        });
    </script>
</body>
</html>
'''

@app.route('/', methods=['GET'])
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/api/detect', methods=['POST'])
def detect_files():
    """API endpoint to detect files in uploaded ZIP without conversion."""
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    if file.filename == '' or not allowed_file(file.filename):
        return jsonify({'error': 'Invalid file'}), 400
    
    try:
        input_path = os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(file.filename))
        file.save(input_path)
        
        file_info = detect_files_in_zip(input_path)
        xcode_info = detect_xcode_files(input_path)
        
        os.remove(input_path)
        
        return jsonify({
            'files': file_info['files'],
            'directories': file_info['directories'],
            'xcode_detection': xcode_info
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/convert', methods=['POST'])
def convert():
    """API endpoint to convert ZIP to IPA."""
    if 'file' not in request.files:
        return jsonify({'success': False, 'message': 'No file provided'}), 400
    
    file = request.files['file']
    if file.filename == '' or not allowed_file(file.filename):
        return jsonify({'success': False, 'message': 'Invalid file. Only ZIP files allowed.'}), 400
    
    try:
        filename = secure_filename(file.filename)
        input_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(input_path)
        
        file_info = detect_files_in_zip(input_path)
        xcode_info = detect_xcode_files(input_path)
        
        output_filename = filename.rsplit('.', 1)[0] + '.ipa'
        output_path = os.path.join(app.config['UPLOAD_FOLDER'], output_filename)
        
        convert_zip_to_ipa(input_path, output_path)
        
        os.remove(input_path)
        
        return jsonify({
            'success': True,
            'message': 'Conversion successful',
            'file_count': len(file_info['files']),
            'directory_count': len(file_info['directories']),
            'xcode_detection': xcode_info,
            'download_url': f'/download/{output_filename}'
        })
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500

@app.route('/download/<filename>', methods=['GET'])
def download(filename):
    """Download converted IPA file."""
    try:
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(filename))
        if os.path.exists(file_path):
            return send_file(file_path, as_attachment=True, download_name=filename)
        return jsonify({'error': 'File not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
            flash('Invalid file type. Only ZIP files are allowed.')
            return redirect(request.url)
    return render_template_string('''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Zip to IPA Converter</title>
    </head>
    <body>
        <h1>Convert ZIP to IPA</h1>
        {% with messages = get_flashed_messages() %}
            {% if messages %}
                <ul>
                {% for message in messages %}
                    <li>{{ message }}</li>
                {% endfor %}
                </ul>
            {% endif %}
        {% endwith %}
        <form method="post" enctype="multipart/form-data">
            <input type="file" name="file" accept=".zip">
            <input type="submit" value="Convert">
        </form>
    </body>
    </html>
    ''')

@app.route('/api/convert', methods=['POST'])
def api_convert():
    if 'file' not in request.files:
        return {'error': 'No file part'}, 400
    file = request.files['file']
    if file.filename == '':
        return {'error': 'No selected file'}, 400
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        input_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(input_path)
        output_filename = filename.rsplit('.', 1)[0] + '.ipa'
        output_path = os.path.join(app.config['UPLOAD_FOLDER'], output_filename)
        try:
            convert_zip_to_ipa(input_path, output_path)
            return send_file(output_path, as_attachment=True, download_name=output_filename)
        except Exception as e:
            return {'error': str(e)}, 500
        finally:
            # Clean up
            if os.path.exists(input_path):
                os.remove(input_path)
            if os.path.exists(output_path):
                os.remove(output_path)
    else:
        return {'error': 'Invalid file type. Only ZIP files are allowed.'}, 400

if __name__ == '__main__':
    app.run(debug=os.environ.get('DEBUG', 'False').lower() == 'true', host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))