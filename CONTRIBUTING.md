# Contributing to EAC Helpdesk

Thanks for contributing! This guide covers development setup, testing, and workflow conventions.

## Development setup

1. Create and activate a virtual environment:

   ```powershell
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   ```

2. Install dependencies:

   ```powershell
   pip install -r requirements.txt
   ```

3. Copy environment variable settings if needed. The app reads `.env` automatically, but the sample contains production-oriented values, so keep SQLite defaults for local development unless you are configuring another database:

   ```powershell
   copy .env.example .env
   ```

4. Apply database migrations:

   ```powershell
   .\.venv\Scripts\python.exe manage.py migrate
   ```

5. Create a local superuser:

   ```powershell
   .\.venv\Scripts\python.exe manage.py createsuperuser
   ```

## Running the application

```powershell
.\.venv\Scripts\python.exe manage.py runserver
```

## Running tests

Run the app test suite with:

```powershell
.\.venv\Scripts\python.exe manage.py test
```

## Coding standards

- Keep changes small and focused.
- Add or update tests for any new behavior or bug fix.
- Prefer clear and descriptive commit messages.
- Include database migrations for model changes.

## Stale ticket notifications

The project includes a management command for stale ticket alerts:

```powershell
.\.venv\Scripts\python.exe manage.py send_stale_ticket_notifications --days 3
```

## Pull request checklist

- [ ] Branch name reflects the feature or fix.
- [ ] Code passes `python manage.py check`.
- [ ] Tests added or updated and passing.
- [ ] README updated for new functionality.
- [ ] Migrations included for model changes.
