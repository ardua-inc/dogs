#!/usr/bin/env python3
"""
Migrate data from SQLite (dogs.db) to PostgreSQL.

Usage:
    1. Copy dogs.db to /srv/containers/dogs/data/
    2. Run: docker compose exec web python /app/deploy/frink/migrate_sqlite_to_postgres.py

Or run standalone with proper environment variables set.
"""
import os
import sqlite3
from datetime import datetime

# Try to import from the app context, fall back to standalone
try:
    from dogs_app import create_app, db
    from dogs_app.models import User, Dog, DogPhoto, MedicalRecord, Vaccination
    app = create_app()
except ImportError:
    print("Run this script from within the Docker container:")
    print("  docker compose exec web python migrate_sqlite_to_postgres.py")
    exit(1)


def migrate_data(sqlite_path='/app/data/dogs.db'):
    """Migrate all data from SQLite to PostgreSQL."""

    if not os.path.exists(sqlite_path):
        print(f"SQLite database not found at {sqlite_path}")
        print("Copy your dogs.db file to /srv/containers/dogs/data/dogs.db on the host")
        return False

    # Connect to SQLite
    sqlite_conn = sqlite3.connect(sqlite_path)
    sqlite_conn.row_factory = sqlite3.Row
    cursor = sqlite_conn.cursor()

    with app.app_context():
        # Check if PostgreSQL already has data
        if User.query.first():
            print("PostgreSQL database already has data!")
            response = input("Do you want to clear it and re-migrate? (yes/no): ")
            if response.lower() != 'yes':
                print("Migration cancelled.")
                return False

            # Clear existing data (order matters due to foreign keys)
            Vaccination.query.delete()
            MedicalRecord.query.delete()
            DogPhoto.query.delete()
            Dog.query.delete()
            User.query.delete()
            db.session.commit()
            print("Cleared existing PostgreSQL data.")

        # Migrate Users
        print("Migrating users...")
        cursor.execute("SELECT * FROM users")
        for row in cursor.fetchall():
            user = User(
                id=row['id'],
                username=row['username'],
                password_hash=row['password_hash'],
                role=row['role'],
                full_name=row['full_name'] if 'full_name' in row.keys() else None,
                email=row['email'] if 'email' in row.keys() else None,
                is_active=bool(row['is_active']) if 'is_active' in row.keys() else True
            )
            db.session.add(user)
        db.session.commit()
        print(f"  Migrated {User.query.count()} users")

        # Migrate Dogs
        print("Migrating dogs...")
        cursor.execute("SELECT * FROM dogs")
        for row in cursor.fetchall():
            dog = Dog(
                id=row['id'],
                name=row['name'],
                breed=row['breed'] if 'breed' in row.keys() else None,
                birthdate=parse_date(row['birthdate']) if row['birthdate'] else None,
                deathdate=parse_date(row['deathdate']) if row['deathdate'] else None,
                status=row['status'] if 'status' in row.keys() else 'Living',
                microchip_company=row['microchip_company'] if 'microchip_company' in row.keys() else None,
                microchip_id=row['microchip_id'] if 'microchip_id' in row.keys() else None
            )
            db.session.add(dog)
        db.session.commit()
        print(f"  Migrated {Dog.query.count()} dogs")

        # Migrate Dog Photos
        print("Migrating photos...")
        cursor.execute("SELECT * FROM dog_photos")
        for row in cursor.fetchall():
            photo = DogPhoto(
                id=row['id'],
                dog_id=row['dog_id'],
                original_filename=row['original_filename'] if 'original_filename' in row.keys() else None,
                filename=row['filename'],
                filepath=row['filepath'],
                is_primary=bool(row['is_primary']) if 'is_primary' in row.keys() else False,
                caption=row['caption'] if 'caption' in row.keys() else None,
                taken_date=parse_date(row['taken_date']) if 'taken_date' in row.keys() and row['taken_date'] else None,
                sort_order=row['sort_order'] if 'sort_order' in row.keys() else 0
            )
            db.session.add(photo)
        db.session.commit()
        print(f"  Migrated {DogPhoto.query.count()} photos")

        # Migrate Medical Records
        print("Migrating medical records...")
        cursor.execute("SELECT * FROM medical_records")
        for row in cursor.fetchall():
            record = MedicalRecord(
                id=row['id'],
                dog_id=row['dog_id'],
                original_filename=row['original_filename'] if 'original_filename' in row.keys() else None,
                filename=row['filename'],
                filepath=row['filepath'],
                description=row['description'] if 'description' in row.keys() else None,
                category=row['category'] if 'category' in row.keys() else None,
                record_date=parse_date(row['record_date']) if row['record_date'] else None
            )
            db.session.add(record)
        db.session.commit()
        print(f"  Migrated {MedicalRecord.query.count()} medical records")

        # Migrate Vaccinations
        print("Migrating vaccinations...")
        cursor.execute("SELECT * FROM vaccinations")
        for row in cursor.fetchall():
            vaccination = Vaccination(
                id=row['id'],
                dog_id=row['dog_id'],
                vaccine_type=row['vaccine_type'],
                date_administered=parse_date(row['date_administered']),
                next_due_date=parse_date(row['next_due_date']) if row['next_due_date'] else None,
                notes=row['notes'] if 'notes' in row.keys() else None,
                certificate_id=row['certificate_id'] if 'certificate_id' in row.keys() else None
            )
            db.session.add(vaccination)
        db.session.commit()
        print(f"  Migrated {Vaccination.query.count()} vaccinations")

        # Reset sequences for PostgreSQL
        print("Resetting PostgreSQL sequences...")
        tables = ['users', 'dogs', 'dog_photos', 'medical_records', 'vaccinations']
        for table in tables:
            db.session.execute(db.text(
                f"SELECT setval('{table}_id_seq', (SELECT COALESCE(MAX(id), 0) + 1 FROM {table}), false)"
            ))
        db.session.commit()

        print("\nMigration completed successfully!")
        return True

    sqlite_conn.close()


def parse_date(date_str):
    """Parse date string to date object."""
    if not date_str:
        return None
    try:
        # Try common formats
        for fmt in ['%Y-%m-%d', '%Y-%m-%d %H:%M:%S', '%d/%m/%Y']:
            try:
                return datetime.strptime(str(date_str), fmt).date()
            except ValueError:
                continue
        return None
    except Exception:
        return None


if __name__ == '__main__':
    import sys
    sqlite_path = sys.argv[1] if len(sys.argv) > 1 else '/app/data/dogs.db'
    migrate_data(sqlite_path)
