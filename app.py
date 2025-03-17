import os
from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3

from werkzeug.utils import send_from_directory

from heatmap import generate_heatmaps

UPLOAD_FOLDER = 'uploads'
HEATMAP_FOLDER = 'heatmap'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'csv'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS
app = Flask(__name__)
app.secret_key = 'your_secret_key'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['HEATMAP_FOLDER'] = HEATMAP_FOLDER

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(HEATMAP_FOLDER, exist_ok=True)
@app.route('/')
def home():
    return render_template('home.html')

@app.route('/upload', methods=['GET', 'POST'])
def upload_file():
    if 'csv_file' not in request.files or 'image_file' not in request.files:
        flash('No file part')
        return redirect(request.url)

    csv_file = request.files['csv_file']
    image_file = request.files['image_file']

    if csv_file and allowed_file(csv_file.filename) and image_file and allowed_file(image_file.filename):
        csv_path = os.path.join(app.config['UPLOAD_FOLDER'], csv_file.filename)
        image_path = os.path.join(app.config['UPLOAD_FOLDER'], image_file.filename)

        csv_file.save(csv_path)
        image_file.save(image_path)

        try:
            output_files = generate_heatmaps(csv_path, image_path, app.config['HEATMAP_FOLDER'])
        except Exception as e:
            flash(f'Error processing files: {str(e)}')
            return redirect(url_for('index'))

        flash(f"Successfully created {len(output_files)} heatmaps!")
        return render_template('heatmap.html', heatmaps=[os.path.basename(f) for f in output_files])

    else:
        flash('Allowed file types are csv, jpg, jpeg, png')
        return redirect(request.url)

@app.route('/heatmaps/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['HEATMAP_FOLDER'], filename)
@app.route('/heatmap', methods=['GET', 'POST'])
def heatmap():
    if 'username' not in session:
        return redirect(url_for('login'))

    username = session['username']

    # Generate or load heatmap
    heatmap_file = generate_heatmaps(username)

    if not heatmap_file:
        return render_template('dashboard.html', username=username, error='No gaze data available')

    heatmap_url = url_for('static', filename=f'heatmaps/heatmap_user_{username}.png')

    return render_template('dashboard.html', username=username, heatmap_url=heatmap_url)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        username_error = ""
        password_error = ""

        if not username:
            username_error = 'Name is required.'
        if not password:
            password_error = 'Password is required.'

        if username_error or password_error:
            return render_template('login.html',
                                   username_error=username_error,
                                   password_error=password_error,
                                   registration_success='')

        conn = sqlite3.connect('users.db')
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE username = ? AND password = ?', (username,password))
        user = cursor.fetchone()
        conn.close()

        if user:
            session['username'] = user[0]
            session['password'] = user[1]
            flash('Login successful!')
            return redirect(url_for('dashboard', username=username))
        else:
            flash('Login unsuccessful!')

    # GET request goes here
    return render_template('login.html',
                           username_error='',
                           password_error='',
                           registration_success='')
@app.route('/dashboard')
def dashboard():
    username = session.get('username')

    if not username:
        return redirect(url_for('login'))

    # Generate the heatmap and get the relative path
    heatmap_relative_path = generate_heatmaps(username)

    if not heatmap_relative_path:
        flash('No heatmap data found for user.', 'warning')
        heatmap_url = None
    else:
        heatmap_url = url_for('static', filename=f'heatmaps/heatmap_user_{username}.png')

    return render_template('dashboard.html', username=username, heatmap_url=heatmap_url)
@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.')
    return redirect(url_for('home'))
if __name__ == '__main__':
    app.run(debug=True)
