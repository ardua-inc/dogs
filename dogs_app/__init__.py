"""
Comanche Dogs - Flask Application Factory
"""
import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager

db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()


def create_app(config_name=None):
    """Application factory for creating Flask app instances."""
    app = Flask(__name__)

    # Load configuration
    if config_name is None:
        config_name = os.environ.get('FLASK_CONFIG', 'development')

    from dogs_app.config import config
    app.config.from_object(config[config_name])

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'

    # Ensure upload directories exist
    os.makedirs(app.config['DOG_PHOTOS_FOLDER'], exist_ok=True)
    os.makedirs(app.config['MEDICAL_RECORDS_FOLDER'], exist_ok=True)

    # Register blueprints
    from dogs_app.routes.auth import auth_bp
    from dogs_app.routes.dogs import dogs_bp
    from dogs_app.routes.photos import photos_bp
    from dogs_app.routes.medical import medical_bp
    from dogs_app.routes.admin import admin_bp
    from dogs_app.routes.about import about_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(dogs_bp)
    app.register_blueprint(photos_bp)
    app.register_blueprint(medical_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(about_bp)

    # User loader for Flask-Login
    from dogs_app.models import User

    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(User, int(user_id))

    # Create tables and seed admin user
    with app.app_context():
        db.create_all()
        _seed_admin_user()

    return app


def _seed_admin_user():
    """Create default admin user if no users exist."""
    from dogs_app.models import User
    from werkzeug.security import generate_password_hash

    if User.query.count() == 0:
        admin = User(
            username='admin',
            password_hash=generate_password_hash('admin123'),
            role='admin',
            full_name='Administrator',
            email='admin@example.com',
            is_active=True
        )
        db.session.add(admin)
        db.session.commit()
