# Comanche Dogs

A Flask web application for managing dog records, photos, medical records, and vaccination schedules.

## Versioning

The version is defined once, as `__version__` in `dogs_app/__init__.py`, and
displayed on the About page (clicking it opens the changelog). On every merge to
`main`:

1. Bump the patch number (`2.0.2` → `2.0.3`); minor/major bumps are deliberate
2. Add a matching `## [x.y.z] - YYYY-MM-DD` entry at the top of `CHANGELOG.md`
3. Tag the merge commit: `git tag vx.y.z && git push --tags`

`tests/test_changelog.py` fails if the newest changelog entry doesn't match
`__version__`.

## License
MIT License © 2026 Ardua, Inc.

## Features

- **Dog Management**: Track dogs with photos, breed, birthdate, microchip info, and status
- **Photo Gallery**: Upload multiple photos with automatic thumbnail generation, slideshow mode
- **Medical Records**: Upload and organize veterinary documents by category
- **Vaccination Tracking**: Record vaccinations with due date reminders
- **User Management**: Role-based access (admin, doctor, viewer)

## Quick Start (Development)

```bash
# Clone and setup
git clone git@github.com:ardua-inc/dogs.git
cd dogs

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run development server
FLASK_APP=wsgi:app FLASK_DEBUG=1 flask run --port 5001
```

Access at http://localhost:5001 (default login: `admin` / `admin123`)

## Project Structure

```
Dogs/
├── dogs_app/                 # Flask application package
│   ├── __init__.py           # Application factory
│   ├── config.py             # Configuration classes
│   ├── models.py             # SQLAlchemy models
│   ├── routes/               # Blueprint routes
│   │   ├── auth.py           # Login, logout, password
│   │   ├── dogs.py           # Dog CRUD
│   │   ├── photos.py         # Photo management, slideshow
│   │   ├── medical.py        # Medical records
│   │   ├── admin.py          # User management
│   │   └── about.py          # About page and changelog view
│   ├── templates/            # Jinja2 templates
│   ├── static/               # CSS, JS, images
│   └── utils/                # Image processing, changelog parsing
├── migrations/               # Flask-Migrate database migrations
├── tests/                    # pytest test suite
├── deploy/                   # Deployment configurations
│   ├── frink/                # Docker config for frink server
│   ├── sideshowbob/          # Nginx config
│   └── RUNNER_GUIDE.md       # CI/CD documentation
├── .github/workflows/        # GitHub Actions CI/CD
├── CHANGELOG.md              # Release history (shown in the app)
├── Dockerfile                # Container build
├── wsgi.py                   # WSGI entry point
├── gunicorn.conf.py          # Gunicorn configuration
├── requirements.txt          # Python dependencies
└── DEPLOYMENT.md             # Production deployment guide
```

## Configuration

The app uses environment variables (via `.env` file):

```bash
# Required
FLASK_SECRET_KEY=your-secret-key-here

# Optional
FLASK_DEBUG=False
FLASK_ENV=production
BASE_DATA_PATH=/app/data
```

Generate a secret key:
```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

## Database

Uses SQLite by default. Database file location:
- Development: `./dogs.db`
- Production: `/app/data/dogs.db` (inside container)

Run migrations:
```bash
FLASK_APP=wsgi:app flask db upgrade
```

## Production Deployment

The app deploys via Docker to `frink.ardua.lan` with nginx on `sideshowbob.ardua.lan`.

See [DEPLOYMENT.md](DEPLOYMENT.md) for full instructions.

### Quick Deploy

Push to `main` branch triggers automatic deployment:
1. GitHub Actions runs tests
2. Builds Docker image → `ghcr.io/ardua-inc/dogs:latest`
3. Self-hosted runner on frink pulls and restarts containers

### Manual Deploy

```bash
ssh frink.ardua.lan
cd /srv/containers/dogs
docker compose pull
docker compose up -d
```

## Testing

```bash
# Run all tests
pytest tests/ -v

# With coverage
pytest tests/ -v --cov=dogs_app --cov-report=term-missing
```

## User Roles

| Role | Permissions |
|------|-------------|
| admin | Full access: manage users, dogs, photos, records |
| doctor | Edit dogs, photos, medical records, vaccinations |
| viewer | Read-only access to all data |

## API Routes

| Route | Description |
|-------|-------------|
| `/` | Homepage - dog grid with status |
| `/dog/<id>` | Dog detail page |
| `/dog/<id>/edit` | Edit dog (admin/doctor) |
| `/dog/<id>/slideshow` | Photo slideshow |
| `/slideshow` | All dogs slideshow (random) |
| `/about` | Version info (version links to changelog) |
| `/about/changelog` | Release history from CHANGELOG.md |
| `/login`, `/logout` | Authentication |
| `/manage_users` | User admin (admin only) |

## Versioning

The version is defined once, as `__version__` in `dogs_app/__init__.py`, and
displayed on the About page (clicking it opens the changelog). On every merge to
`main`:

1. Bump the patch number (`2.0.2` → `2.0.3`); minor/major bumps are deliberate
2. Add a matching `## [x.y.z] - YYYY-MM-DD` entry at the top of `CHANGELOG.md`
3. Tag the merge commit: `git tag vx.y.z && git push --tags`

`tests/test_changelog.py` fails if the newest changelog entry doesn't match
`__version__`.

## License

MIT License
