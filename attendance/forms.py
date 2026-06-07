from django import forms
from django.contrib.auth.forms import UserCreationForm

from .models import LeaveRequest, OfficePolicy, User
from .utils import parse_coordinate


class EmployeeCreationForm(UserCreationForm):
    class Meta:
        model = User
        fields = (
            "username",
            "first_name",
            "last_name",
            "email",
            "employee_code",
            "phone",
            "department",
            "role",
            "manager",
            "allowed_leave_days",
            "password1",
            "password2",
        )


class EmployeeUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = (
            "first_name",
            "last_name",
            "email",
            "employee_code",
            "phone",
            "department",
            "role",
            "manager",
            "allowed_leave_days",
            "is_employee_active",
            "is_active",
        )


class OfficePolicyForm(forms.ModelForm):
    latitude = forms.CharField(
        help_text='Accepts decimal or DMS format, for example 9°24\'06.3"N.',
    )
    longitude = forms.CharField(
        help_text='Accepts decimal or DMS format, for example 76°21\'23.2"E.',
    )

    class Meta:
        model = OfficePolicy
        fields = (
            "name",
            "latitude",
            "longitude",
            "allowed_radius_meters",
            "office_start_time",
            "office_end_time",
            "attendance_start_time",
            "attendance_end_time",
            "auto_leave_enabled",
        )
        widgets = {
            "office_start_time": forms.TimeInput(attrs={"type": "time"}),
            "office_end_time": forms.TimeInput(attrs={"type": "time"}),
            "attendance_start_time": forms.TimeInput(attrs={"type": "time"}),
            "attendance_end_time": forms.TimeInput(attrs={"type": "time"}),
        }

    def clean_latitude(self):
        try:
            latitude = parse_coordinate(self.cleaned_data["latitude"])
        except ValueError as exc:
            raise forms.ValidationError(str(exc))
        if latitude < -90 or latitude > 90:
            raise forms.ValidationError("Latitude must be between -90 and 90.")
        return latitude

    def clean_longitude(self):
        try:
            longitude = parse_coordinate(self.cleaned_data["longitude"])
        except ValueError as exc:
            raise forms.ValidationError(str(exc))
        if longitude < -180 or longitude > 180:
            raise forms.ValidationError("Longitude must be between -180 and 180.")
        return longitude


class LeaveRequestForm(forms.ModelForm):
    class Meta:
        model = LeaveRequest
        fields = ("start_date", "end_date", "reason")
        widgets = {
            "start_date": forms.DateInput(attrs={"type": "date"}),
            "end_date": forms.DateInput(attrs={"type": "date"}),
        }

    def clean(self):
        cleaned = super().clean()
        start = cleaned.get("start_date")
        end = cleaned.get("end_date")
        if start and end and end < start:
            raise forms.ValidationError("End date cannot be before start date.")
        return cleaned


class LeaveReviewForm(forms.Form):
    action = forms.ChoiceField(choices=(("approve", "Approve"), ("reject", "Reject")))
    manager_note = forms.CharField(required=False, widget=forms.Textarea)
