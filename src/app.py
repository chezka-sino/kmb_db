from flask import Flask, render_template, request, jsonify, flash, redirect, url_for
from werkzeug.utils import secure_filename
import os
from datetime import datetime
from database import (add_to_customers, add_pass, add_class, 
                     add_purchases, add_attendances)
from logger import ErrorLogger
from dotenv import load_dotenv
from supabase import create_client, Client

app = Flask(__name__)
app.secret_key = 'your-secret-key-here'  # Change this to a secure secret key

# Configure upload folder
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'csv'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Initialize Supabase and logger
load_dotenv()
url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_SECRET_KEY")
supabase: Client = create_client(url, key)
error_logger = ErrorLogger()

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload/<operation>', methods=['GET', 'POST'])
def upload(operation):
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No file selected')
            return redirect(request.url)
        
        file = request.files['file']
        if file.filename == '':
            flash('No file selected')
            return redirect(request.url)
        
        if file and allowed_file(file.filename):
            try:
                filename = secure_filename(file.filename)
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(filepath)

                if operation == 'customers':
                    last_pull = request.form.get('last_pull')
                    if not last_pull:
                        flash('Last pull date is required')
                        return redirect(request.url)
                    last_pull_date = datetime.strptime(last_pull, '%Y-%m-%d').date()
                    count = add_to_customers(supabase, filepath, last_pull_date)
                    flash(f'{count} customer(s) added successfully')

                elif operation == 'passes':
                    count, duplicates = add_pass(supabase, filepath)
                    message = f'{count} pass(es) added successfully'
                    if duplicates:
                        message += f'. Skipped duplicates: {", ".join(duplicates)}'
                    flash(message)

                elif operation == 'classes':
                    count = add_class(supabase, filepath)
                    flash(f'{count} class(es) added successfully')

                elif operation == 'purchases':
                    count = add_purchases(supabase, filepath)
                    flash(f'{count} purchase(s) added successfully')

                elif operation == 'attendances':
                    count = add_attendances(supabase, filepath)
                    flash(f'{count} attendance record(s) added successfully')

                # Clean up uploaded file
                os.remove(filepath)
                return redirect(url_for('index'))

            except Exception as e:
                error_logger.log_error(f"Upload {operation}", e, {
                    "file": file.filename,
                    "operation": operation
                })
                flash(f'Error: {str(e)}')
                return redirect(request.url)

    return render_template('upload.html', operation=operation)

if __name__ == '__main__':
    # Create upload folder if it doesn't exist
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    app.run(debug=True) 