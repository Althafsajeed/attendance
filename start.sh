#!/usr/bin/env bash
set -o errexit

python manage.py migrate --noinput
python manage.py create_default_admin --username "${ADMIN_USERNAME:-admin}" --password "${ADMIN_PASSWORD:-admin}"
gunicorn attendance_project.wsgi:application
