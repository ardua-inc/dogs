# Dogs App Deployment Guide

This guide covers deploying the Dogs app to frink.ardua.lan with NGINX on sideshowbob.

## Architecture

```
Internet → sideshowbob (NGINX + SSL) → frink.ardua.lan:8001 (Docker)
                                              ↓
                                    ┌─────────────────┐
                                    │  dogs-web:8000  │
                                    │  dogs-db:5432   │
                                    │  dogs-backup    │
                                    └─────────────────┘
```

## Prerequisites

- Docker on frink (already installed: v29.1.3)
- NGINX on sideshowbob
- GitHub org-level runner on frink

---

## Part 1: Move GitHub Runner from books to frink

### Step 1: Remove runner from books

```bash
# SSH to books.ardua.lan
ssh books.ardua.lan

# Find and stop the runner
cd /path/to/actions-runner  # wherever it's installed
sudo ./svc.sh stop
sudo ./svc.sh uninstall
./config.sh remove --token <REMOVE_TOKEN>
```

To get the remove token:
1. Go to https://github.com/organizations/jimatardua/settings/actions/runners
2. Click on the runner → "Remove" → Copy the token

### Step 2: Set up runner on frink (containerized)

```bash
# SSH to frink.ardua.lan
ssh frink.ardua.lan

# Create runner directory
sudo mkdir -p /srv/containers/github-runner
cd /srv/containers/github-runner

# Create docker-compose.yml
cat > docker-compose.yml << 'EOF'
version: '3.8'

services:
  runner:
    image: myoung34/github-runner:latest
    container_name: github-runner
    restart: unless-stopped
    environment:
      - RUNNER_NAME=frink-runner
      - RUNNER_SCOPE=org
      - ORG_NAME=jimatardua
      - ACCESS_TOKEN=${GITHUB_PAT}
      - RUNNER_WORKDIR=/tmp/runner/work
      - LABELS=self-hosted,linux,x64,docker
      - DISABLE_AUTO_UPDATE=false
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock
      - runner-work:/tmp/runner/work
    security_opt:
      - label:disable

volumes:
  runner-work:
EOF

# Create .env file with your GitHub PAT
cat > .env << 'EOF'
GITHUB_PAT=ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
EOF
chmod 600 .env
```

### Step 3: Create GitHub Personal Access Token

1. Go to https://github.com/settings/tokens
2. Generate new token (classic)
3. Select scopes:
   - `repo` (full control of private repositories)
   - `admin:org` → `manage_runners:org`
4. Copy the token to `/srv/containers/github-runner/.env`

### Step 4: Start the runner

```bash
cd /srv/containers/github-runner
docker compose up -d
docker compose logs -f  # Watch for successful registration
```

### Step 5: Verify runner is registered

Go to https://github.com/organizations/jimatardua/settings/actions/runners

You should see "frink-runner" with status "Idle".

---

## Part 2: Set up GHCR Authentication on frink

The runner needs to pull images from ghcr.io/jimatardua.

```bash
# SSH to frink
ssh frink.ardua.lan

# Login to GitHub Container Registry
# Use your GitHub username and a PAT with read:packages scope
echo "ghp_your_token" | docker login ghcr.io -u jimatardua --password-stdin
```

This saves credentials to `~/.docker/config.json` which Docker will use for pulls.

---

## Part 3: Deploy Dogs Application

### Step 1: Create directory structure on frink

```bash
ssh frink.ardua.lan

sudo mkdir -p /srv/containers/dogs/data/uploads/dog_photos
sudo mkdir -p /srv/containers/dogs/data/uploads/medical_records
sudo mkdir -p /srv/containers/dogs/data/postgres
sudo mkdir -p /srv/containers/dogs/data/backups
```

### Step 2: Copy deployment files

From your local machine:
```bash
cd /Users/jramsey/Documents/Code/dogs/Dogs

# Copy docker-compose.yml
scp deploy/frink/docker-compose.yml frink.ardua.lan:/srv/containers/dogs/

# Copy .env.example and create .env
scp deploy/frink/.env.example frink.ardua.lan:/srv/containers/dogs/
```

### Step 3: Configure environment on frink

```bash
ssh frink.ardua.lan
cd /srv/containers/dogs

# Create .env from example
cp .env.example .env

# Edit with real values
nano .env
```

Generate secrets:
```bash
# Generate FLASK_SECRET_KEY
python3 -c "import secrets; print(secrets.token_hex(32))"

# Generate POSTGRES_PASSWORD
python3 -c "import secrets; print(secrets.token_urlsafe(24))"
```

### Step 4: Copy existing data

From your dev machine:
```bash
# Copy the SQLite database (for migration)
scp /Users/jramsey/Documents/Code/dogs/Dogs/dogs.db frink.ardua.lan:/srv/containers/dogs/data/

# Copy existing uploads
scp -r /Users/jramsey/Documents/Code/dogs/Dogs/uploads/* frink.ardua.lan:/srv/containers/dogs/data/uploads/
```

### Step 5: Initial deployment (manual first time)

```bash
ssh frink.ardua.lan
cd /srv/containers/dogs

# Pull and start
docker compose pull
docker compose up -d

# Check logs
docker compose logs -f web
```

### Step 6: Run database migrations

```bash
docker compose exec web flask db upgrade
```

### Step 7: Migrate data from SQLite to PostgreSQL

```bash
# Copy the migration script into the container
docker compose cp /srv/containers/dogs/data/dogs.db web:/app/data/dogs.db

# Run migration
docker compose exec web python deploy/frink/migrate_sqlite_to_postgres.py
```

---

## Part 4: Configure NGINX on sideshowbob

### Step 1: Copy nginx config

```bash
# From your local machine
scp deploy/sideshowbob/dogs.ardua.com sideshowbob.ardua.lan:/tmp/

# SSH to sideshowbob
ssh sideshowbob.ardua.lan

# Move to nginx sites
sudo mv /tmp/dogs.ardua.com /etc/nginx/sites-available/
sudo ln -s /etc/nginx/sites-available/dogs.ardua.com /etc/nginx/sites-enabled/

# Test config
sudo nginx -t
```

### Step 2: Get SSL certificate

```bash
# First, temporarily comment out the SSL server block
sudo nano /etc/nginx/sites-available/dogs.ardua.com
# Comment out lines 14-44 (the ssl server block)

# Reload nginx with just HTTP
sudo systemctl reload nginx

# Get certificate
sudo certbot --nginx -d dogs.ardua.com

# Certbot will update the config with SSL settings
```

### Step 3: Verify

Visit https://dogs.ardua.com - you should see the login page.

---

## Part 5: CI/CD Flow

After setup, the deployment is automatic:

1. Push code to `main` branch
2. GitHub Actions runs tests on GitHub-hosted runner
3. GitHub Actions builds Docker image and pushes to ghcr.io
4. Deploy job runs on frink-runner (self-hosted)
5. frink pulls new image and restarts containers

### Manual deployment (if needed)

```bash
ssh frink.ardua.lan
cd /srv/containers/dogs
docker compose pull
docker compose up -d
```

---

## Useful Commands

```bash
# View app logs
docker compose logs -f web

# View all logs
docker compose logs -f

# Restart app
docker compose restart web

# Run Flask shell
docker compose exec web flask shell

# Run database migration
docker compose exec web flask db upgrade

# View runner logs
cd /srv/containers/github-runner && docker compose logs -f

# Check disk usage
docker system df
```

---

## Backup & Recovery

### Database backups

Automatic daily backups are stored in `/srv/containers/dogs/data/backups/`

```bash
# List backups
ls -la /srv/containers/dogs/data/backups/

# Restore from backup
gunzip < /srv/containers/dogs/data/backups/dogs-YYYYMMDD-HHMMSS.sql.gz | \
  docker compose exec -T db psql -U dogs -d dogs
```

### Uploads backup

Consider adding rclone to sync uploads to S3/B2:
```bash
# Add to crontab
0 3 * * * rclone sync /srv/containers/dogs/data/uploads s3:dogs-backups/uploads
```

---

## Troubleshooting

### Runner not picking up jobs

```bash
cd /srv/containers/github-runner
docker compose logs -f
docker compose restart
```

### App not starting

```bash
cd /srv/containers/dogs
docker compose logs web
docker compose exec web flask db upgrade  # Ensure migrations ran
```

### Can't pull from ghcr.io

```bash
# Re-authenticate
echo "ghp_your_token" | docker login ghcr.io -u jimatardua --password-stdin
```

### Database connection issues

```bash
# Check if postgres is healthy
docker compose ps
docker compose logs db

# Connect to postgres directly
docker compose exec db psql -U dogs -d dogs
```
