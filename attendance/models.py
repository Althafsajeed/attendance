from datetime import timedelta

from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone


class User(AbstractUser):
    EMPLOYEE = "employee"
    MANAGER = "manager"
    ADMIN = "admin"
    ROLE_CHOICES = [
        (EMPLOYEE, "Employee"),
        (MANAGER, "Manager"),
        (ADMIN, "Admin"),
    ]

    employee_code = models.CharField(max_length=30, unique=True, null=True, blank=True)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default=EMPLOYEE)
    phone = models.CharField(max_length=20, blank=True)
    department = models.CharField(max_length=80, blank=True)
    manager = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="team_members",
        limit_choices_to={"role__in": [MANAGER, ADMIN]},
    )
    allowed_leave_days = models.PositiveIntegerField(default=2)
    is_employee_active = models.BooleanField(default=True)

    @property
    def is_company_admin(self):
        return self.is_superuser or self.role == self.ADMIN

    @property
    def is_manager(self):
        return self.is_company_admin or self.role == self.MANAGER

    def used_leave_days(self):
        return Attendance.objects.filter(employee=self, status=Attendance.LEAVE).count()

    def remaining_leave_days(self):
        return max(self.allowed_leave_days - self.used_leave_days(), 0)


class OfficePolicy(models.Model):
    name = models.CharField(max_length=100, default="Main Office")
    latitude = models.DecimalField(max_digits=9, decimal_places=6, default=0)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, default=0)
    allowed_radius_meters = models.PositiveIntegerField(default=150)
    office_start_time = models.TimeField(default="09:00")
    office_end_time = models.TimeField(default="18:00")
    attendance_start_time = models.TimeField(default="08:30")
    attendance_end_time = models.TimeField(default="09:30")
    exit_start_time = models.TimeField(default="17:30")
    exit_end_time = models.TimeField(default="19:00")
    auto_leave_enabled = models.BooleanField(default=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "Office policies"

    def __str__(self):
        return self.name

    @classmethod
    def current(cls):
        policy, _ = cls.objects.get_or_create(pk=1)
        return policy


class Attendance(models.Model):
    PRESENT = "present"
    HALF_DAY = "half_day"
    LEAVE = "leave"
    STATUS_CHOICES = [
        (PRESENT, "Present"),
        (HALF_DAY, "Half Day"),
        (LEAVE, "Leave"),
    ]

    employee = models.ForeignKey(User, on_delete=models.CASCADE, related_name="attendance_records")
    date = models.DateField(default=timezone.localdate)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=PRESENT)
    check_in_time = models.DateTimeField(null=True, blank=True)
    check_out_time = models.DateTimeField(null=True, blank=True)
    check_in_latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    check_in_longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    check_out_latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    check_out_longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    distance_from_office_meters = models.FloatField(null=True, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("employee", "date")
        ordering = ["-date", "-created_at"]

    def __str__(self):
        return f"{self.employee.username} - {self.date} - {self.status}"

    @property
    def total_work_duration(self):
        if not self.check_in_time:
            return None
        end_time = self.check_out_time or timezone.now()
        return end_time - self.check_in_time

    @property
    def total_work_hours_display(self):
        duration = self.total_work_duration
        if not duration:
            return "-"
        total_minutes = int(duration.total_seconds() // 60)
        hours = total_minutes // 60
        minutes = total_minutes % 60
        suffix = "" if self.check_out_time else " (In office)"
        return f"{hours}h {minutes}m{suffix}"


class LeaveRequest(models.Model):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    STATUS_CHOICES = [
        (PENDING, "Pending"),
        (APPROVED, "Approved"),
        (REJECTED, "Rejected"),
    ]

    employee = models.ForeignKey(User, on_delete=models.CASCADE, related_name="leave_requests")
    manager = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="managed_leave_requests",
    )
    start_date = models.DateField(default=timezone.localdate)
    end_date = models.DateField(default=timezone.localdate)
    reason = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=PENDING)
    manager_note = models.TextField(blank=True)
    reviewed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reviewed_leave_requests",
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    @property
    def total_days(self):
        return (self.end_date - self.start_date).days + 1

    def approve(self, reviewer):
        self.status = self.APPROVED
        self.reviewed_by = reviewer
        self.reviewed_at = timezone.now()
        self.save()
        for offset in range(self.total_days):
            leave_date = self.start_date + timedelta(days=offset)
            Attendance.objects.update_or_create(
                employee=self.employee,
                date=leave_date,
                defaults={"status": Attendance.LEAVE, "notes": "Approved leave request"},
            )

    def reject(self, reviewer, note=""):
        self.status = self.REJECTED
        self.reviewed_by = reviewer
        self.reviewed_at = timezone.now()
        self.manager_note = note
        self.save()
