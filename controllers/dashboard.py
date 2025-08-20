from odoo import http
from odoo.http import request
from datetime import datetime, timedelta, date
import pytz
import calendar
import logging

_logger = logging.getLogger(__name__)

MYANMAR_TZ = pytz.timezone('Asia/Yangon')


class AttendanceDashboardController(http.Controller):

    def _now_myanmar(self):
        """Return current datetime in Myanmar timezone"""
        return datetime.now(pytz.utc).astimezone(MYANMAR_TZ)

    def _get_fiscal_period(self):
        """Return start_date and end_date based on fiscal year starting July 26"""
        today = self._now_myanmar()
        july_26_current = today.replace(month=7, day=26, hour=0, minute=0, second=0, microsecond=0)

        if today < july_26_current:
            start_date = july_26_current.replace(year=today.year - 1)
        else:
            start_date = july_26_current.replace(year=today.year)

        return start_date, today

    # --- Dashboard Route ---
    @http.route('/attendance/dashboard', type='http', auth='public', website=True)
    def attendance_dashboard(self, **kwargs):
        employee = self._get_employee()
        if not employee:
            return request.redirect('/employee/register')

        start_date, end_date = self._get_fiscal_period()

        attendances = request.env['hr.attendance'].sudo().search([
            ('employee_id', '=', employee.id),
            ('check_in', '>=', start_date),
            ('check_in', '<=', end_date)
        ])

        stats = self._calculate_stats(employee, attendances, start_date, end_date)

        return request.render('attendance_dashboard.main_dashboard', {
            'employee': employee,
            'stats': stats,
            'current_period': f"{start_date.strftime('%B %d, %Y')} - {end_date.strftime('%B %d, %Y')}",
            'company_info': {
                'name': 'AGB Communication',
                'country': 'Myanmar',
                'phone': '+959-765492075',
                'email': 'hr@agbcommunication.com'
            }
        })

    # --- Calendar Route ---
    @http.route('/attendance/calendar', type='http', auth='public', website=True)
    def attendance_calendar(self, year=None, month=None, **kwargs):
        employee = self._get_employee()
        if not employee:
            return request.redirect('/employee/register')

        today = self._now_myanmar()
        year = int(year) if year else today.year
        month = int(month) if month else today.month

        calendar_data = self._get_calendar_data(employee, year, month)

        return request.render('attendance_dashboard.attendance_calendar', {
            'employee': employee,
            'calendar_data': calendar_data,
            'year': year,
            'month': month,
            'month_name': calendar.month_name[month],
            'prev_month': self._get_prev_month(year, month),
            'next_month': self._get_next_month(year, month),
        })

    # --- Absent Route ---
    @http.route('/attendance/absent', type='http', auth='public', website=True)
    def absent_details(self, **kwargs):
        employee = self._get_employee()
        if not employee:
            return request.redirect('/employee/register')

        absent_days = self._get_absent_days(employee)
        return request.render('attendance_dashboard.absent_details', {
            'employee': employee,
            'absent_days': absent_days,
            'total_absent': len(absent_days),
            'current_period': f"{self._get_fiscal_period()[0].strftime('%B %d, %Y')} - {self._now_myanmar().strftime('%B %d, %Y')}"
        })

    # --- Late Route ---
    @http.route('/attendance/late', type='http', auth='public', website=True)
    def late_details(self, **kwargs):
        employee = self._get_employee()
        if not employee:
            return request.redirect('/employee/register')

        late_days, total_late_minutes, avg_lateness = self._get_late_days(employee)

        return request.render('attendance_dashboard.late_details', {
            'employee': employee,
            'late_days': late_days,
            'total_late_days': len(late_days),
            'total_late_minutes': total_late_minutes,
            'avg_lateness': avg_lateness,
            'current_period': f"{self._get_fiscal_period()[0].strftime('%B %d, %Y')} - {self._now_myanmar().strftime('%B %d, %Y')}"
        })

    # --- Logout Route ---
    @http.route('/attendance/logout', type='http', auth='public', website=True)
    def attendance_logout(self, **kwargs):
        request.session.pop('employee_number', None)
        return request.redirect('/employee/register')

    # --- Helper Methods ---
    def _get_employee(self):
        employee_id = request.session.get('employee_number')
        if not employee_id:
            return None
        employee = request.env['hr.employee'].sudo().browse(employee_id)
        if not employee.exists():
            request.session.pop('employee_number', None)
            return None
        return employee

    def _calculate_stats(self, employee, attendances, start_date, end_date):
        absent_days = self._get_absent_days(employee)
        present_days = len(attendances)
        late_count = sum(1 for a in attendances if getattr(a, 'display_late_minutes', 0) > 0)
        total_days = (end_date.date() - start_date.date()).days + 1

        return {
            'attendanceCount': present_days,
            'absentCount': len(absent_days),
            'lateCount': late_count,
            'total_days': total_days,
        }

    def _get_calendar_data(self, employee, year, month):
        calendar_data = {}
        _, num_days = calendar.monthrange(year, month)

        for day in range(1, num_days + 1):
            current_date = date(year, month, day)
            weekday = current_date.weekday()

            day_att = request.env['hr.attendance'].sudo().search([
                ('employee_id', '=', employee.id),
                ('check_in', '>=', datetime(year, month, day)),
                ('check_in', '<', datetime(year, month, day, 23, 59, 59))
            ], limit=1)

            check_in = day_att.check_in.astimezone(MYANMAR_TZ) if day_att and day_att.check_in else None
            check_out = day_att.check_out.astimezone(MYANMAR_TZ) if day_att and day_att.check_out else None

            late_minutes = 0
            is_late = False
            severity = None

            if day_att and getattr(day_att, 'display_late_minutes', "00:00") != "00:00":
                display_late = day_att.display_late_minutes
                if isinstance(display_late, float):
                    hours = int(display_late)
                    minutes = int((display_late - hours) * 60)
                else:
                    try:
                        hh, mm = display_late.split(":")
                        hours, minutes = int(hh), int(mm)
                    except Exception:
                        hours, minutes = 0, 0
                late_minutes = hours * 60 + minutes

                if late_minutes > 0:
                    is_late = True
                    if late_minutes <= 5:
                        severity = 'low'
                    elif late_minutes <= 15:
                        severity = 'medium'
                    else:
                        severity = 'high'

            calendar_data[day] = {
                'date': current_date,
                'day': day,
                'formatted_date': current_date.strftime('%Y-%m-%d'),
                'check_in_time': check_in.strftime('%H:%M') if check_in else None,
                'check_out_time': check_out.strftime('%H:%M') if check_out else None,
                'is_weekend': weekday >= 5,
                'is_late': is_late,
                'late_minutes': late_minutes,
                'severity': severity,
                'has_check_in': bool(check_in),
                'has_check_out': bool(check_out),
            }

        return calendar_data

    def _get_prev_month(self, year, month):
        if month == 1:
            return {'year': year - 1, 'month': 12}
        return {'year': year, 'month': month - 1}

    def _get_next_month(self, year, month):
        if month == 12:
            return {'year': year + 1, 'month': 1}
        return {'year': year, 'month': month + 1}

    def _get_absent_days(self, employee):
        start_date, end_date = self._get_fiscal_period()
        today = end_date.date()

        attendances = request.env['hr.attendance'].sudo().search([
            ('employee_id', '=', employee.id),
            ('check_in', '>=', start_date),
            ('check_in', '<=', end_date),
        ])

        calendar_id = employee.resource_calendar_id
        end_hour = 17
        if calendar_id and calendar_id.attendance_ids:
            end_hour = max(a.hour_to for a in calendar_id.attendance_ids)

        absent_days = []
        current_date = start_date.date()
        while current_date <= today:
            day_att = attendances.filtered(lambda a: a.check_in.date() == current_date)

            if not day_att:
                if current_date.weekday() < 5:
                    absent_days.append({
                        'date': current_date,
                        'formatted_date': current_date.strftime('%A, %B %d, %Y'),
                        'iso_date': current_date.isoformat(),
                        'status': 'full_absent',
                        'absence_type': 'Full Day Absent'
                    })
            else:
                att = day_att[0]
                check_in = att.check_in.astimezone(MYANMAR_TZ) if att.check_in else None
                check_out = att.check_out.astimezone(MYANMAR_TZ) if att.check_out else None

                if not check_in and check_out:
                    absent_days.append({
                        'date': current_date,
                        'formatted_date': current_date.strftime('%A, %B %d, %Y'),
                        'iso_date': current_date.isoformat(),
                        'status': 'half_absent',
                        'absence_type': 'Morning Absent',
                        'check_out_time': check_out.strftime('%H:%M')
                    })
                elif check_in and not check_out:
                    if current_date == today:
                        now_hour = self._now_myanmar().hour
                        if now_hour >= end_hour:
                            absent_days.append({
                                'date': current_date,
                                'formatted_date': current_date.strftime('%A, %B %d, %Y'),
                                'iso_date': current_date.isoformat(),
                                'status': 'half_absent',
                                'absence_type': 'Evening Absent',
                                'check_in_time': check_in.strftime('%H:%M')
                            })
                    else:
                        absent_days.append({
                            'date': current_date,
                            'formatted_date': current_date.strftime('%A, %B %d, %Y'),
                            'iso_date': current_date.isoformat(),
                            'status': 'half_absent',
                            'absence_type': 'Evening Absent',
                            'check_in_time': check_in.strftime('%H:%M')
                        })

            current_date += timedelta(days=1)

        return absent_days

    def _get_late_days(self, employee):
        start_date, end_date = self._get_fiscal_period()

        attendances = request.env['hr.attendance'].sudo().search([
            ('employee_id', '=', employee.id),
            ('check_in', '>=', start_date),
            ('check_in', '<=', end_date)
        ])

        late_days = []
        total_late_minutes = 0

        for att in attendances:
            display_late = getattr(att, "display_late_minutes", "00:00")
            if display_late != "00:00":
                check_in_local = att.check_in.astimezone(MYANMAR_TZ) if att.check_in else None
                if isinstance(display_late, float):
                    hours = int(display_late)
                    minutes = int((display_late - hours) * 60)
                else:
                    hh, mm = display_late.split(":")
                    hours, minutes = int(hh), int(mm)

                late_minutes = hours * 60 + minutes
                if late_minutes == 0:
                    continue

                total_late_minutes += late_minutes
                if late_minutes <= 5:
                    severity = 'low'
                elif late_minutes <= 15:
                    severity = 'medium'
                else:
                    severity = 'high'

                late_days.append({
                    'date': check_in_local.date() if check_in_local else None,
                    'iso_date': check_in_local.strftime('%Y-%m-%d') if check_in_local else "",
                    'formatted_date': check_in_local.strftime('%A, %B %d, %Y') if check_in_local else "",
                    'check_in_time': check_in_local.strftime('%H:%M') if check_in_local else None,
                    'late_minutes': late_minutes,
                    'severity': severity,
                })

        avg_lateness = total_late_minutes / len(late_days) if late_days else 0
        return late_days, total_late_minutes, avg_lateness
