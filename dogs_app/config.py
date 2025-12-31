"""
Configuration classes for different environments.
"""
import os
from datetime import timedelta
from pathlib import Path

basedir = Path(__file__).parent.parent


class Config:
    """Base configuration."""
    SECRET_KEY = os.environ.get('FLASK_SECRET_KEY', 'dev-secret-key-change-in-production')

    # Session configuration - stay logged in for 30 days
    REMEMBER_COOKIE_DURATION = timedelta(days=30)
    PERMANENT_SESSION_LIFETIME = timedelta(days=30)

    # SQLAlchemy
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # File uploads
    BASE_DATA_PATH = os.environ.get('BASE_DATA_PATH', str(basedir))
    UPLOAD_FOLDER = os.path.join(BASE_DATA_PATH, 'uploads')
    DOG_PHOTOS_FOLDER = os.path.join(UPLOAD_FOLDER, 'dog_photos')
    MEDICAL_RECORDS_FOLDER = os.path.join(UPLOAD_FOLDER, 'medical_records')
    MAX_CONTENT_LENGTH = 100 * 1024 * 1024  # 100MB for bulk photo uploads

    # Allowed file extensions
    ALLOWED_IMAGE_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
    ALLOWED_DOCUMENT_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg'}

    # Thumbnail sizes
    THUMB_SIZES = {
        'sm': (200, 200),
        'md': (400, 400),
        'lg': (800, 800),
    }


class DevelopmentConfig(Config):
    """Development configuration."""
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        f"sqlite:///{os.path.join(Config.BASE_DATA_PATH, 'dogs.db')}"


class ProductionConfig(Config):
    """Production configuration."""
    DEBUG = False

    # SQLite database - simple and sufficient for small dataset
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        f"sqlite:///{os.path.join(Config.BASE_DATA_PATH, 'dogs.db')}"


class TestingConfig(Config):
    """Testing configuration."""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False


config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}
