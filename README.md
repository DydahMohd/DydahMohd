# EAC Helpdesk

A Django-based incident ticketing system for the East African Community (EAC).

## Overview

This project implements an internal helpdesk with role-based access and ticket workflows.

Key features:
- Custom user roles: `Admin`, `Technician`, and `Staff`
- Ticket metadata: wing, floor, room number, device serial number, category, priority
- Ticket lifecycle: open, in progress, resolved, closed, reopen
- Admin user management and role updates
- **AI-powered ticket categorization (initial integration)**
- Audit logging for ticket and user actions
- Report screens and export in PDF / Excel / CSV
- Stale ticket detection and notification support
- Staff cannot modify resolved/closed tickets
- Technician assignment, resolve, close, and reopen actions

## Requirements

- Python 3.11+
- Django 6.0.6

## Setup

1. Create and activate a virtual environment:

   ```powershell
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   ```

2. Install dependencies:

   ```powershell
   pip install -r requirements.txt
   ```

3. Apply database migrations:

   ```powershell
   .\.venv\Scripts\python.exe manage.py migrate
   ```

4. Create a superuser:

   ```powershell
   .\.venv\Scripts\python.exe manage.py createsuperuser
   ```

5. Run the development server:

   ```powershell
   .\.venv\Scripts\python.exe manage.py runserver
   ```

## Environment variables

You can configure the project via environment variables. The app also reads a local `.env` file from the project root, so production deployments can copy `.env.example` and replace the placeholder values.

Examples:

- `DJANGO_SECRET_KEY`
- `DJANGO_DEBUG`
- `DJANGO_ALLOWED_HOSTS`
- `DJANGO_DB_ENGINE`
- `DJANGO_DB_NAME`
- `DJANGO_EMAIL_BACKEND`
- `DJANGO_EMAIL_HOST`
- `DJANGO_EMAIL_PORT`
- `DJANGO_EMAIL_USE_TLS`
- `DJANGO_EMAIL_HOST_USER`
- `DJANGO_EMAIL_HOST_PASSWORD`
- `DJANGO_DEFAULT_FROM_EMAIL`

By default the project uses SQLite and the console email backend.

Generate a strong secret key before deploying:

```powershell
.\.venv\Scripts\python.exe -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

Recommended production values:

```powershell
DJANGO_SECRET_KEY=<paste_generated_secret_key>
DJANGO_DEBUG=False
DJANGO_ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
DJANGO_CSRF_TRUSTED_ORIGINS=https://yourdomain.com
DJANGO_SECURE_SSL_REDIRECT=True
DJANGO_SESSION_COOKIE_SECURE=True
DJANGO_CSRF_COOKIE_SECURE=True
```

After setting production values, verify them with:

```powershell
.\.venv\Scripts\python.exe manage.py check --deploy
```

## Running tests

Use the Django test runner for the core app:

```powershell
.\.venv\Scripts\python.exe manage.py test
```

## Scheduling stale ticket notifications

Stale ticket notifications can be run manually or scheduled.

### Cron (Linux/macOS)

```bash
0 7 * * * cd /path/to/eac_helpdesk && /path/to/.venv/Scripts/python.exe manage.py send_stale_ticket_notifications --days 3
```

### Windows Task Scheduler

- Action: `Start a program`
- Program/script: `C:\Path\To\.venv\Scripts\python.exe`
- Arguments: `manage.py send_stale_ticket_notifications --days 3`
- Start in: `C:\Path\To\eac_helpdesk`

## Authentication & Roles

- `Admin` users can manage users, access reports, and trigger stale ticket notifications.
- `Technician` users can assign, resolve, close, and reopen tickets.
- `Staff` users can create and update tickets they reported, but cannot modify resolved or closed tickets.

## Ticket workflows

- Staff reports incidents and enters metadata such as wing, floor, room, and device serial number.
- Technicians can assign themselves to tickets, update status, and resolve incidents.
- Admins can edit any ticket and manage roles.
- Tickets can be reopened with an optional reopen reason.
- Stale tickets are detected when open or in progress for more than 3 days.

## Stale ticket notifications

A management command is available to notify admins and assigned technicians about stale incidents.

Run manually:

```powershell
.\.venv\Scripts\python.exe manage.py send_stale_ticket_notifications --days 3
```

Admins can also trigger stale alerts from the dashboard when stale tickets are present.

## Reports

Reports are available to admins and technicians at `/tickets/report/` and can be exported as:
- PDF
- Excel
- CSV

## Notes

- Use the Django admin for advanced user and ticket management at `/admin/`.
- Static files and media are configured for development mode.
- Ensure `EMAIL_BACKEND` is configured appropriately for email delivery in production.

For contribution and development workflow details, see `CONTRIBUTING.md`.
