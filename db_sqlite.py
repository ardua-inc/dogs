import sqlite3
from dog_app.db import DatabaseInterface
from werkzeug.security import generate_password_hash

class SQLiteDatabase(DatabaseInterface):
    def __init__(self, config):
        self.database = config['database']

    def connect(self):
        conn = sqlite3.connect(self.database)
        conn.row_factory = sqlite3.Row
        return conn

    def close(self, conn):
        conn.commit()
        conn.close()

    def init_db(self):
        conn = self.connect()
        conn.executescript('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL,
            full_name TEXT,
            email TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            is_active BOOLEAN DEFAULT 1
        );
        CREATE TABLE IF NOT EXISTS dogs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            breed TEXT,
            birthdate DATE,
            deathdate DATE,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            status TEXT DEFAULT 'Living'
        );
        CREATE TABLE IF NOT EXISTS dog_photos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            dog_id INTEGER,
            original_filename TEXT NOT NULL,
            filename TEXT NOT NULL,
            filepath TEXT NOT NULL,
            is_primary BOOLEAN DEFAULT 0,
            upload_date DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (dog_id) REFERENCES dogs (id)
        );
        CREATE TABLE IF NOT EXISTS medical_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            dog_id INTEGER,
            original_filename TEXT NOT NULL,
            filename TEXT NOT NULL,
            filepath TEXT NOT NULL,
            description TEXT,
            category TEXT,
            record_date DATE,
            upload_date DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (dog_id) REFERENCES dogs (id)
        );
        CREATE TABLE IF NOT EXISTS vaccinations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            dog_id INTEGER,
            vaccine_type TEXT NOT NULL,
            date_administered DATE NOT NULL,
            next_due_date DATE,
            notes TEXT,
            certificate_id INTEGER,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (dog_id) REFERENCES dogs (id),
            FOREIGN KEY (certificate_id) REFERENCES medical_records (id)
        );
        ''')
        hashed_password = generate_password_hash('admin123')
        conn.execute('INSERT OR IGNORE INTO users (username, password_hash, role, full_name, email, is_active) VALUES (?, ?, ?, ?, ?, ?)',
                    ('admin', hashed_password, 'admin', 'Admin User', 'admin@example.com', 1))
        conn.commit()
        conn.close()

    def execute(self, query, params=()):
        conn = self.connect()
        try:
            conn.execute(query, params)
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()

    def fetch_one(self, query, params=()):
        conn = self.connect()
        try:
            result = conn.execute(query, params).fetchone()
            return result
        finally:
            conn.close()

    def fetch_all(self, query, params=()):
        conn = self.connect()
        try:
            result = conn.execute(query, params).fetchall()
            return result
        finally:
            conn.close()

    def last_insert_id(self):
        conn = self.connect()
        try:
            result = conn.execute('SELECT last_insert_rowid()').fetchone()
            return result[0]
        finally:
            conn.close()
