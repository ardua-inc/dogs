# Dogs App Deployment Guide

This guide covers deploying the Dogs app to frink.ardua.lan with NGINX on sideshowbob.

## Architecture

```
Internet → sideshowbob (NGINX + SSL) → frink.ardua.lan:8001 (Docker)
                                              ↓
                                    ┌─────────────────┐
                                    │  dogs-web:8000  │
                                    │  dogs-backup    │
                                    │  (SQLite + S3)  │
                                    └─────────────────┘
```

## Prerequisites

- Docker on frink (already installed: v29.1.3)
- NGINX on sideshowbob
- GitHub org-level runner on frink (ardua-inc)

---

## Part 1: GitHub Runner Setup (Already Complete)

The containerized GitHub runner is already configured at `/srv/containers/github-runner` on frink, registered with the ardua-inc organization.

To verify: https://github.com/organizations/ardua-inc/settings/actions/runners

---

## Part 2: Set up GHCR Authentication on frink

The runner needs to pull images from ghcr.io/ardua-inc.

```bash
ssh frink.ardua.lan

# Login to GitHub Container Registry
# Use your GitHub username and a PAT with read:packages scope
echo "ghp_your_token" | docker login ghcr.io -u YOUR_GITHUB_USERNAME --password-stdin
```

---

## Part 3: Deploy Dogs Application

### Step 1: Create directory structure on frink

```bash
ssh frink.ardua.lan

sudo mkdir -p /srv/containers/dogs/data/uploads/dog_photos
sudo mkdir -p /srv/containers/dogs/data/uploads/medical_records
sudo mkdir -p /srv/containers/dogs/rclone
```

### Step 2: Copy deployment files

From your local machine:
```bash
cd /Users/jramsey/Documents/Code/dogs/Dogs

# Copy docker-compose.yml
scp deploy/frink/docker-compose.yml frink.ardua.lan:/srv/containers/dogs/

# Copy .env.example
scp deploy/frink/.env.example frink.ardua.lan:/srv/containers/dogs/.env

# Copy rclone config example
scp deploy/frink/rclone/rclone.conf.example frink.ardua.lan:/srv/containers/dogs/rclone/rclone.conf
```

### Step 3: Configure environment on frink

```bash
ssh frink.ardua.lan
cd /srv/containers/dogs

# Edit .env with real values
nano .env
```

Generate the Flask secret key:
```bash
python3 -c "import secrets; print(secrets.token_hex(32))"
```

Update `.env`:
```
FLASK_SECRET_KEY=<generated-key>
S3_BUCKET=your-backup-bucket
```

### Step 4: Configure S3 backup

Edit the rclone config with your S3/B2 credentials:
```bash
nano /srv/containers/dogs/rclone/rclone.conf
```

### Step 5: Copy existing data

From your dev machine:
```bash
# Copy the SQLite database
scp /Users/jramsey/Documents/Code/dogs/Dogs/dogs.db frink.ardua.lan:/srv/containers/dogs/data/

# Copy existing uploads
scp -r /Users/jramsey/Documents/Code/dogs/Dogs/uploads/* frink.ardua.lan:/srv/containers/dogs/data/uploads/
```

### Step 6: Initial deployment (manual first time)

```bash
ssh frink.ardua.lan
cd /srv/containers/dogs

# Pull and start
docker compose pull
docker compose up -d

# Check logs
docker compose logs -f web
```

### Step 7: Run database migrations

```bash
docker compose exec web flask db upgrade
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
# Comment out lines 17-47 (the ssl server block)

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

After setup, deployment is automatic:

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

# View backup logs
docker compose logs -f backup

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

# Manual backup trigger
docker compose exec backup rclone sync /data s3:your-bucket/dogs --config /config/rclone/rclone.conf
```

---

## Backup & Recovery

### Automatic backups

The backup container syncs `/srv/containers/dogs/data/` to S3 every 6 hours. This includes:
- `dogs.db` - SQLite database
- `uploads/` - Dog photos and medical records

### Manual backup

```bash
docker compose exec backup rclone sync /data s3:your-bucket/dogs --config /config/rclone/rclone.conf
```

### Restore from backup

```bash
# Stop the app
docker compose stop web

# Sync from S3
docker compose exec backup rclone sync s3:your-bucket/dogs /data --config /config/rclone/rclone.conf

# Start the app
docker compose start web
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
echo "ghp_your_token" | docker login ghcr.io -u YOUR_GITHUB_USERNAME --password-stdin
```

### Database issues

```bash
# Check if database exists
docker compose exec web ls -la /app/data/

# Run migrations
docker compose exec web flask db upgrade

# Open SQLite shell
docker compose exec web sqlite3 /app/data/dogs.db
```

### Backup not working

```bash
# Check backup logs
docker compose logs backup

# Test rclone config
docker compose exec backup rclone lsd s3: --config /config/rclone/rclone.conf
```
