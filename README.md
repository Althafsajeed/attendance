# Attendance Management System

A simple Django web application for office attendance marking with admin and employee dashboards.

## Features

- Employee login accounts
- Admin dashboard
- Employee dashboard
- Office location validation using browser GPS
- Admin can set office latitude, longitude, radius, office time, and attendance time
- DMS coordinate support, for example `9°24'06.3"N`
- Attendance marking from office location only
- Late attendance after attendance end time is marked as `Half Day`
- Exit can be marked any time from office location
- Working hours calculation
- Leave request and manager/admin approval
- Auto leave marking command for employees who do not mark attendance
- Attendance report filters by week, month, year, or custom date range
- Per-employee PDF report download
- Monthly PDF attendance report email command

## Setup

Create and activate a virtual environment:

```powershell
python -m venv .venv
.\.venv\Scripts\activate
```

Install dependencies:

```powershell
pip install -r requirements.txt
```

Apply migrations:

```powershell
python manage.py migrate
```

Create or update the default admin user:

```powershell
python manage.py create_default_admin --username admin --password admin
```

Start the development server:

```powershell
python manage.py runserver
```

Open:

```text
http://127.0.0.1:8000/login/
```

## Default Admin Login

```text
Username: admin
Password: admin
```

## First Admin Steps

1. Log in as admin.
2. Go to `Office Rules`.
3. Set the real office latitude and longitude.
4. Set the allowed location radius in meters.
5. Set attendance start and end time.
6. Create employee login accounts.

Office location accepts decimal coordinates or DMS coordinates:

```text
Latitude: 9°24'06.3"N
Longitude: 76°21'23.2"E
```

## Attendance Rules

- Employee must allow browser location permission.
- Employee must be inside the configured office radius.
- Attendance before or at attendance end time is marked as `Present`.
- Attendance after attendance end time is marked as `Half Day`.
- Exit can be marked any time, but only from office location.
- Working hours are calculated from check-in to exit.
- If exit is not marked yet, dashboard shows the employee as `In office`.

## Reports

Admin can open:

```text
http://127.0.0.1:8000/admin-dashboard/reports/
```

Available filters:

- Week
- Month
- Year
- Custom from date and to date
- Employee-wise filter

Each employee row has a `Download PDF` button.

## Auto Mark Leave

Run this command to mark active employees as leave when they did not mark attendance:

```powershell
python manage.py mark_absentees_as_leave
```

For a specific date:

```powershell
python manage.py mark_absentees_as_leave --date 2026-06-07
```

## Monthly Email Reports

Send monthly attendance PDF reports to employees with email IDs:

```powershell
python manage.py send_monthly_attendance_reports --month 2026-06
```

By default, email uses Django console backend for development. Emails are printed in the terminal instead of being sent.

To send real emails, update SMTP settings in `attendance_project/settings.py`.

Example Gmail-style settings:

```python
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = "smtp.gmail.com"
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = "your-email@gmail.com"
EMAIL_HOST_PASSWORD = "your-app-password"
DEFAULT_FROM_EMAIL = "Attendance System <your-email@gmail.com>"
```

## Useful Commands

```powershell
python manage.py check
python manage.py migrate
python manage.py runserver
python manage.py create_default_admin --username admin --password admin
python manage.py mark_absentees_as_leave
python manage.py send_monthly_attendance_reports --month 2026-06
```

## Notes

- This project uses SQLite for local development.
- Browser geolocation works best on localhost or HTTPS.
- Change `SECRET_KEY`, `DEBUG`, email settings, and database settings before production use.
