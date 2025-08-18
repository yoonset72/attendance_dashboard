from odoo import http
from odoo.http import request
import logging
from datetime import datetime 
_logger = logging.getLogger(__name__)

class EmployeePortal(http.Controller):

    @http.route('/employee/register', type='http', auth='public', website=True, methods=['GET', 'POST'], csrf=False)
    def employee_register(self, **kwargs):
        _logger.info("Rendering employee register template with context: %s", kwargs)

        if http.request.httprequest.method == 'POST':
            input_emp_id = kwargs.get('employee_number')
            password = kwargs.get('password')
            new_password = kwargs.get('new_password')
            forgot = kwargs.get('forgot')

            employee = request.env['hr.employee'].sudo().search([('employee_number', '=', input_emp_id)], limit=1)

            _logger.info("Incoming employee data: %s", employee)
            if not employee:
                # Wrong Employee ID
                return request.render('attendance_dashboard.register_template', {
                    'error': 'Employee ID not found.',
                    'employee_number': input_emp_id,
                    'forgot': False,
                })

            login_record = request.env['employee.login'].sudo().search([('employee_number', '=', employee.id)], limit=1)

            if not login_record:
                # Register new employee login
                request.env['employee.login'].sudo().create({
                    'employee_number': employee.id,
                    'password': password
                })
                request.session['employee_number'] = employee.id
                return request.redirect('/employee/profile')

            if forgot:
                # Only show reset template if user explicitly clicked "Forgot Password"
                if not new_password:
                    return request.render('attendance_dashboard.register_template', {
                        'error': 'Please enter a new password.',
                        'employee_number': input_emp_id,
                        'forgot': True
                    })
                login_record.sudo().write({'password': new_password})
                return request.render('attendance_dashboard.register_template', {
                    'success': 'Password updated successfully. Please log in again.',
                    'employee_number': input_emp_id,
                    'forgot': False
                })
            else:
                # User is trying to login
                if login_record.password == password:
                    request.session['employee_number'] = employee.id
                    return request.redirect('/attendance/dashboard')
                else:
                    # Correct ID but wrong password, show noti, do NOT show reset template
                    return request.render('attendance_dashboard.register_template', {
                        'error': 'Wrong password.',
                        'employee_number': input_emp_id,
                        'forgot': False
                    })
        else:
            # GET method - show form
            employee_number = kwargs.get('employee_number', '')
            forgot = kwargs.get('forgot', '')
            return request.render('attendance_dashboard.register_template', {
                'employee_number': employee_number,
                'forgot': forgot.lower() in ['1', 'true', 'yes'],
            })

