"""
SQLAlchemy database models.
"""
from datetime import datetime, date, timezone
from flask_login import UserMixin
from dogs_app import db


class User(UserMixin, db.Model):
    """User model for authentication."""
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='viewer')  # admin, doctor, viewer
    full_name = db.Column(db.String(120))
    email = db.Column(db.String(120))
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    def __repr__(self):
        return f'<User {self.username}>'


class Dog(db.Model):
    """Dog model."""
    __tablename__ = 'dogs'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    breed = db.Column(db.String(100))
    birthdate = db.Column(db.Date)
    deathdate = db.Column(db.Date)
    status = db.Column(db.String(20), default='Living')  # Living, Deceased
    microchip_company = db.Column(db.String(100))
    microchip_id = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    photos = db.relationship('DogPhoto', backref='dog', lazy='dynamic', cascade='all, delete-orphan')
    medical_records = db.relationship('MedicalRecord', backref='dog', lazy='dynamic', cascade='all, delete-orphan')
    vaccinations = db.relationship('Vaccination', backref='dog', lazy='dynamic', cascade='all, delete-orphan')

    @property
    def age(self):
        """Calculate age from birthdate."""
        if not self.birthdate:
            return 'Unknown'
        end_date = self.deathdate or date.today()
        delta = end_date - self.birthdate
        years = delta.days // 365
        months = (delta.days % 365) // 30
        days = (delta.days % 365) % 30
        return f'{years} years, {months} months, {days} days'

    @property
    def primary_photo(self):
        """Get the primary photo for this dog."""
        return self.photos.filter_by(is_primary=True).first()

    def __repr__(self):
        return f'<Dog {self.name}>'


class DogPhoto(db.Model):
    """Dog photo model with enhanced fields."""
    __tablename__ = 'dog_photos'

    id = db.Column(db.Integer, primary_key=True)
    dog_id = db.Column(db.Integer, db.ForeignKey('dogs.id'), nullable=False)
    original_filename = db.Column(db.String(255))
    filename = db.Column(db.String(255), nullable=False)
    filepath = db.Column(db.String(512), nullable=False)
    is_primary = db.Column(db.Boolean, default=False)
    caption = db.Column(db.Text)
    taken_date = db.Column(db.Date)
    sort_order = db.Column(db.Integer, default=0)
    upload_date = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    @property
    def thumb_sm(self):
        """Small thumbnail filename."""
        return f"thumb_sm_{self.filename}"

    @property
    def thumb_md(self):
        """Medium thumbnail filename."""
        return f"thumb_md_{self.filename}"

    @property
    def thumb_lg(self):
        """Large thumbnail filename."""
        return f"thumb_lg_{self.filename}"

    def to_dict(self):
        """Convert to dictionary for JSON responses."""
        return {
            'id': self.id,
            'dog_id': self.dog_id,
            'filename': self.filename,
            'caption': self.caption,
            'taken_date': self.taken_date.isoformat() if self.taken_date else None,
            'is_primary': self.is_primary,
            'sort_order': self.sort_order,
        }

    def __repr__(self):
        return f'<DogPhoto {self.filename}>'


class MedicalRecord(db.Model):
    """Medical record model."""
    __tablename__ = 'medical_records'

    id = db.Column(db.Integer, primary_key=True)
    dog_id = db.Column(db.Integer, db.ForeignKey('dogs.id'), nullable=False)
    original_filename = db.Column(db.String(255))
    filename = db.Column(db.String(255), nullable=False)
    filepath = db.Column(db.String(512), nullable=False)
    description = db.Column(db.Text)
    category = db.Column(db.String(50))  # Vaccination, Lab Results, etc.
    record_date = db.Column(db.Date)
    upload_date = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationship to vaccinations that reference this as certificate
    vaccination_certificates = db.relationship('Vaccination', backref='certificate', lazy='dynamic')

    def __repr__(self):
        return f'<MedicalRecord {self.original_filename}>'


class Vaccination(db.Model):
    """Vaccination record model."""
    __tablename__ = 'vaccinations'

    id = db.Column(db.Integer, primary_key=True)
    dog_id = db.Column(db.Integer, db.ForeignKey('dogs.id'), nullable=False)
    vaccine_type = db.Column(db.String(100), nullable=False)
    date_administered = db.Column(db.Date, nullable=False)
    next_due_date = db.Column(db.Date)
    notes = db.Column(db.Text)
    certificate_id = db.Column(db.Integer, db.ForeignKey('medical_records.id'))
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    def __repr__(self):
        return f'<Vaccination {self.vaccine_type} for dog {self.dog_id}>'
