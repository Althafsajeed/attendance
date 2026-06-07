from datetime import timedelta
from decimal import Decimal, InvalidOperation

from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db.models import Count
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from .forms import (
    EmployeeCreationForm,
    EmployeeUpdateForm,
    LeaveRequestForm,
    LeaveReviewForm,
    OfficePolicyForm,
)
from .models import Attendance, LeaveRequest, OfficePolicy, User
from .reports import build_attendance_report_pdf
from .utils import distance_meters


def admin_required(user):
    return user.is_authenticated and user.is_company_admin


def manager_required(user):
    return user.is_authenticated and user.is_manager


@login_required
def dashboard(request):
    if request.user.is_company_admin:
        return redirect("admin_dashboard")

    today = timezone.localdate()
    policy = OfficePolicy.current()
    today_attendance = Attendance.objects.filter(employee=request.user, date=today).first()
    records = Attendance.objects.filter(employee=request.user).order_by("-date")[:20]
    leave_requests = LeaveRequest.objects.filter(employee=request.user)[:10]
    pending_team_requests = LeaveRequest.objects.none()
    if request.user.is_manager:
        pending_team_requests = LeaveRequest.objects.filter(manager=request.user, status=LeaveRequest.PENDING)

    return render(
        request,
        "attendance/employee_dashboard.html",
        {
            "policy": policy,
            "today_attendance": today_attendance,
            "records": records,
            "leave_requests": leave_requests,
            "pending_team_requests": pending_team_requests,
        },
    )


def _get_location(request):
    try:
        return Decimal(request.POST["latitude"]), Decimal(request.POST["longitude"])
    except (KeyError, InvalidOperation):
        return None, None


def _validate_attendance_location(latitude, longitude, policy):
    if latitude is None or longitude is None:
        return None, "Location permission is required to mark attendance."
    if float(policy.latitude) == 0 and float(policy.longitude) == 0:
        return None, "Admin must set the office latitude and longitude first."

    distance = distance_meters(latitude, longitude, policy.latitude, policy.longitude)
    if distance > policy.allowed_radius_meters:
        return distance, f"You are {int(distance)} meters from office. Attendance is allowed within {policy.allowed_radius_meters} meters."
    return distance, ""


@login_required
def mark_attendance(request):
    if request.method != "POST":
        return redirect("dashboard")

    user = request.user
    if not user.is_employee_active:
        messages.error(request, "Your employee account is inactive. Please contact admin.")
        return redirect("dashboard")

    policy = OfficePolicy.current()
    current_time = timezone.localtime().time()
    is_late = current_time > policy.attendance_end_time

    if user.used_leave_days() >= user.allowed_leave_days and not LeaveRequest.objects.filter(
        employee=user, status=LeaveRequest.APPROVED, start_date__lte=timezone.localdate(), end_date__gte=timezone.localdate()
    ).exists():
        messages.error(request, "Your leave limit is over. Please request your manager before marking attendance.")
        return redirect("leave_request")

    latitude, longitude = _get_location(request)
    distance, error = _validate_attendance_location(latitude, longitude, policy)
    if error:
        messages.error(request, error)
        return redirect("dashboard")

    attendance, created = Attendance.objects.get_or_create(employee=user, date=timezone.localdate())
    if attendance.check_in_time:
        messages.info(request, "Attendance is already marked for today.")
        return redirect("dashboard")

    attendance.status = Attendance.HALF_DAY if is_late else Attendance.PRESENT
    attendance.check_in_time = timezone.now()
    attendance.check_in_latitude = latitude
    attendance.check_in_longitude = longitude
    attendance.distance_from_office_meters = distance
    attendance.notes = "Late attendance marked as half day." if is_late else "Marked by employee from approved office location."
    attendance.save()
    if is_late:
        messages.success(request, "Attendance marked as half day because it was after the attendance end time.")
    else:
        messages.success(request, "Attendance marked successfully.")
    return redirect("dashboard")


@login_required
def mark_checkout(request):
    if request.method != "POST":
        return redirect("dashboard")

    policy = OfficePolicy.current()
    latitude, longitude = _get_location(request)
    distance, error = _validate_attendance_location(latitude, longitude, policy)
    if error:
        messages.error(request, error)
        return redirect("dashboard")

    attendance = Attendance.objects.filter(
        employee=request.user,
        date=timezone.localdate(),
        status__in=[Attendance.PRESENT, Attendance.HALF_DAY],
    ).first()
    if not attendance:
        messages.error(request, "You must mark attendance before checkout.")
        return redirect("dashboard")
    if attendance.check_out_time:
        messages.info(request, "Checkout is already marked for today.")
        return redirect("dashboard")

    attendance.check_out_time = timezone.now()
    attendance.check_out_latitude = latitude
    attendance.check_out_longitude = longitude
    attendance.save()
    messages.success(request, "Checkout marked successfully.")
    return redirect("dashboard")


@login_required
def leave_request(request):
    if request.method == "POST":
        form = LeaveRequestForm(request.POST)
        if form.is_valid():
            leave = form.save(commit=False)
            leave.employee = request.user
            leave.manager = request.user.manager
            leave.save()
            messages.success(request, "Leave request sent to your manager.")
            return redirect("dashboard")
    else:
        form = LeaveRequestForm()
    return render(request, "attendance/leave_request.html", {"form": form})


@user_passes_test(admin_required)
def admin_dashboard(request):
    today = timezone.localdate()
    employees = User.objects.filter(is_superuser=False).order_by("first_name", "username")
    today_records = Attendance.objects.filter(date=today).select_related("employee")
    stats = {
        "employees": employees.count(),
        "present": today_records.filter(status=Attendance.PRESENT).count(),
        "half_day": today_records.filter(status=Attendance.HALF_DAY).count(),
        "leave": today_records.filter(status=Attendance.LEAVE).count(),
        "pending_requests": LeaveRequest.objects.filter(status=LeaveRequest.PENDING).count(),
    }
    records_by_employee = {record.employee_id: record for record in today_records}
    employee_rows = [
        {"employee": employee, "today_record": records_by_employee.get(employee.id)}
        for employee in employees
    ]
    recent_records = Attendance.objects.select_related("employee")[:25]
    leave_requests = LeaveRequest.objects.select_related("employee", "manager").filter(status=LeaveRequest.PENDING)[:20]
    departments = employees.values("department").annotate(total=Count("id")).order_by("department")
    return render(
        request,
        "attendance/admin_dashboard.html",
        {
            "stats": stats,
            "employees": employees,
            "employee_rows": employee_rows,
            "recent_records": recent_records,
            "leave_requests": leave_requests,
            "departments": departments,
            "policy": OfficePolicy.current(),
        },
    )


@user_passes_test(admin_required)
def policy_settings(request):
    policy = OfficePolicy.current()
    if request.method == "POST":
        form = OfficePolicyForm(request.POST, instance=policy)
        if form.is_valid():
            form.save()
            messages.success(request, "Office rules updated.")
            return redirect("admin_dashboard")
    else:
        form = OfficePolicyForm(instance=policy)
    return render(request, "attendance/policy_settings.html", {"form": form})


def _report_dates(request):
    today = timezone.localdate()
    preset = request.GET.get("preset", "week")
    start_date = today - timedelta(days=6)
    end_date = today

    if preset == "month":
        start_date = today.replace(day=1)
    elif preset == "year":
        start_date = today.replace(month=1, day=1)
    elif preset == "custom":
        try:
            start_date = timezone.datetime.strptime(request.GET.get("from_date", ""), "%Y-%m-%d").date()
            end_date = timezone.datetime.strptime(request.GET.get("to_date", ""), "%Y-%m-%d").date()
        except ValueError:
            start_date = today - timedelta(days=6)
            end_date = today
            preset = "week"

    if end_date < start_date:
        start_date, end_date = end_date, start_date
    return preset, start_date, end_date


@user_passes_test(admin_required)
def attendance_report(request):
    preset, start_date, end_date = _report_dates(request)
    selected_employee = request.GET.get("employee")
    employees = User.objects.filter(is_superuser=False).order_by("first_name", "username")
    records = Attendance.objects.select_related("employee").filter(date__range=(start_date, end_date))

    if selected_employee:
        records = records.filter(employee_id=selected_employee)

    employee_map = {employee.id: employee for employee in employees}
    report_rows = {
        employee.id: {
            "employee": employee,
            "present": 0,
            "half_day": 0,
            "leave": 0,
            "total_minutes": 0,
            "records": [],
        }
        for employee in employees
        if not selected_employee or str(employee.id) == selected_employee
    }

    for record in records.order_by("employee__first_name", "employee__username", "date"):
        row = report_rows.setdefault(
            record.employee_id,
            {
                "employee": employee_map.get(record.employee_id, record.employee),
                "present": 0,
                "half_day": 0,
                "leave": 0,
                "total_minutes": 0,
                "records": [],
            },
        )
        if record.status == Attendance.PRESENT:
            row["present"] += 1
        elif record.status == Attendance.HALF_DAY:
            row["half_day"] += 1
        elif record.status == Attendance.LEAVE:
            row["leave"] += 1

        duration = record.total_work_duration
        if duration and record.check_out_time:
            row["total_minutes"] += int(duration.total_seconds() // 60)
        row["records"].append(record)

    for row in report_rows.values():
        hours = row["total_minutes"] // 60
        minutes = row["total_minutes"] % 60
        row["total_hours_display"] = f"{hours}h {minutes}m"
        row["download_url"] = (
            f"?employee={row['employee'].id}&preset=custom&from_date={start_date:%Y-%m-%d}&to_date={end_date:%Y-%m-%d}"
        )

    return render(
        request,
        "attendance/attendance_report.html",
        {
            "employees": employees,
            "report_rows": report_rows.values(),
            "records": records.order_by("-date", "employee__first_name", "employee__username"),
            "preset": preset,
            "from_date": start_date,
            "to_date": end_date,
            "selected_employee": selected_employee,
        },
    )


@user_passes_test(admin_required)
def attendance_report_pdf(request, employee_id):
    preset, start_date, end_date = _report_dates(request)
    employee = get_object_or_404(User, pk=employee_id, is_superuser=False)
    records = list(
        Attendance.objects.filter(employee=employee, date__range=(start_date, end_date)).order_by("date")
    )
    pdf = build_attendance_report_pdf(employee, records, start_date, end_date)
    filename = f"{employee.username}-attendance-{start_date:%Y%m%d}-{end_date:%Y%m%d}.pdf"
    response = HttpResponse(pdf, content_type="application/pdf")
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    return response


@user_passes_test(admin_required)
def create_employee(request):
    if request.method == "POST":
        form = EmployeeCreationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Employee login created.")
            return redirect("admin_dashboard")
    else:
        form = EmployeeCreationForm()
    return render(request, "attendance/employee_form.html", {"form": form, "title": "Create Employee"})


@user_passes_test(admin_required)
def edit_employee(request, pk):
    employee = get_object_or_404(User, pk=pk)
    if request.method == "POST":
        form = EmployeeUpdateForm(request.POST, instance=employee)
        if form.is_valid():
            form.save()
            messages.success(request, "Employee updated.")
            return redirect("admin_dashboard")
    else:
        form = EmployeeUpdateForm(instance=employee)
    return render(request, "attendance/employee_form.html", {"form": form, "title": "Edit Employee"})


@user_passes_test(manager_required)
def review_leave_request(request, pk):
    leave = get_object_or_404(LeaveRequest, pk=pk)
    if not request.user.is_company_admin and leave.manager_id != request.user.id:
        messages.error(request, "You can only review requests assigned to you.")
        return redirect("dashboard")

    if request.method == "POST":
        form = LeaveReviewForm(request.POST)
        if form.is_valid():
            if form.cleaned_data["action"] == "approve":
                leave.approve(request.user)
                messages.success(request, "Leave request approved.")
            else:
                leave.reject(request.user, form.cleaned_data["manager_note"])
                messages.success(request, "Leave request rejected.")
            return redirect("dashboard")
    else:
        form = LeaveReviewForm()
    return render(request, "attendance/review_leave.html", {"form": form, "leave": leave})
