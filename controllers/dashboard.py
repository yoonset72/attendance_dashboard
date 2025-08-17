from odoo import http
from odoo.http import request
from datetime import datetime, timedelta
import calendar
import json
import logging

_logger = logging.getLogger(__name__)

class AttendanceDashboardController(http.Controller):

    @http.route('/attendance/dashboard', type='http', auth='public', website=True)
    def attendance_dashboard(self, **kwargs):
        """Main attendance dashboard route - uses session employee_number"""
        # Check if employee is logged in via session
        employee_id = request.session.get('employee_number')
        if not employee_id:
            return request.redirect('/employee/register')
        
        employee = request.env['hr.employee'].sudo().browse(employee_id)
        
        if not employee.exists():
            # Clear invalid session and redirect to register
            request.session.pop('employee_number', None)
            return request.redirect('/employee/register')
        
        # Get current month stats
        today = datetime.now()
        start_of_month = today.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        end_of_month = (start_of_month + timedelta(days=32)).replace(day=1) - timedelta(days=1)
        
        attendances = request.env['hr.attendance'].sudo().search([
            ('employee_id', '=', employee.id),
            ('check_in', '>=', start_of_month),
            ('check_in', '<=', end_of_month)
        ])
        
        stats = self._calculate_stats(employee, attendances, start_of_month, end_of_month)
        
        return request.render('attendance_dashboard.main_dashboard', {
            'employee': employee,
            'stats': stats,
            'current_month': today.strftime('%B %Y'),
            'company_info': {
                'name': 'AGB Communication',
                'country': 'Myanmar',
                'phone': '+959-765492075',
                'email': 'hr@agbcommunication.com'
            }
        })

    @http.route('/attendance/calendar', type='http', auth='public', website=True)
    def attendance_calendar(self, year=None, month=None, **kwargs):
        """Attendance calendar view"""
        # Check if employee is logged in via session
        employee_id = request.session.get('employee_number')
        if not employee_id:
            return request.redirect('/employee/register')
        
        employee = request.env['hr.employee'].sudo().browse(employee_id)
        
        if not employee.exists():
            request.session.pop('employee_number', None)
            return request.redirect('/employee/register')
        
        # Default to current month if not specified
        if not year or not month:
            today = datetime.now()
            year = int(year) if year else today.year
            month = int(month) if month else today.month
        else:
            year = int(year)
            month = int(month)
        
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

    @http.route('/attendance/absent', type='http', auth='public', website=True)
    def absent_details(self, **kwargs):
        """Absent days details view"""
        # Check if employee is logged in via session
        employee_id = request.session.get('employee_number')
        if not employee_id:
            return request.redirect('/employee/register')
        
        employee = request.env['hr.employee'].sudo().browse(employee_id)
        
        if not employee.exists():
            request.session.pop('employee_number', None)
            return request.redirect('/employee/register')
        
        absent_days = self._get_absent_days(employee)
        
        return request.render('attendance_dashboard.absent_details', {
            'employee': employee,
            'absent_days': absent_days,
            'total_absent': len(absent_days),
            'current_month': datetime.now().strftime('%B %Y')
        })

    @http.route('/attendance/late', type='http', auth='public', website=True)
    def late_details(self, **kwargs):
        """Late arrivals details view"""
        # Check if employee is logged in via session
        employee_id = request.session.get('employee_number')
        if not employee_id:
            return request.redirect('/employee/register')
        
        employee = request.env['hr.employee'].sudo().browse(employee_id)
        
        if not employee.exists():
            request.session.pop('employee_number', None)
            return request.redirect('/employee/register')
        
        late_days = self._get_late_days(employee)
        total_late_minutes = sum(day['late_minutes'] for day in late_days)
        avg_lateness = round(total_late_minutes / len(late_days)) if late_days else 0
        
        return request.render('attendance_dashboard.late_details', {
            'employee': employee,
            'late_days': late_days,
            'total_late_days': len(late_days),
            'total_late_minutes': total_late_minutes,
            'avg_lateness': avg_lateness,
            'current_month': datetime.now().strftime('%B %Y')
        })

    @http.route('/attendance/logout', type='http', auth='public', website=True)
    def attendance_logout(self, **kwargs):
        """Logout and clear session"""
        request.session.pop('employee_number', None)
        return request.redirect('/employee/register')

    def _calculate_stats(self, employee, attendances, start_date, end_date):
        """Calculate attendance statistics"""
        # Count unique days with attendance
        attendance_days = set()
        late_count = 0
        
        for attendance in attendances:
            day = attendance.check_in.date()
            attendance_days.add(day)
            
            # Check if late (assuming 9:00 AM start time)
            if attendance.check_in.hour > 9 or (attendance.check_in.hour == 9 and attendance.check_in.minute > 0):
                late_count += 1
        
        # Count working days in month (excluding weekends)
        working_days = 0
        current_date = start_date.date()
        end = end_date.date()
        
        while current_date <= end:
            if current_date.weekday() < 5:  # Monday = 0, Friday = 4
                working_days += 1
            current_date += timedelta(days=1)
        
        attendance_count = len(attendance_days)
        absent_count = working_days - attendance_count
        
        return {
            'attendanceCount': attendance_count,
            'absentCount': max(0, absent_count),
            'lateCount': late_count
        }

    def _get_calendar_data(self, employee, year, month):
        """Get calendar data for the month"""
        start_date = datetime(year, month, 1)
        if month == 12:
            end_date = datetime(year + 1, 1, 1) - timedelta(days=1)
        else:
            end_date = datetime(year, month + 1, 1) - timedelta(days=1)
        
        attendances = request.env['hr.attendance'].sudo().search([
            ('employee_id', '=', employee.id),
            ('check_in', '>=', start_date),
            ('check_in', '<=', end_date)
        ])
        
        # Group by date
        calendar_data = {}
        days_in_month = calendar.monthrange(year, month)[1]
        
        for day in range(1, days_in_month + 1):
            date = datetime(year, month, day).date()
            is_weekend = date.weekday() >= 5
            
            day_attendances = attendances.filtered(
                lambda a: a.check_in.date() == date
            )
            
            check_in = None
            check_out = None
            
            if day_attendances:
                check_in = day_attendances[0].check_in
                if day_attendances[0].check_out:
                    check_out = day_attendances[0].check_out
            
            calendar_data[day] = {
                'date': date,
                'is_weekend': is_weekend,
                'check_in': check_in,
                'check_out': check_out,
                'has_check_in': bool(check_in),
                'has_check_out': bool(check_out)
            }
        
        return calendar_data

    def _get_absent_days(self, employee):
        """Get list of absent days for current month"""
        today = datetime.now()
        start_of_month = today.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        end_of_month = (start_of_month + timedelta(days=32)).replace(day=1) - timedelta(days=1)
        
        attendances = request.env['hr.attendance'].sudo().search([
            ('employee_id', '=', employee.id),
            ('check_in', '>=', start_of_month),
            ('check_in', '<=', end_of_month)
        ])
        
        attended_dates = set(att.check_in.date() for att in attendances)
        absent_days = []
        
        current_date = start_of_month.date()
        while current_date <= end_of_month.date():
            if current_date.weekday() < 5 and current_date not in attended_dates:
                absent_days.append({
                    'date': current_date,
                    'formatted_date': current_date.strftime('%A, %B %d, %Y'),
                    'iso_date': current_date.isoformat()
                })
            current_date += timedelta(days=1)
        
        return absent_days

    def _get_late_days(self, employee):
        """Get list of late arrival days for current month"""
        today = datetime.now()
        start_of_month = today.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        end_of_month = (start_of_month + timedelta(days=32)).replace(day=1) - timedelta(days=1)
        
        attendances = request.env['hr.attendance'].sudo().search([
            ('employee_id', '=', employee.id),
            ('check_in', '>=', start_of_month),
            ('check_in', '<=', end_of_month)
        ])
        
        late_days = []
        standard_start = 9  # 9:00 AM
        
        for attendance in attendances:
            check_in_hour = attendance.check_in.hour
            check_in_minute = attendance.check_in.minute
            
            if check_in_hour > standard_start or (check_in_hour == standard_start and check_in_minute > 0):
                late_minutes = (check_in_hour - standard_start) * 60 + check_in_minute
                
                late_days.append({
                    'date': attendance.check_in.date(),
                    'formatted_date': attendance.check_in.strftime('%A, %B %d, %Y'),
                    'iso_date': attendance.check_in.date().isoformat(),
                    'check_in': attendance.check_in,
                    'check_in_time': attendance.check_in.strftime('%I:%M %p'),
                    'late_minutes': late_minutes,
                    'severity': self._get_lateness_severity(late_minutes)
                })
        
        return late_days

    def _get_lateness_severity(self, minutes):
        """Get lateness severity level"""
        if minutes <= 10:
            return 'low'
        elif minutes <= 20:
            return 'medium'
        else:
            return 'high'

    def _get_prev_month(self, year, month):
        """Get previous month and year"""
        if month == 1:
            return {'year': year - 1, 'month': 12}
        return {'year': year, 'month': month - 1}

    def _get_next_month(self, year, month):
        """Get next month and year"""
        if month == 12:
            return {'year': year + 1, 'month': 1}
        return {'year': year, 'month': month + 1}