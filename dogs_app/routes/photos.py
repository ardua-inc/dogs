"""
Photo management routes: upload, delete, reorder, slideshow.
"""
import os
import random
import uuid
from datetime import datetime
from flask import Blueprint, render_template, redirect, url_for, flash, request, abort, jsonify, current_app, send_from_directory
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from dogs_app.models import Dog, DogPhoto
from dogs_app import db
from dogs_app.utils.images import process_uploaded_image, delete_photo_files

photos_bp = Blueprint('photos', __name__)


def allowed_file(filename):
    """Check if file extension is allowed."""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in current_app.config['ALLOWED_IMAGE_EXTENSIONS']


@photos_bp.route('/upload_photo/<int:dog_id>', methods=['POST'])
@login_required
def upload_photo(dog_id):
    """Upload one or more photos for a dog."""
    if current_user.role not in ['admin', 'doctor']:
        abort(403)

    dog = Dog.query.get_or_404(dog_id)

    if 'photos' not in request.files and 'photo' not in request.files:
        flash('No file selected')
        return redirect(url_for('dogs.edit_dog', dog_id=dog_id))

    # Support both single 'photo' and multiple 'photos' field names
    files = request.files.getlist('photos') or [request.files.get('photo')]
    files = [f for f in files if f and f.filename]

    if not files:
        flash('No file selected')
        return redirect(url_for('dogs.edit_dog', dog_id=dog_id))

    # Get current photo count to determine if first upload
    existing_count = dog.photos.count()
    # Get max sort order
    max_order = db.session.query(db.func.max(DogPhoto.sort_order)).filter_by(dog_id=dog_id).scalar() or 0

    uploaded_count = 0
    for file in files:
        if file and allowed_file(file.filename):
            original_filename = secure_filename(file.filename)
            unique_filename = f"{uuid.uuid4()}_{original_filename}"
            filepath = os.path.join(current_app.config['DOG_PHOTOS_FOLDER'], unique_filename)

            # Save original and generate thumbnails
            file.save(filepath)
            process_uploaded_image(filepath, unique_filename, current_app.config['DOG_PHOTOS_FOLDER'])

            # Determine if this should be primary (first photo)
            is_primary = (existing_count == 0 and uploaded_count == 0)

            # Get caption and date from form if provided
            caption = request.form.get('caption')
            taken_date_str = request.form.get('taken_date')
            taken_date = datetime.strptime(taken_date_str, '%Y-%m-%d').date() if taken_date_str else None

            max_order += 1
            photo = DogPhoto(
                dog_id=dog_id,
                original_filename=original_filename,
                filename=unique_filename,
                filepath=filepath,
                is_primary=is_primary,
                caption=caption,
                taken_date=taken_date,
                sort_order=max_order
            )
            db.session.add(photo)
            uploaded_count += 1
        else:
            flash(f'Invalid file format: {file.filename}')

    if uploaded_count > 0:
        db.session.commit()
        flash(f'{uploaded_count} photo(s) uploaded successfully')

    return redirect(url_for('dogs.edit_dog', dog_id=dog_id))


@photos_bp.route('/set_primary_photo/<int:dog_id>/<int:photo_id>')
@login_required
def set_primary_photo(dog_id, photo_id):
    """Set a photo as the primary photo for a dog."""
    if current_user.role not in ['admin', 'doctor']:
        abort(403)

    # Unset all primary photos for this dog
    DogPhoto.query.filter_by(dog_id=dog_id).update({'is_primary': False})
    # Set the selected photo as primary
    photo = DogPhoto.query.filter_by(id=photo_id, dog_id=dog_id).first_or_404()
    photo.is_primary = True
    db.session.commit()

    flash('Primary photo updated')
    return redirect(url_for('dogs.edit_dog', dog_id=dog_id))


@photos_bp.route('/delete_photo/<int:dog_id>/<int:photo_id>')
@login_required
def delete_photo(dog_id, photo_id):
    """Delete a photo."""
    if current_user.role not in ['admin', 'doctor']:
        abort(403)

    photo = DogPhoto.query.filter_by(id=photo_id, dog_id=dog_id).first_or_404()

    # Delete files from disk
    delete_photo_files(photo.filename, current_app.config['DOG_PHOTOS_FOLDER'])

    db.session.delete(photo)
    db.session.commit()

    flash('Photo deleted')
    return redirect(url_for('dogs.edit_dog', dog_id=dog_id))


@photos_bp.route('/update_photo/<int:photo_id>', methods=['POST'])
@login_required
def update_photo(photo_id):
    """Update photo caption and date."""
    if current_user.role not in ['admin', 'doctor']:
        abort(403)

    photo = DogPhoto.query.get_or_404(photo_id)
    photo.caption = request.form.get('caption')

    taken_date_str = request.form.get('taken_date')
    photo.taken_date = datetime.strptime(taken_date_str, '%Y-%m-%d').date() if taken_date_str else None

    db.session.commit()
    flash('Photo updated')
    return redirect(url_for('dogs.edit_dog', dog_id=photo.dog_id))


@photos_bp.route('/reorder_photos/<int:dog_id>', methods=['POST'])
@login_required
def reorder_photos(dog_id):
    """Reorder photos via AJAX."""
    if current_user.role not in ['admin', 'doctor']:
        return jsonify({'error': 'Forbidden'}), 403

    data = request.get_json()
    if not data or 'order' not in data:
        return jsonify({'error': 'Invalid data'}), 400

    for index, photo_id in enumerate(data['order']):
        photo = DogPhoto.query.filter_by(id=photo_id, dog_id=dog_id).first()
        if photo:
            photo.sort_order = index

    db.session.commit()
    return jsonify({'success': True})


@photos_bp.route('/api/dog/<int:dog_id>/photos')
@login_required
def api_dog_photos(dog_id):
    """JSON endpoint for dog photos (used by slideshow)."""
    dog = Dog.query.get_or_404(dog_id)
    photos = dog.photos.order_by('sort_order', 'upload_date').all()
    return jsonify({
        'dog': {'id': dog.id, 'name': dog.name},
        'photos': [photo.to_dict() for photo in photos]
    })


@photos_bp.route('/dog/<int:dog_id>/slideshow')
@login_required
def dog_slideshow(dog_id):
    """Slideshow view for a single dog."""
    dog = Dog.query.get_or_404(dog_id)
    photos = dog.photos.order_by('sort_order', 'upload_date').all()
    return render_template('slideshow.html', dog=dog, photos=photos, mode='dog')


@photos_bp.route('/slideshow')
@login_required
def all_slideshow():
    """Slideshow view for all dogs."""
    # Get all photos from all dogs in random order
    photos = DogPhoto.query.all()
    random.shuffle(photos)
    return render_template('slideshow.html', photos=photos, mode='all')


@photos_bp.route('/uploads/<path:filename>')
@login_required
def uploaded_file(filename):
    """Serve uploaded files."""
    return send_from_directory(current_app.config['UPLOAD_FOLDER'], filename)
