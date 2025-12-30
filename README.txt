Comanche Dogs
Comanche Dogs is a Flask-based web application for managing dog records, including their details, photos, medical records, and vaccination schedules. It supports multiple database backends (SQLite, MySQL, PostgreSQL) and includes user authentication with role-based access control.
Features

User Management:
Roles: admin (full access), doctor (edit dogs and records), viewer (read-only).
Admin can register, edit, or delete users via /manage_users.
Users can change their passwords via /change_password.


Dog Management:
Add, edit, or view dog details (name, breed, birthdate, deathdate, status).
View-only dog details at /dog/<dog_id> for all users.
Edit dogs at /edit_dog/<dog_id> (admin/doctor only).


Photo Management:
Upload photos (PNG, JPG, JPEG) for dogs, with automatic thumbnail generation.
Set a primary photo (indicated by a checkmark).
Delete photos (admin/doctor only).


Medical Records:
Upload medical records (TXT, PDF, PNG, JPG, JPEG) with description, category, and date.
Edit or delete records (admin/doctor only).


Vaccinations:
Add vaccination records with type, administration date, next due date, notes, and optional certificate ID.
Alerts for upcoming vaccinations (within 30 days) on the homepage.


Database Support:
Modular support for SQLite, MySQL, or PostgreSQL, configured via dog_app.conf.


Configuration:
Configurable data path and database settings via dog_app.conf (loaded from the current working directory or /etc/dog_app.conf).



Project Structure
grok/
├── dog_app.conf  # Configuration file (in working directory, e.g., grok/)
└── dog_app/
    ├── __init__.py
    ├── app.py  # Main Flask application
    ├── db.py  # Database interface
    ├── db_sqlite.py  # SQLite implementation
    ├── db_mysql.py  # MySQL implementation
    ├── db_postgresql.py  # PostgreSQL implementation
    ├── dog_app.conf.example  # Example configuration file
    ├── requirements.txt  # Python dependencies
    ├── database.db  # SQLite database (default)
    ├── static/
    │   ├── css/
    │   │   └── styles.css
    │   └── js/
    │       └── scripts.js
    ├── templates/
    │   ├── add_dog.html
    │   ├── base.html
    │   ├── change_password.html
    │   ├── dog_detail.html
    │   ├── edit_dog.html
    │   ├── edit_medical_record.html
    │   ├── index.html
    │   ├── login.html
    │   ├── manage_users.html
    │   └── register.html
    └── Uploads/
        ├── dog_photos/  # Dog photos and thumbnails
        └── medical_records/  # Medical record files

Prerequisites

Python: 3.8 or higher
Dependencies: Listed in requirements.txt
Optional Databases:
SQLite: Included with Python (no setup needed).
MySQL: MySQL Server 8.0+.
PostgreSQL: PostgreSQL Server 12+.


System: Linux, macOS, or Windows (Linux recommended for production).

Setup for Local Development

Clone the Repository (if using version control):
git clone <repository-url>
cd grok


Create a Virtual Environment:
python -m venv dog_app/venv
source dog_app/venv/bin/activate  # On Windows: dog_app\venv\Scripts\activate


Install Dependencies:
pip install -r dog_app/requirements.txt


Configure dog_app.conf:

Copy the example configuration:cp dog_app/dog_app.conf.example dog_app.conf


Edit dog_app.conf:nano dog_app.conf

Example for SQLite:[General]
base_data_path = /path/to/grok/dog_app
secret_key = super_secret_key

[Database]
type = sqlite
sqlite_database = database.db
mysql_host = localhost
mysql_user = root
mysql_password = your_mysql_password
mysql_database = comanche_dogs
postgresql_host = localhost
postgresql_user = postgres
postgresql_password = your_postgresql_password
postgresql_database = comanche_dogs


Replace /path/to/grok/dog_app with the absolute path to dog_app/ (e.g., /Users/jramsey/Documents/Code/dogs/grok/dog_app).
Use a secure secret_key for production.
For MySQL/PostgreSQL, update the respective fields with valid credentials.




Set Up Data Directory:

Ensure base_data_path exists and contains database.db and Uploads/:mkdir -p dog_app/Uploads/dog_photos dog_app/Uploads/medical_records


Verify file paths in the database (if migrating existing data):sqlite3 dog_app/database.db

UPDATE dog_photos SET filepath = 'Uploads/dog_photos/' || filename;
UPDATE medical_records SET filepath = 'Uploads/medical_records/' || filename;




Run the Application:
cd grok
source dog_app/venv/bin/activate
python -m dog_app.app


Access at http://localhost:5056.
Log in with default credentials: admin / admin123.



Configuration (dog_app.conf)
The application loads dog_app.conf from the current working directory (e.g., grok/) or falls back to /etc/dog_app.conf in production. The file uses INI format with two sections:

[General]:
base_data_path: Absolute path to the directory containing database.db and Uploads/ (photos and medical records).
secret_key: Flask session secret key (use a random, secure string in production).


[Database]:
type: sqlite, mysql, or postgresql.
sqlite_database: Database file name (e.g., database.db), stored in base_data_path.
mysql_*: Host, user, password, and database name for MySQL.
postgresql_*: Host, user, password, and database name for PostgreSQL.



Example for local development (SQLite):
[General]
base_data_path = /Users/jramsey/Documents/Code/dogs/grok/dog_app
secret_key = super_secret_key

[Database]
type = sqlite
sqlite_database = database.db
mysql_host = localhost
mysql_user = root
mysql_password = your_mysql_password
mysql_database = comanche_dogs
postgresql_host = localhost
postgresql_user = postgres
postgresql_password = your_postgresql_password
postgresql_database = comanche_dogs

Copy dog_app/dog_app.conf.example to dog_app.conf and customize as needed.
Testing

Verify Setup:

Ensure dog_app.conf is in the working directory (e.g., grok/).
Check database.db and Uploads/ in base_data_path:ls dog_app/database.db
ls -l dog_app/Uploads/




Run Tests:

Start the app: python -m dog_app.app.
Open http://localhost:5056 and log in (admin / admin123).
Test features:
Homepage (/): Lists dogs and vaccination alerts.
Dog details (/dog/<dog_id>): View dog info, photos, and records.
Edit dog (/edit_dog/<dog_id>): Add/edit photos, records, vaccinations (admin/doctor).
User management (/manage_users): Admin-only user CRUD.
Password change (/change_password).


Verify database:sqlite3 dog_app/database.db
.tables
SELECT * FROM dogs;
SELECT * FROM dog_photos;
SELECT * FROM medical_records;




Troubleshooting:

Config File Errors:
Ensure dog_app.conf is in the current working directory:ls dog_app.conf


Check permissions: chmod 644 dog_app.conf.
Verify INI format (no missing sections/keys).


File Path Issues:
If photos/records fail to load, ensure base_data_path matches the location of database.db and Uploads/.
Update database file paths:UPDATE dog_photos SET filepath = 'Uploads/dog_photos/' || filename;
UPDATE medical_records SET filepath = 'Uploads/medical_records/' || filename;




Database Errors:
For MySQL/PostgreSQL, verify credentials and server status.
Share tracebacks for debugging.





Deployment for Production

Prepare the Server (e.g., Ubuntu):
sudo apt-get update
sudo apt-get install python3 python3-venv python3-pip nginx gunicorn
sudo apt-get install sqlite3  # For SQLite
# For MySQL: sudo apt-get install mysql-server libmysqlclient-dev
# For PostgreSQL: sudo apt-get install postgresql postgresql-contrib


Copy Files:
scp -r grok user@server:/path/to/grok


Set Up Configuration:

Create /etc/dog_app.conf:sudo cp grok/dog_app/dog_app.conf.example /etc/dog_app.conf
sudo nano /etc/dog_app.conf

Example for MySQL:[General]
base_data_path = /var/lib/dog_app
secret_key = your_secure_random_key

[Database]
type = mysql
sqlite_database = database.db
mysql_host = localhost
mysql_user = dog_app_user
mysql_password = secure_password
mysql_database = comanche_dogs
postgresql_host = localhost
postgresql_user = postgres
postgresql_password = secure_password
postgresql_database = comanche_dogs


Secure the file:sudo chown dog_app_user:dog_app_group /etc/dog_app.conf
sudo chmod 600 /etc/dog_app.conf




Set Up Data Directory:
sudo mkdir -p /var/lib/dog_app/Uploads/{dog_photos,medical_records}
sudo mv grok/dog_app/database.db /var/lib/dog_app/
sudo mv grok/dog_app/Uploads /var/lib/dog_app/
sudo chown -R dog_app_user:dog_app_group /var/lib/dog_app


Install Dependencies:
cd /path/to/grok
python3 -m venv dog_app/venv
source dog_app/venv/bin/activate
pip install -r dog_app/requirements.txt


Set Up Database (if using MySQL/PostgreSQL):

MySQL:mysql -u root -p -e "CREATE DATABASE comanche_dogs;"
mysql -u root -p -e "CREATE USER 'dog_app_user'@'localhost' IDENTIFIED BY 'secure_password';"
mysql -u root -p -e "GRANT ALL PRIVILEGES ON comanche_dogs.* TO 'dog_app_user'@'localhost';"

Migrate SQLite data:sqlite3 /var/lib/dog_app/database.db .dump > dump.sql
nano dump.sql  # Replace BOOLEAN with TINYINT, AUTOINCREMENT with AUTO_INCREMENT
mysql -u dog_app_user -p comanche_dogs < dump.sql


PostgreSQL:sudo -u postgres psql -c "CREATE DATABASE comanche_dogs;"
sudo -u postgres psql -c "CREATE USER dog_app_user WITH PASSWORD 'secure_password';"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE comanche_dogs TO dog_app_user;"




Run with Gunicorn:
cd /path/to/grok
source dog_app/venv/bin/activate
gunicorn -w 4 -b 0.0.0.0:5056 dog_app.app:app


Set Up Nginx:
sudo nano /etc/nginx/sites-available/dog_app

Add:
server {
    listen 80;
    server_name your_domain.com;
    location / {
        proxy_pass http://127.0.0.1:5056;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}

Enable and restart:
sudo ln -s /etc/nginx/sites-available/dog_app /etc/nginx/sites-enabled/
sudo systemctl restart nginx


Use Systemd for Gunicorn:
sudo nano /etc/systemd/system/dog_app.service

Add:
[Unit]
Description=Comanche Dogs Gunicorn Service
After=network.target

[Service]
User=dog_app_user
Group=dog_app_group
WorkingDirectory=/path/to/grok
ExecStart=/path/to/grok/dog_app/venv/bin/gunicorn -w 4 -b 0.0.0.0:5056 dog_app.app:app

[Install]
WantedBy=multi-user.target

Enable and start:
sudo systemctl enable dog_app
sudo systemctl start dog_app



Practical Implementation Notes

Version Control:
Add dog_app.conf and database.db to .gitignore:echo -e "dog_app.conf\ndatabase.db\nUploads/" >> .gitignore


Include dog_app.conf.example and requirements.txt in the repository.


Security:
Use a strong secret_key in production.
Secure /etc/dog_app.conf with chmod 600.
Use environment variables for sensitive data (e.g., database passwords) if preferred.


Database Migration:
For MySQL/PostgreSQL, migrate SQLite data using sqldump or manual export/import.
Ensure file paths in dog_photos and medical_records match base_data_path/Uploads/.


Backup:
Regularly back up database.db and Uploads/:cp -r dog_app/database.db dog_app/Uploads /backup/location




Performance:
For production, adjust Gunicorn workers (-w) based on server CPU cores.
Use a CDN for static files (static/) if needed.



License
MIT License (or as specified by your project).
