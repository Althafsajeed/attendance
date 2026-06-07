from django.core.management.base import BaseCommand
from django.utils import timezone

from attendance.models import Attendance, OfficePolicy, User


class Command(BaseCommand):
    help = "Mark active employees who did not check in as leave for a selected date."

    def add_arguments(self, parser):
        parser.add_argument("--date", help="Date in YYYY-MM-DD format. Defaults to today.")

    def handle(self, *args, **options):
        policy = OfficePolicy.current()
        if not policy.auto_leave_enabled:
            self.stdout.write(self.style.WARNING("Auto leave is disabled in office rules."))
            return

        selected_date = timezone.localdate()
        if options["date"]:
            selected_date = timezone.datetime.strptime(options["date"], "%Y-%m-%d").date()

        employees = User.objects.filter(is_employee_active=True, is_active=True, is_superuser=False)
        created_count = 0
        for employee in employees:
            _, created = Attendance.objects.get_or_create(
                employee=employee,
                date=selected_date,
                defaults={"status": Attendance.LEAVE, "notes": "Automatically marked as leave because attendance was not marked."},
            )
            if created:
                created_count += 1

        self.stdout.write(self.style.SUCCESS(f"Marked {created_count} employee(s) as leave for {selected_date}."))
