# Comanche Dogs Application Requirements Definition

## 1. Overview
The Comanche Dogs application is a web-based system for managing dog records, including their details, photos, medical records, and vaccination schedules. It supports multiple user roles with role-based access control and allows flexible configuration for development and production environments. The application is implemented using Flask and supports SQLite, MySQL, or PostgreSQL databases.

### 1.1 Purpose
The application enables users to:
- Manage dog profiles (name, breed, birthdate, deathdate, status).
- Upload and manage photos and medical records for dogs.
- Track vaccination schedules with alerts for upcoming vaccinations.
- Administer user accounts with different access levels (admin, doctor, viewer).
- Operate in both development and production environments with configurable database and file storage settings.

### 1.2 Scope
The system supports:
- Web interface for user interaction.
- Role-based authentication (admin, doctor, viewer).
- File uploads for photos (PNG, JPG, JPEG) and medical records (TXT, PDF, PNG, JPG, JPEG).
- Modular database support (SQLite, MySQL, PostgreSQL).
- Flexible configuration via `dog_app.conf` loaded from the current working directory or `/etc/dog_app.conf`.
- Example configuration template (`dog_app.conf.example`) for easy setup.

## 2. Stakeholders
- **Administrators**: Manage users, dogs, photos, medical records, and vaccinations.
- **Doctors**: Manage dog details, photos, medical records, and vaccinations.
- **Viewers**: View dog details, photos, medical records, and vaccination alerts.
- **Developers/DevOps**: Configure and deploy the application for development or production.

## 3. Functional Requirements

### 3.1 User Management
- **UR1**: The system shall support user registration by administrators via a web interface (`/register`).
  - Fields: username, password, role (admin/doctor/viewer), full name, email.
  - Constraint: Username must be unique.
- **UR2**: The system shall support user login with username and password (`/login`).
  - Default credentials: `admin` / `admin123`.
- **UR3**: The system shall allow users to change their passwords (`/change_password`).
  - Requires current password verification.
- **UR4**: Administrators shall manage users (`/manage_users`):
  - View all users.
  - Edit user details (username, role, full name, email, active status).
  - Delete users (except their own account).
- **UR5**: The system shall enforce role-based access control:
  - Admin: Full access to all features.
  - Doctor: Add/edit/delete dogs, photos, medical records, and vaccinations.
  - Viewer: Read-only access to dog details, photos, medical records, and vaccination alerts.

### 3.2 Dog Management
- **DR1**: The system shall allow admins and doctors to add dogs via a web interface (`/add_dog`).
  - Fields: name (required), breed (optional), birthdate (optional), deathdate (optional).
  - Status: Automatically set to "Deceased" if deathdate is provided, else "Living".
- **DR2**: The system shall allow all users to view dog details (`/dog/<dog_id>`).
  - Display: name, breed, birthdate, deathdate, status, calculated age, photos, medical records, vaccinations.
- **DR3**: The system shall allow admins and doctors to edit dog details (`/edit_dog/<dog_id>`).
  - Fields: name, breed, birthdate, deathdate, status (updated automatically).
- **DR4**: The system shall calculate and display a dog’s age based on birthdate (format: X years, Y months, Z days).

### 3.3 Photo Management
- **PR1**: The system shall allow admins and doctors to upload photos for a dog (`/edit_dog/<dog_id>`).
  - Supported formats: PNG, JPG, JPEG.
  - Maximum file size: 16MB.
  - Generate thumbnails (200x200 pixels).
  - Store photos in `Uploads/dog_photos/` with unique filenames (UUID + original filename).
  - First uploaded photo is automatically set as primary.
- **PR2**: The system shall allow admins and doctors to set a primary photo (`/set_primary_photo/<dog_id>/<photo_id>`).
  - Only one photo per dog is primary, indicated by a checkmark.
- **PR3**: The system shall allow admins and doctors to delete photos (`/delete_photo/<dog_id>/<photo_id>`).
  - Delete both original and thumbnail files.
- **PR4**: The system shall display photos in the dog details view (`/dog/<dog_id>`), with thumbnails and a checkmark for the primary photo.

### 3.4 Medical Records Management
- **MR1**: The system shall allow admins and doctors to upload medical records for a dog (`/edit_dog/<dog_id>`).
  - Supported formats: TXT, PDF, PNG, JPG, JPEG.
  - Maximum file size: 16MB.
  - Fields: description (optional), category (optional), record date (defaults to current date).
  - Store records in `Uploads/medical_records/` with unique filenames (UUID + original filename).
- **MR2**: The system shall allow admins and doctors to edit medical records (`/edit_medical_record/<dog_id>/<record_id>`).
  - Update description, category, record date, or replace the file.
- **MR3**: The system shall allow admins and doctors to delete medical records (`/delete_medical_record/<dog_id>/<record_id>`).
  - Delete the associated file.
- **MR4**: The system shall display medical records in the dog details view (`/dog/<dog_id>`).

### 3.5 Vaccination Management
- **VR1**: The system shall allow admins and doctors to add vaccination records for a dog (`/edit_dog/<dog_id>`).
  - Fields: vaccine type, date administered, next due date (optional), notes (optional), certificate ID (optional).
- **VR2**: The system shall display vaccination records in the dog details view (`/dog/<dog_id>`).
- **VR3**: The system shall display alerts for upcoming vaccinations (due within 30 days) on the homepage (`/`).

### 3.6 Configuration
- **CR1**: The system shall load configuration from `dog_app.conf` in the current working directory or `/etc/dog_app.conf` (production).
  - Format: INI with `[General]` and `[Database]` sections.
  - `[General]`:
    - `base_data_path`: Absolute path to data directory (e.g., `/Users/jramsey/Documents/Code/dogs/grok/dog_app`).
    - `secret_key`: Flask session secret key.
  - `[Database]`:
    - `type`: `sqlite`, `mysql`, or `postgresql`.
    - `sqlite_database`: Database file name (e.g., `database.db`).
    - `mysql_*`: Host, user, password, database for MySQL.
    - `postgresql_*`: Host, user, password, database for PostgreSQL.
- **CR2**: The system shall include a `dog_app.conf.example` file in the `dog_app/` directory as a template for creating `dog_app.conf`.

### 3.7 Database
- **DB1**: The system shall support SQLite, MySQL, and PostgreSQL databases.
- **DB2**: The system shall initialize the database schema automatically on first run.
- **DB3**: The system shall store:
  - Users: id, username, password_hash, role, full_name, email, is_active.
  - Dogs: id, name, breed, birthdate, deathdate, status.
  - Dog photos: id, dog_id, original_filename, filename, filepath, is_primary.
  - Medical records: id, dog_id, original_filename, filename, filepath, description, category, record_date.
  - Vaccinations: id, dog_id, vaccine_type, date_administered, next_due_date, notes, certificate_id.

## 4. Non-Functional Requirements

### 4.1 Performance
- **P1**: The system shall handle up to 100 concurrent users with response times under 2 seconds for page loads.
- **P2**: File uploads (photos, medical records) shall complete within 10 seconds for files up to 16MB.

### 4.2 Security
- **S1**: The system shall use password hashing (PBKDF2, SHA256, or similar) for user passwords.
- **S2**: The system shall enforce role-based access control for all routes.
- **S3**: The system shall use secure session management with a configurable `secret_key`.
- **S4**: The system shall sanitize filenames for uploaded files to prevent directory traversal attacks.
- **S5**: In production, `dog_app.conf` shall have restricted permissions (e.g., 600).

### 4.3 Usability
- **U1**: The web interface shall be intuitive, with clear navigation and feedback (e.g., flash messages for success/errors).
- **U2**: The system shall provide a `dog_app.conf.example` template with comments explaining each configuration field.
- **U3**: The system shall display dog cards on the homepage (`/`) without underlines on linked text (e.g., name, breed, age, status) for improved readability and aesthetics.

### 4.4 Scalability
- **SC1**: The system shall support database scaling (e.g., MySQL/PostgreSQL for larger datasets).
- **SC2**: The system shall support deployment with WSGI servers (e.g., Gunicorn) and reverse proxies (e.g., Nginx).

### 4.5 Maintainability
- **M1**: The code shall be modular, with separate modules for database logic (`db.py`, `db_sqlite.py`, etc.).
- **M2**: The system shall include a `requirements.txt` file listing all dependencies.

### 4.6 Portability
- **PO1**: The system shall run on Linux, macOS, or Windows.
- **PO2**: The system shall support configuration via `dog_app.conf` in the working directory for development or `/etc/dog_app.conf` for production.

## 5. Constraints
- **C1**: Maximum file upload size is 16MB.
- **C2**: Supported file formats:
  - Photos: PNG, JPG, JPEG.
  - Medical records: TXT, PDF, PNG, JPG, JPEG.
- **C3**: The system shall use Flask 2.3.3 and compatible library versions.
- **C4**: SQLite is the default database for development; MySQL/PostgreSQL are optional.

## 6. Assumptions
- Users have Python 3.8+ installed.
- For MySQL/PostgreSQL, a database server is available and configured.
- The `base_data_path` directory is writable by the application.
- Users follow the `dog_app.conf.example` template to create `dog_app.conf`.

## 7. Implementation Notes
- **Configuration Flexibility**:
  - The system loads `dog_app.conf` from the current working directory (e.g., `grok/` when running `python -m dog_app.app`), allowing users to switch configurations by changing directories or files.
  - A fallback to `/etc/dog_app.conf` supports production environments.
  - `dog_app.conf.example` in `dog_app/` provides a template for setup.
- **Development**:
  - Run from `~/Documents/Code/dogs/grok/` with `dog_app.conf` in that directory.
  - Use SQLite for simplicity (`database.db` in `base_data_path`).
- **Production**:
  - Deploy with Gunicorn and Nginx.
  - Use `/etc/dog_app.conf` and a secure `base_data_path` (e.g., `/var/lib/dog_app`).
  - Consider MySQL/PostgreSQL for scalability.
- **Version Control**:
  - Exclude `dog_app.conf`, `database.db`, and `Uploads/` from Git.
  - Include `dog_app.conf.example` and `requirements.txt`.