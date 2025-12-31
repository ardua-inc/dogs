"""
Route blueprints for the Dogs application.
"""
from dogs_app.routes.auth import auth_bp
from dogs_app.routes.dogs import dogs_bp
from dogs_app.routes.photos import photos_bp
from dogs_app.routes.medical import medical_bp
from dogs_app.routes.admin import admin_bp
from dogs_app.routes.about import about_bp

__all__ = ['auth_bp', 'dogs_bp', 'photos_bp', 'medical_bp', 'admin_bp', 'about_bp']
