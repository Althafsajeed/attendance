from io import BytesIO

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from .models import Attendance


def build_attendance_summary(employee, records):
    summary = {
        "present": 0,
        "half_day": 0,
        "leave": 0,
        "total_minutes": 0,
    }
    for record in records:
        if record.status == Attendance.PRESENT:
            summary["present"] += 1
        elif record.status == Attendance.HALF_DAY:
            summary["half_day"] += 1
        elif record.status == Attendance.LEAVE:
            summary["leave"] += 1

        duration = record.total_work_duration
        if duration and record.check_out_time:
            summary["total_minutes"] += int(duration.total_seconds() // 60)

    hours = summary["total_minutes"] // 60
    minutes = summary["total_minutes"] % 60
    summary["total_hours_display"] = f"{hours}h {minutes}m"
    summary["employee"] = employee
    return summary


def build_attendance_report_pdf(employee, records, start_date, end_date):
    buffer = BytesIO()
    document = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=28, leftMargin=28, topMargin=28, bottomMargin=28)
    styles = getSampleStyleSheet()
    summary = build_attendance_summary(employee, records)

    story = [
        Paragraph("Monthly Attendance Report", styles["Title"]),
        Paragraph(f"Employee: {employee.get_full_name() or employee.username}", styles["Normal"]),
        Paragraph(f"Employee Code: {employee.employee_code or '-'}", styles["Normal"]),
        Paragraph(f"Department: {employee.department or '-'}", styles["Normal"]),
        Paragraph(f"Period: {start_date} to {end_date}", styles["Normal"]),
        Spacer(1, 14),
    ]

    summary_table = Table(
        [
            ["Present", "Half Day", "Leave", "Total Hours"],
            [summary["present"], summary["half_day"], summary["leave"], summary["total_hours_display"]],
        ],
        colWidths=[100, 100, 100, 120],
    )
    summary_table.setStyle(_table_style())
    story.extend([summary_table, Spacer(1, 18)])

    rows = [["Date", "Status", "Check In", "Exit", "Hours", "Distance"]]
    for record in records:
        rows.append(
            [
                str(record.date),
                record.get_status_display(),
                record.check_in_time.strftime("%I:%M %p") if record.check_in_time else "-",
                record.check_out_time.strftime("%I:%M %p") if record.check_out_time else "-",
                record.total_work_hours_display,
                f"{record.distance_from_office_meters:.0f} m" if record.distance_from_office_meters is not None else "-",
            ]
        )

    if len(rows) == 1:
        rows.append(["No attendance records", "-", "-", "-", "-", "-"])

    records_table = Table(rows, colWidths=[72, 82, 72, 72, 86, 82], repeatRows=1)
    records_table.setStyle(_table_style())
    story.append(records_table)

    document.build(story)
    pdf = buffer.getvalue()
    buffer.close()
    return pdf


def _table_style():
    return TableStyle(
        [
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#116466")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#dce3ec")),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f5f7fb")]),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
            ("TOPPADDING", (0, 0), (-1, -1), 7),
        ]
    )
