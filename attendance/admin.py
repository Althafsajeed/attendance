from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import Attendance, LeaveRequest, OfficePolicy, User


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (
        (
            "Employee details",
            {
                "fields": (
                    "employee_code",
                    "role",
                    "phone",
                    "department",
                    "manager",
                    "allowed_leave_days",
                    "is_employee_active",
                )
            },
        ),
    )
    list_display = ("username", "employee_code", "role", "department", "manager", "is_active")
    list_filter = ("role", "department", "is_active")


@admin.register(OfficePolicy)
class OfficePolicyAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "latitude",
        "longitude",
        "allowed_radius_meters",
        "attendance_start_time",
        "attendance_end_time",
    )


@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ("employee", "date", "status", "check_in_time", "check_out_time", "distance_from_office_meters")
    list_filter = ("status", "date")
    search_fields = ("employee__username", "employee__employee_code")


@admin.register(LeaveRequest)
class LeaveRequestAdmin(admin.ModelAdmin):
    list_display = ("employee", "manager", "start_date", "end_date", "status", "reviewed_by")
    list_filter = ("status", "start_date")
    search_fields = ("employee__username", "reason")
