"""
About page route.
"""
import os
from flask import Blueprint, render_template
from flask_login import login_required

about_bp = Blueprint('about', __name__)


@about_bp.route('/about')
@login_required
def about():
    """Display the about page with version information."""
    version = os.environ.get('APP_VERSION', 'dev')
    return render_template('about.html', version=version)
