#!/usr/bin/env bash
set -o errexit

pip install -r requirements.txt
python manage.py collectstatic --no-input
python manage.py migrate --noinput
python manage.py create_default_admin --username "${ADMIN_USERNAME:-admin}" --password "${ADMIN_PASSWORD:-admin}"
