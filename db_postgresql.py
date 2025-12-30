import psycopg2
from psycopg2.extras import DictCursor
from dog_app.db import DatabaseInterface
from werkzeug.security import generate_password_hash

class PostgreSQLDatabase(DatabaseInterface):
    def __init__(self, config):
        self.config = config

    def connect(self):
        return psycopg2.connect(**self.config, cursor_factory=DictCursor)

    def close(self, conn):
        conn.commit()
        conn.close()

    def init_db(self):
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            username VARCHAR(255) UNIQUE NOT NULL,
            password_hash VARCHAR(255) NOT NULL,
            role VARCHAR(50) NOT NULL,
            full_name VARCHAR(255),
            email VARCHAR(255),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            is_active BOOLEAN DEFAULT TRUE
        )
        ''')
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS dogs (
            id SERIAL PRIMARY KEY,
            name VARCHAR(255) NOT NULL,
            breed VARCHAR(255),
            birthdate DATE,
            deathdate DATE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            status VARCHAR(50) DEFAULT 'Living'
        )
        ''')
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS dog_photos (
            id SERIAL PRIMARY KEY,
            dog_id INTEGER,
            original_filename VARCHAR(255) NOT NULL,
            filename VARCHAR(255) NOT NULL,
            filepath VARCHAR(255) NOT NULL,
            is_primary BOOLEAN DEFAULT FALSE,
            upload_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (dog_id) REFERENCES dogs (id)
        )
        ''')
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS medical_records (
            id SERIAL PRIMARY KEY,
            dog_id INTEGER,
            original_filename VARCHAR(255) NOT NULL,
            filename VARCHAR(255) NOT NULL,
            filepath VARCHAR(255) NOT NULL,
            description TEXT,
            category VARCHAR(255),
            record_date DATE,
            upload_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (dog_id) REFERENCES dogs (id)
        )
        ''')
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS vaccinations (
            id SERIAL PRIMARY KEY,
            dog_id INTEGER,
            vaccine_type VARCHAR(255) NOT NULL,
            date_administered DATE NOT NULL,
            next_due_date DATE,
            notes TEXT,
            certificate_id INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (dog_id) REFERENCES dogs (id),
            FOREIGN KEY (certificate_id) REFERENCES medical_records (id)
        )
        ''')
        hashed_password = generate_password_hash('admin123')
        cursor.execute('INSERT INTO users (username, password_hash, role, full_name, email, is_active) VALUES (%s, %s, %s, %s, %s, %s) ON CONFLICT DO NOTHING',
                       ('admin', hashed_password, 'admin', 'Admin User', 'admin@example.com', True))
        conn.commit()
        conn.close()

    def execute(self, query, params=()):
        conn = self.connect()
        cursor = conn.cursor()
        try:
            cursor.execute(query, params)
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()

    def fetch_one(self, query, params=()):
        conn = self.connect()
        cursor = conn.cursor()
        try:
            cursor.execute(query, params)
            return cursor.fetchone()
        finally:
            conn.close()

    def fetch_all(self, query, params=()):
        conn = self.connect()
        cursor = conn.cursor()
        try:
            cursor.execute(query, params)
            return cursor.fetchall()
        finally:
            conn.close()

    def last_insert_id(self):
        conn = self.connect()
        cursor = conn.cursor()
        try:
            cursor.execute('SELECT lastval()')
            return cursor.fetchone()[0]
        finally:
            conn.close()
