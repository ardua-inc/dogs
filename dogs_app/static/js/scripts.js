/**
 * Lightbox functionality for photo galleries
 */

let currentImageIndex = 0;

function openLightbox(index) {
    currentImageIndex = index;
    const lightbox = document.getElementById('lightbox');
    const lightboxImg = document.getElementById('lightbox-img');
    const lightboxCaption = document.getElementById('lightbox-caption');

    if (lightbox && lightboxImg && typeof photos !== 'undefined' && photos.length > 0) {
        const photo = photos[index];
        lightboxImg.src = photo.url || photo;
        if (lightboxCaption) {
            lightboxCaption.textContent = photo.caption || '';
        }
        lightbox.style.display = 'flex';
        document.body.style.overflow = 'hidden';
    }
}

function closeLightbox() {
    const lightbox = document.getElementById('lightbox');
    if (lightbox) {
        lightbox.style.display = 'none';
        document.body.style.overflow = '';
    }
}

function changeImage(direction) {
    if (typeof photos === 'undefined' || photos.length === 0) return;

    currentImageIndex += direction;

    if (currentImageIndex >= photos.length) {
        currentImageIndex = 0;
    } else if (currentImageIndex < 0) {
        currentImageIndex = photos.length - 1;
    }

    const lightboxImg = document.getElementById('lightbox-img');
    const lightboxCaption = document.getElementById('lightbox-caption');
    const photo = photos[currentImageIndex];

    if (lightboxImg) {
        lightboxImg.src = photo.url || photo;
    }
    if (lightboxCaption) {
        lightboxCaption.textContent = photo.caption || '';
    }
}

// Keyboard navigation for lightbox
document.addEventListener('keydown', function(e) {
    const lightbox = document.getElementById('lightbox');
    if (lightbox && lightbox.style.display === 'flex') {
        switch(e.key) {
            case 'ArrowLeft':
                changeImage(-1);
                break;
            case 'ArrowRight':
                changeImage(1);
                break;
            case 'Escape':
                closeLightbox();
                break;
        }
    }
});

// Close lightbox when clicking outside the image
document.addEventListener('click', function(e) {
    const lightbox = document.getElementById('lightbox');
    if (lightbox && e.target === lightbox) {
        closeLightbox();
    }
});

// Drag and drop reordering for photo gallery
document.addEventListener('DOMContentLoaded', function() {
    const gallery = document.getElementById('photo-gallery');
    if (gallery && gallery.classList.contains('sortable')) {
        initDragAndDrop(gallery);
    }
});

function initDragAndDrop(gallery) {
    let draggedItem = null;

    gallery.querySelectorAll('.photo').forEach(photo => {
        photo.setAttribute('draggable', 'true');

        photo.addEventListener('dragstart', function(e) {
            draggedItem = this;
            this.style.opacity = '0.5';
            e.dataTransfer.effectAllowed = 'move';
        });

        photo.addEventListener('dragend', function() {
            this.style.opacity = '1';
            draggedItem = null;

            // Save new order
            savePhotoOrder(gallery);
        });

        photo.addEventListener('dragover', function(e) {
            e.preventDefault();
            e.dataTransfer.dropEffect = 'move';
        });

        photo.addEventListener('dragenter', function(e) {
            e.preventDefault();
            if (this !== draggedItem) {
                this.style.borderLeft = '3px solid #007bff';
            }
        });

        photo.addEventListener('dragleave', function() {
            this.style.borderLeft = '';
        });

        photo.addEventListener('drop', function(e) {
            e.preventDefault();
            this.style.borderLeft = '';

            if (this !== draggedItem) {
                const allPhotos = Array.from(gallery.querySelectorAll('.photo'));
                const draggedIndex = allPhotos.indexOf(draggedItem);
                const dropIndex = allPhotos.indexOf(this);

                if (draggedIndex < dropIndex) {
                    this.parentNode.insertBefore(draggedItem, this.nextSibling);
                } else {
                    this.parentNode.insertBefore(draggedItem, this);
                }
            }
        });
    });
}

function savePhotoOrder(gallery) {
    const dogId = gallery.dataset.dogId;
    const photoIds = Array.from(gallery.querySelectorAll('.photo')).map(
        photo => parseInt(photo.dataset.photoId)
    );

    fetch(`/reorder_photos/${dogId}`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ order: photoIds })
    })
    .then(response => response.json())
    .then(data => {
        if (!data.success) {
            console.error('Failed to save photo order');
        }
    })
    .catch(error => {
        console.error('Error saving photo order:', error);
    });
}
