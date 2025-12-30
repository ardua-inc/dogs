"""
Tests for route handlers.
"""
import pytest


class TestAuthRoutes:
    """Tests for authentication routes."""

    def test_login_page_loads(self, client):
        """Test login page loads."""
        response = client.get('/login')
        assert response.status_code == 200
        assert b'Login' in response.data

    def test_login_success(self, client, admin_user, app):
        """Test successful login."""
        response = client.post('/login', data={
            'username': 'testadmin',
            'password': 'testpass'
        }, follow_redirects=True)
        assert response.status_code == 200

    def test_login_failure(self, client):
        """Test login with wrong credentials."""
        response = client.post('/login', data={
            'username': 'wronguser',
            'password': 'wrongpass'
        })
        assert b'Invalid username or password' in response.data

    def test_logout(self, logged_in_admin):
        """Test logout."""
        response = logged_in_admin.get('/logout', follow_redirects=True)
        assert response.status_code == 200
        assert b'Login' in response.data

    def test_protected_route_requires_login(self, client):
        """Test that protected routes redirect to login."""
        response = client.get('/')
        assert response.status_code == 302
        assert '/login' in response.location


class TestDogRoutes:
    """Tests for dog management routes."""

    def test_index_page(self, logged_in_admin, sample_dog, app):
        """Test home page shows dogs."""
        with app.app_context():
            response = logged_in_admin.get('/')
            assert response.status_code == 200
            assert b'Dogs' in response.data

    def test_dog_detail_page(self, logged_in_admin, sample_dog, app):
        """Test dog detail page."""
        with app.app_context():
            from dogs_app.models import Dog
            dog = Dog.query.first()
            response = logged_in_admin.get(f'/dog/{dog.id}')
            assert response.status_code == 200
            assert b'Buddy' in response.data

    def test_add_dog_page_admin(self, logged_in_admin):
        """Test add dog page accessible by admin."""
        response = logged_in_admin.get('/add_dog')
        assert response.status_code == 200
        assert b'Add New Dog' in response.data

    def test_add_dog_page_viewer_forbidden(self, logged_in_viewer):
        """Test add dog page forbidden for viewers."""
        response = logged_in_viewer.get('/add_dog')
        assert response.status_code == 403

    def test_add_dog_submission(self, logged_in_admin, app):
        """Test adding a new dog."""
        response = logged_in_admin.post('/add_dog', data={
            'name': 'Rex',
            'breed': 'Labrador',
            'birthdate': '2021-03-15'
        }, follow_redirects=True)
        assert response.status_code == 200

        with app.app_context():
            from dogs_app.models import Dog
            dog = Dog.query.filter_by(name='Rex').first()
            assert dog is not None
            assert dog.breed == 'Labrador'


class TestAdminRoutes:
    """Tests for admin routes."""

    def test_manage_users_admin(self, logged_in_admin):
        """Test manage users accessible by admin."""
        response = logged_in_admin.get('/manage_users')
        assert response.status_code == 200
        assert b'Manage Users' in response.data

    def test_manage_users_viewer_forbidden(self, logged_in_viewer):
        """Test manage users forbidden for non-admins."""
        response = logged_in_viewer.get('/manage_users')
        assert response.status_code == 403

    def test_register_page(self, logged_in_admin):
        """Test register user page."""
        response = logged_in_admin.get('/register')
        assert response.status_code == 200
        assert b'Register' in response.data


class TestPhotoRoutes:
    """Tests for photo routes."""

    def test_slideshow_page(self, logged_in_admin):
        """Test slideshow page loads."""
        response = logged_in_admin.get('/slideshow')
        assert response.status_code == 200
        assert b'Slideshow' in response.data

    def test_dog_slideshow_page(self, logged_in_admin, sample_dog, app):
        """Test dog-specific slideshow page."""
        with app.app_context():
            from dogs_app.models import Dog
            dog = Dog.query.first()
            response = logged_in_admin.get(f'/dog/{dog.id}/slideshow')
            assert response.status_code == 200


class TestMedicalRoutes:
    """Tests for medical record routes."""

    def test_add_vaccination(self, logged_in_admin, sample_dog, app):
        """Test adding vaccination."""
        with app.app_context():
            from dogs_app.models import Dog
            dog = Dog.query.first()
            response = logged_in_admin.post(f'/add_vaccination/{dog.id}', data={
                'vaccine_type': 'Rabies',
                'date_administered': '2023-06-15',
                'next_due_date': '2024-06-15',
                'notes': 'Annual'
            }, follow_redirects=True)
            assert response.status_code == 200
