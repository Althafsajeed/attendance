import os

from django.contrib.auth.hashers import make_password
from django.db import migrations


def create_default_admin(apps, schema_editor):
    User = apps.get_model("attendance", "User")
    username = os.environ.get("ADMIN_USERNAME", "admin")
    password = os.environ.get("ADMIN_PASSWORD", "admin")
    email = os.environ.get("ADMIN_EMAIL", "admin@example.com")

    user, created = User.objects.get_or_create(username=username)
    user.email = email
    user.role = "admin"
    user.is_staff = True
    user.is_superuser = True
    user.is_active = True
    user.is_employee_active = True
    if created:
        user.password = make_password(password)
    user.save()


def noop_reverse(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("attendance", "0002_alter_attendance_status"),
    ]

    operations = [
        migrations.RunPython(create_default_admin, noop_reverse),
    ]
