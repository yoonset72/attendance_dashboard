from odoo import models, fields

class EmployeeLogin(models.Model):
    _name = 'employee.login'
    _description = 'Employee Login'
    
    employee_number = fields.Many2one('hr.employee', required=True)
    password = fields.Char(required=True)