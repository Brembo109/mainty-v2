# mainty

GMP-compliant maintenance management system built with Django 5.1.

**Stack:** Django 5.1 · PostgreSQL 16 · HTMX · Tailwind CSS · Docker

---

## Features

- **Role-based access control** — Admin / User / Viewer via Django Groups
- **Brute-force protection** — django-axes (5 failed attempts → 15 min lockout)
- **Password rotation** — mandatory change after 90 days (configurable)
- **GMP audit trail** — automatic logging of all model changes + login/logout events, exportable as CSV/XLSX
- **Bilingual UI** — German (default) and English via Django i18n

---

## Requirements

- [Docker](https://docs.docker.com/get-docker/) ≥ 24
- [Docker Compose](https://docs.docker.com/compose/) v2 (included with Docker Desktop)

No local Python or Node.js installation required — everything runs inside the container.

---

## Development Setup

### 1. Clone the repository

```bash
git clone git@github.com:Brembo109/mainty-v2.git
cd mainty-v2
```

### 2. Create your `.env` file

```bash
cp .env.example .env
```

The defaults in `.env.example` work out of the box for local development. You only need to change `SECRET_KEY` to any long random string:

```bash
# Generate a secret key
python -c "import secrets; print(secrets.token_urlsafe(50))"
```

Open `.env` and paste the output as `SECRET_KEY`.

### 3. Start the containers

```bash
docker compose up --build
```

This will:
- Build the Docker image (Python 3.12 + Tailwind CSS CLI)
- Start PostgreSQL and Mailhog
- Compile Tailwind CSS
- Wait for the database to be ready
- Run all migrations automatically

First build takes ~2 minutes. Subsequent starts are fast.

### 4. Bootstrap roles

In a second terminal, create the three default roles (Admin / User / Viewer):

```bash
docker compose exec web python manage.py bootstrap_roles
```

### 5. Create the initial admin user

```bash
docker compose exec web python manage.py create_initial_admin
```

Credentials are read from `.env` (`DJANGO_ADMIN_USER`, `DJANGO_ADMIN_EMAIL`, `DJANGO_ADMIN_PASSWORD`). If these are not set, you will be prompted interactively.

### 6. Open the application

| Service | URL |
|---|---|
| Application | http://localhost:8000 |
| Mailhog (email) | http://localhost:8025 |
| Django admin | http://localhost:8000/admin/ |

Log in with the admin credentials you set in step 5.

---

## Environment Variables

All variables are documented in [`.env.example`](.env.example).

| Variable | Required | Default | Description |
|---|---|---|---|
| `SECRET_KEY` | ✅ | — | Django secret key — must be unique and secret |
| `DEBUG` | | `True` | Set to `False` in production |
| `ALLOWED_HOSTS` | | `localhost,127.0.0.1` | Comma-separated list of allowed hostnames |
| `DATABASE_URL` | | `postgres://mainty:mainty@db:5432/mainty` | PostgreSQL connection string |
| `POSTGRES_DB` | | `mainty` | Database name (Docker Compose) |
| `POSTGRES_USER` | | `mainty` | Database user (Docker Compose) |
| `POSTGRES_PASSWORD` | | `mainty` | Database password — **change in production** |
| `PASSWORD_EXPIRY_DAYS` | | `90` | Days before users must change their password |
| `DJANGO_ADMIN_USER` | | — | Initial admin username |
| `DJANGO_ADMIN_EMAIL` | | — | Initial admin email |
| `DJANGO_ADMIN_PASSWORD` | | — | Initial admin password — **change in production** |
| `EMAIL_HOST` | | `mailhog` | SMTP host |
| `EMAIL_PORT` | | `1025` | SMTP port |

---

## Common Commands

```bash
# Start in the background
docker compose up -d

# View logs
docker compose logs -f web

# Stop all containers
docker compose down

# Run Django management commands
docker compose exec web python manage.py <command>

# Open a Django shell
docker compose exec web python manage.py shell

# Create a new migration after model changes
docker compose exec web python manage.py makemigrations

# Run tests
docker compose exec web pytest

# Rebuild the image (after changing requirements)
docker compose up --build
```

---

## Project Structure

```
mainty-v2/
├── apps/
│   ├── accounts/          # Custom user model, roles, authentication
│   └── audit/             # GMP audit trail (signals, views, export)
├── mainty/
│   ├── settings/
│   │   ├── base.py        # Shared settings
│   │   ├── development.py # Dev overrides (DEBUG=True, Mailhog)
│   │   └── production.py  # Prod overrides (HTTPS, SMTP, Gunicorn)
│   └── urls.py
├── templates/
│   ├── base.html          # App shell (sidebar + topbar)
│   ├── accounts/          # Auth pages
│   └── audit/             # Audit trail pages
├── static/src/main.css    # Tailwind source
├── docker-compose.yml     # Development stack
├── docker-compose.prod.yml # Production stack
└── Dockerfile
```

### Adding GMP-audited models

Any model that inherits `AuditedModel` is automatically tracked:

```python
from apps.audit.mixins import AuditedModel

class Equipment(AuditedModel):
    name = models.CharField(max_length=255)
    # ...
```

CREATE, UPDATE, and DELETE events are recorded with the acting user, changed fields, and IP address.

---

## Production Deployment

### 1. Prepare the `.env` file

Set these additional variables for production:

```env
DEBUG=False
ALLOWED_HOSTS=yourdomain.com
SECRET_KEY=<long-random-string>
POSTGRES_PASSWORD=<strong-password>
DJANGO_ADMIN_PASSWORD=<strong-password>

EMAIL_HOST=your-smtp-host
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your@email.com
EMAIL_HOST_PASSWORD=your-smtp-password
```

### 2. Start the production stack

```bash
docker compose -f docker-compose.prod.yml up --build -d
```

This uses Gunicorn (3 workers) behind Nginx, with static files served directly by Nginx.

### 3. Bootstrap roles and admin (first deploy only)

```bash
docker compose -f docker-compose.prod.yml exec web python manage.py bootstrap_roles
docker compose -f docker-compose.prod.yml exec web python manage.py create_initial_admin
```

### Notes

- HTTPS is enforced via `SECURE_SSL_REDIRECT` — put a TLS-terminating reverse proxy (e.g. Caddy, Traefik, or cloud load balancer) in front of Nginx
- Sessions expire after 1 hour of inactivity
- Audit logs are stored in the database and can be exported from the UI at `/audit/`
