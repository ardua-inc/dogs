"""
Tests for database models.
"""
import pytest
from datetime import date
from dogs_app.models import User, Dog, DogPhoto, MedicalRecord, Vaccination
from dogs_app import db


class TestUserModel:
    """Tests for the User model."""

    def test_create_user(self, app):
        """Test creating a user."""
        with app.app_context():
            user = User(
                username='newuser',
                password_hash='hashedpassword',
                role='viewer',
                full_name='New User',
                email='new@test.com'
            )
            db.session.add(user)
            db.session.commit()

            assert user.id is not None
            assert user.username == 'newuser'
            assert user.role == 'viewer'
            assert user.is_active is True

    def test_user_repr(self, app):
        """Test user string representation."""
        with app.app_context():
            user = User(username='testuser', password_hash='hash', role='admin')
            assert repr(user) == '<User testuser>'


class TestDogModel:
    """Tests for the Dog model."""

    def test_create_dog(self, app):
        """Test creating a dog."""
        with app.app_context():
            dog = Dog(
                name='Max',
                breed='German Shepherd',
                birthdate=date(2019, 5, 10),
                status='Living'
            )
            db.session.add(dog)
            db.session.commit()

            assert dog.id is not None
            assert dog.name == 'Max'
            assert dog.breed == 'German Shepherd'

    def test_dog_age_calculation(self, app):
        """Test age property calculation."""
        with app.app_context():
            dog = Dog(
                name='Puppy',
                breed='Beagle',
                birthdate=date(2022, 1, 1),
                status='Living'
            )
            db.session.add(dog)
            db.session.commit()

            age = dog.age
            assert 'years' in age
            assert 'months' in age
            assert 'days' in age

    def test_dog_age_unknown(self, app):
        """Test age when birthdate is not set."""
        with app.app_context():
            dog = Dog(name='Unknown', status='Living')
            db.session.add(dog)
            db.session.commit()

            assert dog.age == 'Unknown'

    def test_dog_deceased_age(self, app):
        """Test age calculation for deceased dog."""
        with app.app_context():
            dog = Dog(
                name='Old Timer',
                birthdate=date(2010, 1, 1),
                deathdate=date(2020, 1, 1),
                status='Deceased'
            )
            db.session.add(dog)
            db.session.commit()

            age = dog.age
            assert '10 years' in age or '9 years' in age  # Account for rounding

    def test_dog_primary_photo(self, app):
        """Test primary photo property."""
        with app.app_context():
            dog = Dog(name='Photogenic', status='Living')
            db.session.add(dog)
            db.session.commit()

            # No photos yet
            assert dog.primary_photo is None

            # Add a primary photo
            photo = DogPhoto(
                dog_id=dog.id,
                filename='test.jpg',
                filepath='/uploads/test.jpg',
                is_primary=True
            )
            db.session.add(photo)
            db.session.commit()

            assert dog.primary_photo is not None
            assert dog.primary_photo.filename == 'test.jpg'


class TestDogPhotoModel:
    """Tests for the DogPhoto model."""

    def test_photo_thumbnail_properties(self, app):
        """Test thumbnail filename properties."""
        with app.app_context():
            dog = Dog(name='Model', status='Living')
            db.session.add(dog)
            db.session.commit()

            photo = DogPhoto(
                dog_id=dog.id,
                filename='photo123.jpg',
                filepath='/uploads/photo123.jpg'
            )
            db.session.add(photo)
            db.session.commit()

            assert photo.thumb_sm == 'thumb_sm_photo123.jpg'
            assert photo.thumb_md == 'thumb_md_photo123.jpg'
            assert photo.thumb_lg == 'thumb_lg_photo123.jpg'

    def test_photo_to_dict(self, app):
        """Test to_dict method."""
        with app.app_context():
            dog = Dog(name='Model', status='Living')
            db.session.add(dog)
            db.session.commit()

            photo = DogPhoto(
                dog_id=dog.id,
                filename='photo.jpg',
                filepath='/uploads/photo.jpg',
                caption='Test caption',
                is_primary=True
            )
            db.session.add(photo)
            db.session.commit()

            data = photo.to_dict()
            assert data['filename'] == 'photo.jpg'
            assert data['caption'] == 'Test caption'
            assert data['is_primary'] is True


class TestVaccinationModel:
    """Tests for the Vaccination model."""

    def test_create_vaccination(self, app, sample_dog):
        """Test creating a vaccination record."""
        with app.app_context():
            dog = Dog.query.first()
            vaccination = Vaccination(
                dog_id=dog.id,
                vaccine_type='Rabies',
                date_administered=date(2023, 6, 15),
                next_due_date=date(2024, 6, 15),
                notes='Annual rabies vaccine'
            )
            db.session.add(vaccination)
            db.session.commit()

            assert vaccination.id is not None
            assert vaccination.vaccine_type == 'Rabies'
            assert vaccination.dog_id == dog.id
