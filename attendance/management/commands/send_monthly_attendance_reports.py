import calendar
from datetime import date

from django.core.mail import EmailMessage
from django.core.management.base import BaseCommand
from django.utils import timezone

from attendance.models import Attendance, User
from attendance.reports import build_attendance_report_pdf


class Command(BaseCommand):
    help = "Email monthly attendance PDF reports to active employees."

    def add_arguments(self, parser):
        parser.add_argument("--month", help="Month in YYYY-MM format. Defaults to the current month.")

    def handle(self, *args, **options):
        start_date, end_date = self._month_range(options["month"])
        employees = User.objects.filter(
            is_superuser=False,
            is_active=True,
            is_employee_active=True,
        ).exclude(email="")

        sent_count = 0
        skipped_count = 0
        for employee in employees:
            records = list(
                Attendance.objects.filter(employee=employee, date__range=(start_date, end_date)).order_by("date")
            )
            pdf = build_attendance_report_pdf(employee, records, start_date, end_date)
            filename = f"{employee.username}-attendance-{start_date:%Y%m}.pdf"
            message = EmailMessage(
                subject=f"Attendance report for {start_date:%B %Y}",
                body=(
                    f"Hello {employee.get_full_name() or employee.username},\n\n"
                    f"Please find your attendance report for {start_date:%B %Y} attached.\n\n"
                    "Regards,\nAttendance Team"
                ),
                to=[employee.email],
            )
            message.attach(filename, pdf, "application/pdf")
            sent_count += message.send(fail_silently=False)

        skipped_count = User.objects.filter(is_superuser=False, is_active=True, is_employee_active=True, email="").count()
        self.stdout.write(
            self.style.SUCCESS(
                f"Sent {sent_count} report email(s) for {start_date} to {end_date}. "
                f"Skipped {skipped_count} employee(s) without email."
            )
        )

    def _month_range(self, month_value):
        if month_value:
            year, month = [int(part) for part in month_value.split("-")]
        else:
            today = timezone.localdate()
            year, month = today.year, today.month

        last_day = calendar.monthrange(year, month)[1]
        return date(year, month, 1), date(year, month, last_day)
