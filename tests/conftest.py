"""
Pytest fixtures for the Dogs application tests.
"""
import pytest
from werkzeug.security import generate_password_hash
from dogs_app import create_app, db
from dogs_app.models import User, Dog


@pytest.fixture
def app():
    """Create application for testing."""
    app = create_app('testing')

    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    """Create test client."""
    return app.test_client()


@pytest.fixture
def runner(app):
    """Create CLI test runner."""
    return app.test_cli_runner()


@pytest.fixture
def admin_user(app):
    """Create admin user for testing."""
    with app.app_context():
        user = User(
            username='testadmin',
            password_hash=generate_password_hash('testpass'),
            role='admin',
            full_name='Test Admin',
            email='admin@test.com',
            is_active=True
        )
        db.session.add(user)
        db.session.commit()
        return user


@pytest.fixture
def viewer_user(app):
    """Create viewer user for testing."""
    with app.app_context():
        user = User(
            username='testviewer',
            password_hash=generate_password_hash('testpass'),
            role='viewer',
            full_name='Test Viewer',
            email='viewer@test.com',
            is_active=True
        )
        db.session.add(user)
        db.session.commit()
        return user


@pytest.fixture
def sample_dog(app):
    """Create sample dog for testing."""
    from datetime import date
    with app.app_context():
        dog = Dog(
            name='Buddy',
            breed='Golden Retriever',
            birthdate=date(2020, 1, 15),
            status='Living'
        )
        db.session.add(dog)
        db.session.commit()
        return dog


@pytest.fixture
def logged_in_admin(client, admin_user):
    """Log in as admin user."""
    client.post('/login', data={
        'username': 'testadmin',
        'password': 'testpass'
    })
    return client


@pytest.fixture
def logged_in_viewer(client, viewer_user):
    """Log in as viewer user."""
    client.post('/login', data={
        'username': 'testviewer',
        'password': 'testpass'
    })
    return client
