import os
import sys
import pathlib
import django
import secrets

# Ensure project root is on sys.path so Django settings can be imported
project_root = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(project_root))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'eac_helpdesk.settings')
django.setup()

from django.contrib.auth import get_user_model
User = get_user_model()

uname = 'ADMIN'
try:
    u = User.objects.get(username=uname)
except User.DoesNotExist:
    u = User.objects.filter(is_superuser=True).first()

if not u:
    print('ERROR: No user found to update.')
else:
    pw = secrets.token_urlsafe(12)
    u.set_password(pw)
    u.save()
    print(f'UPDATED_USER:{u.username}')
    print(f'NEW_PASSWORD:{pw}')
