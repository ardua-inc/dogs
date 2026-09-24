"""
About page route.
"""
import os
from flask import Blueprint, current_app, render_template
from flask_login import login_required

from dogs_app import __version__
from dogs_app.utils.changelog import load_changelog

about_bp = Blueprint('about', __name__)


@about_bp.route('/about')
@login_required
def about():
    """Display the about page with version information."""
    git_commit = os.environ.get('APP_VERSION', 'dev')
    return render_template('about.html', version=__version__, git_commit=git_commit)


@about_bp.route('/about/changelog')
@login_required
def changelog():
    """Display the release history from CHANGELOG.md."""
    entries = load_changelog(current_app.config['CHANGELOG_PATH'])
    if entries is None:
        current_app.logger.warning('Changelog not readable at %s',
                                   current_app.config['CHANGELOG_PATH'])
    return render_template('changelog.html', version=__version__, entries=entries)
