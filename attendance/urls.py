from django.contrib.auth import views as auth_views
from django.urls import path

from . import views


urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("login/", auth_views.LoginView.as_view(template_name="attendance/login.html"), name="login"),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),
    path("mark/", views.mark_attendance, name="mark_attendance"),
    path("checkout/", views.mark_checkout, name="mark_checkout"),
    path("leave/request/", views.leave_request, name="leave_request"),
    path("admin-dashboard/", views.admin_dashboard, name="admin_dashboard"),
    path("admin-dashboard/reports/", views.attendance_report, name="attendance_report"),
    path("admin-dashboard/reports/<int:employee_id>/pdf/", views.attendance_report_pdf, name="attendance_report_pdf"),
    path("admin-dashboard/policy/", views.policy_settings, name="policy_settings"),
    path("admin-dashboard/employees/new/", views.create_employee, name="create_employee"),
    path("admin-dashboard/employees/<int:pk>/edit/", views.edit_employee, name="edit_employee"),
    path("admin-dashboard/leave/<int:pk>/review/", views.review_leave_request, name="review_leave_request"),
]
