"""
Medical records and vaccination routes.
"""
import os
import uuid
from datetime import datetime
from flask import Blueprint, render_template, redirect, url_for, flash, request, abort, current_app
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from dogs_app.models import Dog, MedicalRecord, Vaccination
from dogs_app import db

medical_bp = Blueprint('medical', __name__)

# Medical record categories
MEDICAL_CATEGORIES = [
    'Vaccination',
    'Lab Results',
    'X-Ray/Imaging',
    'Surgery Report',
    'Prescription',
    'Vet Visit Notes',
    'Dental Records',
    'Emergency Care',
    'Other'
]

# Vaccine types
VACCINE_TYPES = [
    'Rabies',
    'DHPP (Distemper, Hepatitis, Parainfluenza, Parvovirus)',
    'Bordetella (Kennel Cough)',
    'Leptospirosis',
    'Lyme Disease',
    'Canine Influenza',
    'Other'
]


def allowed_file(filename):
    """Check if file extension is allowed for documents."""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in current_app.config['ALLOWED_DOCUMENT_EXTENSIONS']


@medical_bp.route('/upload_medical_record/<int:dog_id>', methods=['POST'])
@login_required
def upload_medical_record(dog_id):
    """Upload a medical record."""
    if current_user.role not in ['admin', 'doctor']:
        abort(403)

    dog = Dog.query.get_or_404(dog_id)

    if 'record' not in request.files:
        flash('No file selected')
        return redirect(url_for('dogs.edit_dog', dog_id=dog_id))

    file = request.files['record']
    if not file or not file.filename:
        flash('No file selected')
        return redirect(url_for('dogs.edit_dog', dog_id=dog_id))

    if not allowed_file(file.filename):
        flash('Invalid file format')
        return redirect(url_for('dogs.edit_dog', dog_id=dog_id))

    original_filename = secure_filename(file.filename)
    unique_filename = f"{uuid.uuid4()}_{original_filename}"
    filepath = os.path.join(current_app.config['MEDICAL_RECORDS_FOLDER'], unique_filename)
    file.save(filepath)

    description = request.form.get('description')
    category = request.form.get('category')
    record_date_str = request.form.get('record_date')
    record_date = datetime.strptime(record_date_str, '%Y-%m-%d').date() if record_date_str else datetime.now().date()

    record = MedicalRecord(
        dog_id=dog_id,
        original_filename=original_filename,
        filename=unique_filename,
        filepath=filepath,
        description=description,
        category=category,
        record_date=record_date
    )
    db.session.add(record)
    db.session.commit()

    flash('Medical record uploaded successfully')
    return redirect(url_for('dogs.edit_dog', dog_id=dog_id))


@medical_bp.route('/edit_medical_record/<int:dog_id>/<int:record_id>', methods=['GET', 'POST'])
@login_required
def edit_medical_record(dog_id, record_id):
    """Edit a medical record."""
    if current_user.role not in ['admin', 'doctor']:
        abort(403)

    record = MedicalRecord.query.filter_by(id=record_id, dog_id=dog_id).first_or_404()

    if request.method == 'POST':
        record.description = request.form.get('description')
        record.category = request.form.get('category')

        record_date_str = request.form.get('record_date')
        record.record_date = datetime.strptime(record_date_str, '%Y-%m-%d').date() if record_date_str else None

        # Handle file replacement
        if 'record' in request.files and request.files['record'].filename:
            file = request.files['record']
            if allowed_file(file.filename):
                # Delete old file
                if os.path.exists(record.filepath):
                    os.remove(record.filepath)

                # Save new file
                original_filename = secure_filename(file.filename)
                unique_filename = f"{uuid.uuid4()}_{original_filename}"
                filepath = os.path.join(current_app.config['MEDICAL_RECORDS_FOLDER'], unique_filename)
                file.save(filepath)

                record.original_filename = original_filename
                record.filename = unique_filename
                record.filepath = filepath
            else:
                flash('Invalid file format')
                return redirect(url_for('dogs.edit_dog', dog_id=dog_id))

        db.session.commit()
        flash('Medical record updated successfully')
        return redirect(url_for('dogs.edit_dog', dog_id=dog_id))

    return render_template('edit_medical_record.html',
                           dog_id=dog_id,
                           record=record,
                           categories=MEDICAL_CATEGORIES)


@medical_bp.route('/delete_medical_record/<int:dog_id>/<int:record_id>')
@login_required
def delete_medical_record(dog_id, record_id):
    """Delete a medical record."""
    if current_user.role not in ['admin', 'doctor']:
        abort(403)

    record = MedicalRecord.query.filter_by(id=record_id, dog_id=dog_id).first_or_404()

    # Delete file from disk
    if os.path.exists(record.filepath):
        os.remove(record.filepath)

    db.session.delete(record)
    db.session.commit()

    flash('Medical record deleted')
    return redirect(url_for('dogs.edit_dog', dog_id=dog_id))


@medical_bp.route('/add_vaccination/<int:dog_id>', methods=['POST'])
@login_required
def add_vaccination(dog_id):
    """Add a vaccination record."""
    if current_user.role not in ['admin', 'doctor']:
        abort(403)

    dog = Dog.query.get_or_404(dog_id)

    vaccine_type = request.form.get('vaccine_type')
    date_administered_str = request.form.get('date_administered')
    next_due_date_str = request.form.get('next_due_date')
    notes = request.form.get('notes')
    certificate_id = request.form.get('certificate_id') or None

    if not vaccine_type or not date_administered_str:
        flash('Vaccine type and date administered are required')
        return redirect(url_for('dogs.edit_dog', dog_id=dog_id))

    date_administered = datetime.strptime(date_administered_str, '%Y-%m-%d').date()
    next_due_date = datetime.strptime(next_due_date_str, '%Y-%m-%d').date() if next_due_date_str else None

    vaccination = Vaccination(
        dog_id=dog_id,
        vaccine_type=vaccine_type,
        date_administered=date_administered,
        next_due_date=next_due_date,
        notes=notes,
        certificate_id=certificate_id
    )
    db.session.add(vaccination)
    db.session.commit()

    flash('Vaccination record added')
    return redirect(url_for('dogs.edit_dog', dog_id=dog_id))


@medical_bp.route('/edit_vaccination/<int:dog_id>/<int:vaccination_id>', methods=['GET', 'POST'])
@login_required
def edit_vaccination(dog_id, vaccination_id):
    """Edit a vaccination record."""
    if current_user.role not in ['admin', 'doctor']:
        abort(403)

    vaccination = Vaccination.query.filter_by(id=vaccination_id, dog_id=dog_id).first_or_404()
    dog = Dog.query.get_or_404(dog_id)
    medical_records = dog.medical_records.order_by(db.desc('record_date')).all()

    if request.method == 'POST':
        vaccination.vaccine_type = request.form.get('vaccine_type')

        date_administered_str = request.form.get('date_administered')
        next_due_date_str = request.form.get('next_due_date')

        vaccination.date_administered = datetime.strptime(date_administered_str, '%Y-%m-%d').date() if date_administered_str else vaccination.date_administered
        vaccination.next_due_date = datetime.strptime(next_due_date_str, '%Y-%m-%d').date() if next_due_date_str else None
        vaccination.notes = request.form.get('notes')
        vaccination.certificate_id = request.form.get('certificate_id') or None

        db.session.commit()
        flash('Vaccination record updated')
        return redirect(url_for('dogs.edit_dog', dog_id=dog_id))

    return render_template('edit_vaccination.html',
                           dog=dog,
                           vaccination=vaccination,
                           vaccine_types=VACCINE_TYPES,
                           medical_records=medical_records)


@medical_bp.route('/delete_vaccination/<int:dog_id>/<int:vaccination_id>')
@login_required
def delete_vaccination(dog_id, vaccination_id):
    """Delete a vaccination record."""
    if current_user.role not in ['admin', 'doctor']:
        abort(403)

    vaccination = Vaccination.query.filter_by(id=vaccination_id, dog_id=dog_id).first_or_404()
    db.session.delete(vaccination)
    db.session.commit()

    flash('Vaccination record deleted')
    return redirect(url_for('dogs.edit_dog', dog_id=dog_id))
