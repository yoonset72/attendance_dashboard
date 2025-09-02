from odoo import http
from odoo.http import request
import logging
import uuid
import json

_logger = logging.getLogger(__name__)

class EmployeePortal(http.Controller):

    @http.route('/employee/register', type='http', auth='public', website=True, methods=['GET', 'POST'], csrf=False)
    def employee_register(self, **kwargs):
        _logger.info("Rendering employee register: %s", kwargs)

        # Auto-redirect if already logged in
        if request.session.get('employee_number'):
            return request.redirect('/attendance/dashboard')

        if request.httprequest.method == 'POST':
            emp_id = kwargs.get('employee_number')
            password = kwargs.get('password')
            new_password = kwargs.get('new_password')
            forgot = kwargs.get('forgot')

            employee = request.env['hr.employee'].sudo().search(
                [('employee_number', '=', emp_id)], limit=1)
            if not employee:
                return request.render('attendance_dashboard.register_template', {
                    'error': 'Employee ID not found.',
                    'employee_number': emp_id,
                    'forgot': False,
                })

            login_rec = request.env['employee.login'].sudo().search(
                [('employee_number', '=', employee.id)], limit=1)

            if not login_rec:  # register
                login_rec = request.env['employee.login'].sudo().create({
                    'employee_number': employee.id,
                    'password': password,
                })

            if forgot:  # reset password
                if not new_password:
                    return request.render('attendance_dashboard.register_template', {
                        'error': 'Please enter a new password.',
                        'employee_number': emp_id,
                        'forgot': True
                    })
                login_rec.sudo().write({'password': new_password})
                return request.render('attendance_dashboard.register_template', {
                    'success': 'Password updated successfully. Please log in again.',
                    'employee_number': emp_id,
                    'forgot': False
                })

            # Attempt login
            if login_rec.check_password(password):
                request.session['employee_number'] = employee.id
                token = str(uuid.uuid4())
                login_rec.sudo().write({'login_token': token})
                if 'Mobile' in request.httprequest.headers.get('User-Agent', ''):
                    return request.make_response(
                        json.dumps({'status': 'success', 'token': token}),
                        headers={'Content-Type': 'application/json'}
                    )
                else:
                    return request.redirect('/attendance/dashboard')

            else:
                return request.render('attendance_dashboard.register_template', {
                    'error': 'Wrong password.',
                    'employee_number': emp_id,
                    'forgot': False
                })

        # GET request
        return request.render('attendance_dashboard.register_template', {
            'employee_number': kwargs.get('employee_number', ''),
            'forgot': kwargs.get('forgot', '').lower() in ['1', 'true', 'yes'],
        })
