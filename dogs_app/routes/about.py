"""
About page route.
"""
import os
from flask import Blueprint, render_template
from flask_login import login_required

about_bp = Blueprint('about', __name__)

# Semantic version - update this when releasing new versions
APP_VERSION = '2.0.1'


@about_bp.route('/about')
@login_required
def about():
    """Display the about page with version information."""
    git_commit = os.environ.get('APP_VERSION', 'dev')
    return render_template('about.html', version=APP_VERSION, git_commit=git_commit)
