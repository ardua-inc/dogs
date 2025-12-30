"""
Image processing utilities for photo uploads.
"""
import os
from PIL import Image

# Thumbnail sizes
THUMB_SIZES = {
    'sm': (200, 200),
    'md': (400, 400),
    'lg': (800, 800),
}


def process_uploaded_image(filepath, filename, output_folder):
    """
    Process an uploaded image and generate multiple thumbnail sizes.

    Args:
        filepath: Path to the original uploaded image
        filename: The unique filename for the image
        output_folder: Folder to save thumbnails

    Returns:
        dict: Paths to generated thumbnails
    """
    thumbnails = {}

    try:
        with Image.open(filepath) as img:
            # Convert to RGB if necessary (handles PNG with transparency)
            if img.mode in ('RGBA', 'P'):
                img = img.convert('RGB')

            # Generate each thumbnail size
            for size_name, dimensions in THUMB_SIZES.items():
                thumb = img.copy()
                thumb.thumbnail(dimensions, Image.Resampling.LANCZOS)

                thumb_filename = f"thumb_{size_name}_{filename}"
                thumb_path = os.path.join(output_folder, thumb_filename)
                thumb.save(thumb_path, quality=85, optimize=True)
                thumbnails[size_name] = thumb_path

    except Exception as e:
        # Log error but don't fail the upload
        print(f"Error generating thumbnails: {e}")

    return thumbnails


def delete_photo_files(filename, folder):
    """
    Delete an image and all its thumbnails.

    Args:
        filename: The unique filename of the image
        folder: Folder containing the files
    """
    # Delete original
    original_path = os.path.join(folder, filename)
    if os.path.exists(original_path):
        os.remove(original_path)

    # Delete all thumbnail sizes
    for size_name in THUMB_SIZES.keys():
        thumb_filename = f"thumb_{size_name}_{filename}"
        thumb_path = os.path.join(folder, thumb_filename)
        if os.path.exists(thumb_path):
            os.remove(thumb_path)

    # Also delete legacy thumbnail format (thumb_filename)
    legacy_thumb = os.path.join(folder, f"thumb_{filename}")
    if os.path.exists(legacy_thumb):
        os.remove(legacy_thumb)


def get_image_dimensions(filepath):
    """
    Get the dimensions of an image.

    Args:
        filepath: Path to the image

    Returns:
        tuple: (width, height) or None if error
    """
    try:
        with Image.open(filepath) as img:
            return img.size
    except Exception:
        return None
