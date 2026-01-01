# GitHub Actions Self-Hosted Runner Guide

This guide documents how to deploy applications using the ardua-inc organization's self-hosted GitHub Actions runner on frink.ardua.lan.

## Architecture Overview

```
                                    ┌─────────────────────────────────┐
                                    │  GitHub Actions (cloud)         │
                                    │  - Runs tests                   │
                                    │  - Builds Docker images         │
                                    │  - Pushes to ghcr.io            │
                                    └───────────────┬─────────────────┘
                                                    │
                                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  frink.ardua.lan (Self-Hosted Runner)                                       │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  github-runner container                                             │   │
│  │  - Picks up deploy jobs                                              │   │
│  │  - Has access to /srv/containers (volume mount)                      │   │
│  │  - Has access to Docker socket                                       │   │
│  │  - Can SSH to remote servers                                         │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                          │                              │                   │
│                          ▼                              ▼                   │
│            ┌─────────────────────────┐      ┌─────────────────────┐        │
│            │ /srv/containers/dogs    │      │  SSH to remote      │        │
│            │ /srv/containers/app2    │      │  servers            │        │
│            │ /srv/containers/...     │      └─────────────────────┘        │
│            └─────────────────────────┘                  │                   │
└─────────────────────────────────────────────────────────┼───────────────────┘
                                                          │
                                                          ▼
                                              ┌─────────────────────┐
                                              │  books.ardua.lan    │
                                              │  other.ardua.lan    │
                                              └─────────────────────┘
```

---

## Part 1: GitHub Configuration

### 1.1 Organization Secrets

Set up secrets at the organization level so all repos can use them:

**URL:** https://github.com/organizations/ardua-inc/settings/secrets/actions

| Secret Name | Value | Purpose |
|-------------|-------|---------|
| `DEPLOY_USER` | `jramsey` | SSH username for remote deployments |
| `DEPLOY_SSH_KEY` | Contents of `/home/jramsey/.ssh/deploy_key` on frink | SSH private key for remote deployments |
| `GHCR_PAT` | GitHub PAT with `write:packages` scope | For pushing images (if not using GITHUB_TOKEN) |

### 1.2 Runner Configuration

The runner is registered at the organization level:

**URL:** https://github.com/organizations/ardua-inc/settings/actions/runners

- **Runner name:** frink-runner
- **Labels:** `self-hosted`, `linux`, `x64`, `docker`
- **Runner groups:** Default (must allow public repositories if any repos are public)

### 1.3 Package Visibility

After first build, check package settings:

**URL:** https://github.com/orgs/ardua-inc/packages

For each package:
1. Click the package name
2. Go to "Package settings"
3. Ensure visibility allows the runner to pull (public, or configure access)

---

## Part 2: Deploying Apps Hosted on frink

For applications running on frink itself (e.g., dogs), the runner can directly access the deployment directory.

### 2.1 Prerequisites on frink

```bash
# Create deployment directory
sudo mkdir -p /srv/containers/myapp/data

# Copy docker-compose.yml and .env
# (from your local machine or repo)
```

### 2.2 Workflow Template

```yaml
name: Build and Deploy

on:
  push:
    branches:
      - main

env:
  REGISTRY: ghcr.io
  IMAGE_NAME: ardua-inc/myapp

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      # ... your test steps ...

  build:
    needs: test
    runs-on: ubuntu-latest
    if: github.event_name == 'push'
    permissions:
      contents: read
      packages: write

    steps:
      - uses: actions/checkout@v4

      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v3

      - name: Log in to GitHub Container Registry
        uses: docker/login-action@v3
        with:
          registry: ${{ env.REGISTRY }}
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}

      - name: Build and push Docker image
        uses: docker/build-push-action@v5
        with:
          context: .
          push: true
          tags: |
            ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}:latest
            ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}:${{ github.sha }}
          build-args: |
            GIT_COMMIT=${{ github.sha }}

  deploy:
    needs: build
    runs-on: [self-hosted, linux]
    if: github.ref == 'refs/heads/main'
    permissions:
      packages: read

    steps:
      - name: Log in to GitHub Container Registry
        run: echo "${{ secrets.GITHUB_TOKEN }}" | docker login ghcr.io -u ${{ github.actor }} --password-stdin

      - name: Deploy to production
        run: |
          cd /srv/containers/myapp
          docker compose pull
          docker compose up -d --remove-orphans
          docker image prune -f
          echo "Deployed commit ${{ github.sha }}"
```

### 2.3 Directory Structure on frink

```
/srv/containers/myapp/
├── docker-compose.yml    # References ghcr.io/ardua-inc/myapp:latest
├── .env                  # Environment variables
├── data/                 # Persistent data (mounted volumes)
│   ├── database.db
│   └── uploads/
└── rclone/               # (optional) Backup configuration
    └── rclone.conf
```

---

## Part 3: Deploying Apps on Remote Servers

For applications running on other servers (e.g., books.ardua.lan), the runner uses SSH.

### 3.1 One-Time SSH Setup

On frink (as jramsey or the user running the runner):

```bash
# Generate deployment SSH key (if not already done)
ssh-keygen -t ed25519 -f ~/.ssh/deploy_key -N "" -C "github-actions-deploy"

# Copy public key to remote server
ssh-copy-id -i ~/.ssh/deploy_key.pub jramsey@books.ardua.lan

# Test the connection
ssh -i ~/.ssh/deploy_key jramsey@books.ardua.lan "echo 'SSH works'"
```

Add the private key to GitHub secrets:
```bash
cat ~/.ssh/deploy_key
# Copy this output to DEPLOY_SSH_KEY secret
```

### 3.2 Prerequisites on Remote Server

```bash
# Ensure deploy user can run docker
sudo usermod -aG docker jramsey

# Create deployment directory
sudo mkdir -p /opt/myapp
sudo chown jramsey:jramsey /opt/myapp

# Login to GHCR (one-time)
echo "ghp_your_pat" | docker login ghcr.io -u YOUR_GITHUB_USERNAME --password-stdin
```

### 3.3 Workflow Template

```yaml
name: Build and Deploy

on:
  push:
    branches:
      - main

env:
  REGISTRY: ghcr.io
  IMAGE_NAME: ardua-inc/myapp

jobs:
  build:
    runs-on: ubuntu-latest
    permissions:
      contents: read
      packages: write

    steps:
      - uses: actions/checkout@v4

      - name: Log in to GHCR
        uses: docker/login-action@v3
        with:
          registry: ghcr.io
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}

      - name: Build and push image
        uses: docker/build-push-action@v5
        with:
          context: .
          push: true
          build-args: |
            GIT_COMMIT=${{ github.sha }}
          tags: |
            ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}:latest
            ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}:${{ github.sha }}

  deploy:
    needs: build
    runs-on: [self-hosted]

    steps:
      - name: Setup SSH key
        run: |
          mkdir -p ~/.ssh
          echo "${{ secrets.DEPLOY_SSH_KEY }}" > ~/.ssh/deploy_key
          chmod 600 ~/.ssh/deploy_key
          ssh-keyscan -H targetserver.ardua.lan >> ~/.ssh/known_hosts

      - name: Deploy to production
        run: |
          ssh -i ~/.ssh/deploy_key -o StrictHostKeyChecking=no ${{ secrets.DEPLOY_USER }}@targetserver.ardua.lan '
            cd /opt/myapp
            docker compose pull
            docker compose up -d --remove-orphans
            docker image prune -f
            echo "Deployed successfully"
          '
```

### 3.4 For Django/Flask Apps with Migrations

Add migration commands to the deploy script:

```yaml
      - name: Deploy to production
        run: |
          ssh -i ~/.ssh/deploy_key -o StrictHostKeyChecking=no ${{ secrets.DEPLOY_USER }}@targetserver.ardua.lan '
            cd /opt/myapp
            docker compose pull
            docker compose up -d --remove-orphans
            docker image prune -f
            docker compose exec -T web python manage.py migrate
            docker compose exec -T web python manage.py collectstatic --noinput
          '
```

---

## Part 4: Adding a New Application

### Checklist for frink-hosted apps:

- [ ] Create `/srv/containers/appname/` directory on frink
- [ ] Add `docker-compose.yml` referencing `ghcr.io/ardua-inc/appname:latest`
- [ ] Add `.env` file with secrets
- [ ] Create `.github/workflows/build.yml` in repo (use Part 2 template)
- [ ] Push to main branch to trigger first build
- [ ] Check package visibility in GitHub if pull fails

### Checklist for remote-hosted apps:

- [ ] Ensure SSH key is set up (Part 3.1) - only needed once per remote server
- [ ] Add `DEPLOY_SSH_KEY` and `DEPLOY_USER` to org secrets (if not already)
- [ ] Create deployment directory on remote server
- [ ] Login to ghcr.io on remote server
- [ ] Add `docker-compose.yml` referencing `ghcr.io/ardua-inc/appname:latest`
- [ ] Add `.env` file with secrets
- [ ] Create `.github/workflows/deploy.yml` in repo (use Part 3 template)
- [ ] Push to main branch to trigger first build

---

## Part 5: Troubleshooting

### Runner not picking up jobs

```bash
ssh frink.ardua.lan
cd /srv/containers/github-runner
docker compose logs -f
docker compose restart
```

### "Waiting for runner" in GitHub Actions

1. Check runner is online: https://github.com/organizations/ardua-inc/settings/actions/runners
2. Check runner group allows the repository (especially for public repos)
3. Check workflow labels match runner labels (`self-hosted`, `linux`)

### Docker pull unauthorized

For frink-hosted apps:
- Add docker login step to workflow (uses GITHUB_TOKEN)

For remote-hosted apps:
- SSH to remote server and run: `docker login ghcr.io -u USERNAME --password-stdin`

### SSH connection refused

```bash
# Test from frink
ssh -i ~/.ssh/deploy_key -v jramsey@targetserver.ardua.lan

# Check key permissions
chmod 600 ~/.ssh/deploy_key

# Verify public key is in authorized_keys on target
ssh targetserver.ardua.lan "cat ~/.ssh/authorized_keys"
```

### Deploy directory not found

The runner container must have `/srv/containers` mounted. Check:
```bash
cd /srv/containers/github-runner
cat docker-compose.yml | grep -A5 volumes
```

Should include:
```yaml
volumes:
  - /srv/containers:/srv/containers
```

---

## Part 6: Runner Maintenance

### Updating the runner

```bash
ssh frink.ardua.lan
cd /srv/containers/github-runner
docker compose pull
docker compose down
docker compose up -d
```

### Viewing runner logs

```bash
docker compose logs -f
```

### Runner configuration

Location: `/srv/containers/github-runner/`

```
├── docker-compose.yml
├── .env                  # Contains GITHUB_PAT
```

The PAT in `.env` needs these scopes:
- `repo` (full control of private repositories)
- `admin:org` → `manage_runners:org`
