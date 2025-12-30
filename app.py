from flask import Flask, request, redirect, url_for, render_template, flash, send_from_directory, abort
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from PIL import Image
import os
from datetime import datetime, timedelta
import uuid
import configparser
from dog_app.db import get_db

# Load configuration
config = configparser.ConfigParser()
config_file_local = 'dog_app.conf'
config_file_system = '/etc/dog_app.conf'

if os.path.exists(config_file_local):
    config.read(config_file_local)
elif os.path.exists(config_file_system):
    config.read(config_file_system)
else:
    raise FileNotFoundError("Configuration file not found at dog_app.conf or /etc/dog_app.conf")

# Extract configuration
BASE_DATA_PATH = config['General']['base_data_path']
DATABASE_TYPE = config['Database']['type']
DATABASE_CONFIG = {}
if DATABASE_TYPE == 'sqlite':
    DATABASE_CONFIG['sqlite'] = {'database': os.path.join(BASE_DATA_PATH, config['Database']['sqlite_database'])}
elif DATABASE_TYPE == 'mysql':
    DATABASE_CONFIG['mysql'] = {
        'host': config['Database']['mysql_host'],
        'user': config['Database']['mysql_user'],
        'password': config['Database']['mysql_password'],
        'database': config['Database']['mysql_database']
    }
elif DATABASE_TYPE == 'postgresql':
    DATABASE_CONFIG['postgresql'] = {
        'host': config['Database']['postgresql_host'],
        'user': config['Database']['postgresql_user'],
        'password': config['Database']['postgresql_password'],
        'database': config['Database']['postgresql_database']
    }
else:
    raise ValueError(f"Unsupported database type: {DATABASE_TYPE}")

app = Flask(__name__)
app.secret_key = config.get('General', 'secret_key', fallback='super_secret_key')  # Fallback for development
app.config['DATABASE_TYPE'] = DATABASE_TYPE
app.config['DATABASE_CONFIG'] = DATABASE_CONFIG

# File upload config
UPLOAD_FOLDER = os.path.join(BASE_DATA_PATH, 'Uploads')
DOG_PHOTOS_FOLDER = os.path.join(UPLOAD_FOLDER, 'dog_photos')
MEDICAL_RECORDS_FOLDER = os.path.join(UPLOAD_FOLDER, 'medical_records')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['DOG_PHOTOS_FOLDER'] = DOG_PHOTOS_FOLDER
app.config['MEDICAL_RECORDS_FOLDER'] = MEDICAL_RECORDS_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB

ALLOWED_IMAGE_EXTENSIONS = {'png', 'jpg', 'jpeg'}
ALLOWED_DOCUMENT_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg'}

# Ensure folders exist
os.makedirs(DOG_PHOTOS_FOLDER, exist_ok=True)
os.makedirs(MEDICAL_RECORDS_FOLDER, exist_ok=True)

# Flask-Login setup
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

class User(UserMixin):
    def __init__(self, id, username, role, full_name, email, is_active):
        self.id = id
        self.username = username
        self.role = role
        self.full_name = full_name
        self.email = email
        self._is_active = is_active

    @property
    def is_active(self):
        return self._is_active

@login_manager.user_loader
def load_user(user_id):
    db = get_db()
    user = db.fetch_one('SELECT * FROM users WHERE id = ?', (user_id,))
    if user:
        return User(user['id'], user['username'], user['role'], user['full_name'], user['email'], user['is_active'])
    return None

# Initialize database within app context
with app.app_context():
    db = get_db()
    db.init_db()

# Helper functions
def allowed_file(filename, allowed_extensions):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions

def calculate_age(birthdate, deathdate=None):
    if not birthdate:
        return 'Unknown'
    birth = datetime.strptime(birthdate, '%Y-%m-%d')
    end_date = datetime.strptime(deathdate, '%Y-%m-%d') if deathdate else datetime.now()
    age = end_date - birth
    years = age.days // 365
    months = (age.days % 365) // 30
    days = (age.days % 365) % 30
    return f'{years} years, {months} months, {days} days'

def get_upcoming_vaccinations():
    db = get_db()
    thirty_days = (datetime.now() + timedelta(days=30)).date()
    today = datetime.now().date()
    vaccinations = db.fetch_all('SELECT * FROM vaccinations WHERE next_due_date <= ? AND next_due_date >= ?', (thirty_days, today))
    return vaccinations

# Routes
@app.route('/')
@login_required
def index():
    db = get_db()
    dogs = db.fetch_all('SELECT * FROM dogs')
    photos = db.fetch_all('SELECT * FROM dog_photos')
    dogs = [dict(dog) for dog in dogs]
    for dog in dogs:
        dog['age'] = calculate_age(dog['birthdate'], dog['deathdate'])
    alerts = get_upcoming_vaccinations()
    return render_template('index.html', dogs=dogs, alerts=alerts, photos=photos)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        db = get_db()
        user = db.fetch_one('SELECT * FROM users WHERE username = ?', (username,))
        if user and check_password_hash(user['password_hash'], password) and user['is_active']:
            user_obj = User(user['id'], user['username'], user['role'], user['full_name'], user['email'], user['is_active'])
            login_user(user_obj)
            return redirect(url_for('index'))
        flash('Invalid username or password')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
@login_required
def register():
    if current_user.role != 'admin':
        abort(403)
    if request.method == 'POST':
        username = request.form['username']
        password = generate_password_hash(request.form['password'])
        role = request.form['role']
        full_name = request.form.get('full_name')
        email = request.form.get('email')
        db = get_db()
        try:
            db.execute('INSERT INTO users (username, password_hash, role, full_name, email) VALUES (?, ?, ?, ?, ?)',
                       (username, password, role, full_name, email))
            flash('User registered successfully')
        except Exception as e:
            if 'UNIQUE constraint' in str(e):
                flash('Username already exists')
            else:
                flash('Error registering user')
        return redirect(url_for('manage_users'))
    return render_template('register.html')

@app.route('/change_password', methods=['GET', 'POST'])
@login_required
def change_password():
    if request.method == 'POST':
        old_password = request.form['old_password']
        new_password = request.form['new_password']
        db = get_db()
        user = db.fetch_one('SELECT * FROM users WHERE id = ?', (current_user.id,))
        if check_password_hash(user['password_hash'], old_password):
            hashed = generate_password_hash(new_password)
            db.execute('UPDATE users SET password_hash = ? WHERE id = ?', (hashed, current_user.id))
            flash('Password changed successfully')
        else:
            flash('Incorrect old password')
        return redirect(url_for('index'))
    return render_template('change_password.html')

@app.route('/manage_users', methods=['GET', 'POST'])
@login_required
def manage_users():
    if current_user.role != 'admin':
        abort(403)
    db = get_db()
    users = db.fetch_all('SELECT * FROM users')
    if request.method == 'POST':
        user_id = request.form['user_id']
        action = request.form['action']
        if action == 'edit':
            username = request.form['username']
            role = request.form['role']
            full_name = request.form.get('full_name')
            email = request.form.get('email')
            is_active = 1 if request.form.get('is_active') == 'on' else 0
            db.execute('UPDATE users SET username = ?, role = ?, full_name = ?, email = ?, is_active = ? WHERE id = ?',
                       (username, role, full_name, email, is_active, user_id))
            flash('User updated successfully')
        elif action == 'delete' and int(user_id) != current_user.id:
            db.execute('DELETE FROM users WHERE id = ?', (user_id,))
            flash('User deleted successfully')
        else:
            flash('Cannot delete own account')
        users = db.fetch_all('SELECT * FROM users')
    return render_template('manage_users.html', users=users)

@app.route('/dog/<int:dog_id>')
@login_required
def dog_detail(dog_id):
    db = get_db()
    dog = db.fetch_one('SELECT * FROM dogs WHERE id = ?', (dog_id,))
    if not dog:
        abort(404)
    photos = db.fetch_all('SELECT * FROM dog_photos WHERE dog_id = ?', (dog_id,))
    medical_records = db.fetch_all('SELECT * FROM medical_records WHERE dog_id = ?', (dog_id,))
    vaccinations = db.fetch_all('SELECT * FROM vaccinations WHERE dog_id = ?', (dog_id,))
    dog = dict(dog)
    dog['age'] = calculate_age(dog['birthdate'], dog['deathdate'])
    return render_template('dog_detail.html', dog=dog, photos=photos, medical_records=medical_records, vaccinations=vaccinations)

@app.route('/edit_dog/<int:dog_id>', methods=['GET', 'POST'])
@login_required
def edit_dog(dog_id):
    if current_user.role not in ['admin', 'doctor']:
        abort(403)
    db = get_db()
    dog = db.fetch_one('SELECT * FROM dogs WHERE id = ?', (dog_id,))
    if not dog:
        abort(404)
    photos = db.fetch_all('SELECT * FROM dog_photos WHERE dog_id = ?', (dog_id,))
    medical_records = db.fetch_all('SELECT * FROM medical_records WHERE dog_id = ?', (dog_id,))
    vaccinations = db.fetch_all('SELECT * FROM vaccinations WHERE dog_id = ?', (dog_id,))
    if request.method == 'POST' and 'dog_update' in request.form:
        name = request.form['name']
        breed = request.form.get('breed')
        birthdate = request.form.get('birthdate') or None
        deathdate = request.form.get('deathdate') or None
        status = 'Deceased' if deathdate else 'Living'
        db.execute('UPDATE dogs SET name = ?, breed = ?, birthdate = ?, deathdate = ?, status = ? WHERE id = ?',
                   (name, breed, birthdate, deathdate, status, dog_id))
        flash('Dog updated successfully')
    return render_template('edit_dog.html', dog=dog, photos=photos, medical_records=medical_records, vaccinations=vaccinations)

@app.route('/edit_medical_record/<int:dog_id>/<int:record_id>', methods=['GET', 'POST'])
@login_required
def edit_medical_record(dog_id, record_id):
    if current_user.role not in ['admin', 'doctor']:
        abort(403)
    db = get_db()
    record = db.fetch_one('SELECT * FROM medical_records WHERE id = ? AND dog_id = ?', (record_id, dog_id))
    if not record:
        abort(404)
    if request.method == 'POST':
        description = request.form.get('description')
        category = request.form.get('category')
        record_date = request.form.get('record_date') or datetime.now().date()
        if 'record' in request.files and request.files['record'].filename:
            file = request.files['record']
            if allowed_file(file.filename, ALLOWED_DOCUMENT_EXTENSIONS):
                original_filename = secure_filename(file.filename)
                unique_filename = f"{uuid.uuid4()}_{original_filename}"
                filepath = os.path.join(app.config['MEDICAL_RECORDS_FOLDER'], unique_filename)
                file.save(filepath)
                if os.path.exists(record['filepath']):
                    os.remove(record['filepath'])
                db.execute('UPDATE medical_records SET original_filename = ?, filename = ?, filepath = ?, description = ?, category = ?, record_date = ? WHERE id = ?',
                           (original_filename, unique_filename, filepath, description, category, record_date, record_id))
            else:
                flash('Invalid file format')
                return redirect(url_for('edit_dog', dog_id=dog_id))
        else:
            db.execute('UPDATE medical_records SET description = ?, category = ?, record_date = ? WHERE id = ?',
                       (description, category, record_date, record_id))
        flash('Medical record updated successfully')
        return redirect(url_for('edit_dog', dog_id=dog_id))
    return render_template('edit_medical_record.html', dog_id=dog_id, record=record)

@app.route('/add_dog', methods=['GET', 'POST'])
@login_required
def add_dog():
    if current_user.role not in ['admin', 'doctor']:
        abort(403)
    if request.method == 'POST':
        name = request.form['name']
        breed = request.form.get('breed')
        birthdate = request.form.get('birthdate') or None
        deathdate = request.form.get('deathdate') or None
        status = 'Deceased' if deathdate else 'Living'
        db = get_db()
        db.execute('INSERT INTO dogs (name, breed, birthdate, deathdate, status) VALUES (?, ?, ?, ?, ?)',
                   (name, breed, birthdate, deathdate, status))
        dog_id = db.last_insert_id()
        flash('Dog added successfully')
        return redirect(url_for('index'))
    return render_template('add_dog.html')

@app.route('/upload_photo/<int:dog_id>', methods=['POST'])
@login_required
def upload_photo(dog_id):
    if current_user.role not in ['admin', 'doctor']:
        abort(403)
    if 'photo' not in request.files:
        flash('No file selected')
        return redirect(url_for('edit_dog', dog_id=dog_id))
    file = request.files['photo']
    if file and allowed_file(file.filename, ALLOWED_IMAGE_EXTENSIONS):
        original_filename = secure_filename(file.filename)
        unique_filename = f"{uuid.uuid4()}_{original_filename}"
        filepath = os.path.join(app.config['DOG_PHOTOS_FOLDER'], unique_filename)
        file.save(filepath)
        img = Image.open(filepath)
        img.thumbnail((200, 200))
        thumb_filename = f"thumb_{unique_filename}"
        thumb_filepath = os.path.join(app.config['DOG_PHOTOS_FOLDER'], thumb_filename)
        img.save(thumb_filepath)
        db = get_db()
        is_primary = 0
        existing_photos = db.fetch_one('SELECT COUNT(*) as count FROM dog_photos WHERE dog_id = ?', (dog_id,))['count']
        if existing_photos == 0:
            is_primary = 1
        db.execute('INSERT INTO dog_photos (dog_id, original_filename, filename, filepath, is_primary) VALUES (?, ?, ?, ?, ?)',
                   (dog_id, original_filename, unique_filename, filepath, is_primary))
        flash('Photo uploaded successfully')
    else:
        flash('Invalid file format')
    return redirect(url_for('edit_dog', dog_id=dog_id))

@app.route('/set_primary_photo/<int:dog_id>/<int:photo_id>')
@login_required
def set_primary_photo(dog_id, photo_id):
    if current_user.role not in ['admin', 'doctor']:
        abort(403)
    db = get_db()
    db.execute('UPDATE dog_photos SET is_primary = 0 WHERE dog_id = ?', (dog_id,))
    db.execute('UPDATE dog_photos SET is_primary = 1 WHERE id = ? AND dog_id = ?', (photo_id, dog_id))
    flash('Primary photo set successfully')
    return redirect(url_for('edit_dog', dog_id=dog_id))

@app.route('/delete_photo/<int:dog_id>/<int:photo_id>')
@login_required
def delete_photo(dog_id, photo_id):
    if current_user.role not in ['admin', 'doctor']:
        abort(403)
    db = get_db()
    photo = db.fetch_one('SELECT * FROM dog_photos WHERE id = ? AND dog_id = ?', (photo_id, dog_id))
    if photo:
        os.remove(photo['filepath'])
        thumb_filepath = os.path.join(app.config['DOG_PHOTOS_FOLDER'], f"thumb_{photo['filename']}")
        if os.path.exists(thumb_filepath):
            os.remove(thumb_filepath)
        db.execute('DELETE FROM dog_photos WHERE id = ?', (photo_id,))
        flash('Photo deleted successfully')
    return redirect(url_for('edit_dog', dog_id=dog_id))

@app.route('/Uploads/<path:filename>')
@login_required
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/upload_medical_record/<int:dog_id>', methods=['POST'])
@login_required
def upload_medical_record(dog_id):
    if current_user.role not in ['admin', 'doctor']:
        abort(403)
    if 'record' not in request.files:
        flash('No file selected')
        return redirect(url_for('edit_dog', dog_id=dog_id))
    file = request.files['record']
    if file and allowed_file(file.filename, ALLOWED_DOCUMENT_EXTENSIONS):
        original_filename = secure_filename(file.filename)
        unique_filename = f"{uuid.uuid4()}_{original_filename}"
        filepath = os.path.join(app.config['MEDICAL_RECORDS_FOLDER'], unique_filename)
        file.save(filepath)
        description = request.form.get('description')
        category = request.form.get('category')
        record_date = request.form.get('record_date') or datetime.now().date()
        db = get_db()
        db.execute('INSERT INTO medical_records (dog_id, original_filename, filename, filepath, description, category, record_date) VALUES (?, ?, ?, ?, ?, ?, ?)',
                   (dog_id, original_filename, unique_filename, filepath, description, category, record_date))
        flash('Medical record uploaded successfully')
    else:
        flash('Invalid file format')
    return redirect(url_for('edit_dog', dog_id=dog_id))

@app.route('/delete_medical_record/<int:dog_id>/<int:record_id>')
@login_required
def delete_medical_record(dog_id, record_id):
    if current_user.role not in ['admin', 'doctor']:
        abort(403)
    db = get_db()
    record = db.fetch_one('SELECT * FROM medical_records WHERE id = ? AND dog_id = ?', (record_id, dog_id))
    if record:
        os.remove(record['filepath'])
        db.execute('DELETE FROM medical_records WHERE id = ?', (record_id,))
        flash('Medical record deleted successfully')
    return redirect(url_for('edit_dog', dog_id=dog_id))

@app.route('/add_vaccination/<int:dog_id>', methods=['POST'])
@login_required
def add_vaccination(dog_id):
    if current_user.role not in ['admin', 'doctor']:
        abort(403)
    vaccine_type = request.form['vaccine_type']
    date_administered = request.form['date_administered']
    next_due_date = request.form.get('next_due_date') or None
    notes = request.form.get('notes')
    certificate_id = request.form.get('certificate_id') or None
    db = get_db()
    db.execute('INSERT INTO vaccinations (dog_id, vaccine_type, date_administered, next_due_date, notes, certificate_id) VALUES (?, ?, ?, ?, ?, ?)',
               (dog_id, vaccine_type, date_administered, next_due_date, notes, certificate_id))
    flash('Vaccination added successfully')
    return redirect(url_for('edit_dog', dog_id=dog_id))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5056, debug=True)
