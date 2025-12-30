"""
Dog management routes: list, view, add, edit.
"""
from datetime import datetime, timedelta
from flask import Blueprint, render_template, redirect, url_for, flash, request, abort
from flask_login import login_required, current_user
from dogs_app.models import Dog, Vaccination
from dogs_app import db

dogs_bp = Blueprint('dogs', __name__)


def get_upcoming_vaccinations():
    """Get vaccinations due within the next 30 days."""
    today = datetime.now().date()
    thirty_days = today + timedelta(days=30)
    return Vaccination.query.filter(
        Vaccination.next_due_date >= today,
        Vaccination.next_due_date <= thirty_days
    ).all()


@dogs_bp.route('/')
@login_required
def index():
    """Home page showing all dogs."""
    # Order by status (Living first, Deceased second), then alphabetically by name
    dogs = Dog.query.order_by(Dog.status.desc(), Dog.name).all()
    alerts = get_upcoming_vaccinations()
    return render_template('index.html', dogs=dogs, alerts=alerts)


@dogs_bp.route('/dog/<int:dog_id>')
@login_required
def dog_detail(dog_id):
    """View dog details."""
    dog = Dog.query.get_or_404(dog_id)
    photos = dog.photos.order_by('sort_order', 'upload_date').all()
    medical_records = dog.medical_records.order_by(db.desc('record_date')).all()
    vaccinations = dog.vaccinations.order_by(db.desc('date_administered')).all()

    # Get next upcoming vaccination for living dogs
    next_vaccination = None
    if dog.status == 'Living':
        today = datetime.now().date()
        next_vaccination = Vaccination.query.filter(
            Vaccination.dog_id == dog_id,
            Vaccination.next_due_date >= today
        ).order_by(Vaccination.next_due_date).first()

    return render_template('dog_detail.html',
                           dog=dog,
                           photos=photos,
                           medical_records=medical_records,
                           vaccinations=vaccinations,
                           next_vaccination=next_vaccination)


@dogs_bp.route('/add_dog', methods=['GET', 'POST'])
@login_required
def add_dog():
    """Add a new dog."""
    if current_user.role not in ['admin', 'doctor']:
        abort(403)

    if request.method == 'POST':
        name = request.form.get('name')
        breed = request.form.get('breed')
        birthdate_str = request.form.get('birthdate')
        deathdate_str = request.form.get('deathdate')

        if not name:
            flash('Name is required')
            return render_template('add_dog.html')

        birthdate = datetime.strptime(birthdate_str, '%Y-%m-%d').date() if birthdate_str else None
        deathdate = datetime.strptime(deathdate_str, '%Y-%m-%d').date() if deathdate_str else None
        status = 'Deceased' if deathdate else 'Living'
        microchip_company = request.form.get('microchip_company')
        microchip_id = request.form.get('microchip_id')

        dog = Dog(
            name=name,
            breed=breed,
            birthdate=birthdate,
            deathdate=deathdate,
            status=status,
            microchip_company=microchip_company,
            microchip_id=microchip_id
        )
        db.session.add(dog)
        db.session.commit()
        flash('Dog added successfully')
        return redirect(url_for('dogs.index'))

    return render_template('add_dog.html')


@dogs_bp.route('/edit_dog/<int:dog_id>', methods=['GET', 'POST'])
@login_required
def edit_dog(dog_id):
    """Edit dog details."""
    if current_user.role not in ['admin', 'doctor']:
        abort(403)

    dog = Dog.query.get_or_404(dog_id)
    photos = dog.photos.order_by('sort_order', 'upload_date').all()
    medical_records = dog.medical_records.order_by(db.desc('record_date')).all()
    vaccinations = dog.vaccinations.order_by(db.desc('date_administered')).all()

    if request.method == 'POST' and 'dog_update' in request.form:
        dog.name = request.form.get('name')
        dog.breed = request.form.get('breed')

        birthdate_str = request.form.get('birthdate')
        deathdate_str = request.form.get('deathdate')

        dog.birthdate = datetime.strptime(birthdate_str, '%Y-%m-%d').date() if birthdate_str else None
        dog.deathdate = datetime.strptime(deathdate_str, '%Y-%m-%d').date() if deathdate_str else None
        dog.status = 'Deceased' if dog.deathdate else 'Living'
        dog.microchip_company = request.form.get('microchip_company')
        dog.microchip_id = request.form.get('microchip_id')

        db.session.commit()
        flash('Dog updated successfully')

    return render_template('edit_dog.html',
                           dog=dog,
                           photos=photos,
                           medical_records=medical_records,
                           vaccinations=vaccinations)


@dogs_bp.route('/delete_dog/<int:dog_id>', methods=['POST'])
@login_required
def delete_dog(dog_id):
    """Delete a dog and all associated records."""
    if current_user.role != 'admin':
        abort(403)

    dog = Dog.query.get_or_404(dog_id)
    db.session.delete(dog)
    db.session.commit()
    flash(f'Dog "{dog.name}" has been deleted')
    return redirect(url_for('dogs.index'))
