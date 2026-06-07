from django.core.management.base import BaseCommand

from attendance.models import User


class Command(BaseCommand):
    help = "Create or update the first local admin account."

    def add_arguments(self, parser):
        parser.add_argument("--username", default="admin")
        parser.add_argument("--password", default="admin")
        parser.add_argument("--email", default="admin@example.com")

    def handle(self, *args, **options):
        user, created = User.objects.get_or_create(username=options["username"])
        user.email = options["email"]
        user.role = User.ADMIN
        user.is_staff = True
        user.is_superuser = True
        user.is_active = True
        user.is_employee_active = True
        user.set_password(options["password"])
        user.save()

        action = "Created" if created else "Updated"
        self.stdout.write(self.style.SUCCESS(f"{action} admin user '{user.username}'."))
