from odoo import models, fields, api
from passlib.context import CryptContext
import uuid

# Create a reusable context with the same algorithm as Odoo uses
pwd_context = CryptContext(schemes=["pbkdf2_sha512"], deprecated="auto")

class EmployeeLogin(models.Model):
    _name = 'employee.login'
    _description = 'Employee Login'
    
    employee_number = fields.Many2one('hr.employee', required=True)
    password = fields.Char(required=True)
    login_token = fields.Char(string='Login Token', readonly=True)

    def _hash_password(self, raw_password):
        return pwd_context.hash(raw_password)

    @api.model
    def create(self, vals):
        if vals.get('password'):
            vals['password'] = self._hash_password(vals['password'])
        if not vals.get('login_token'):
            vals['login_token'] = str(uuid.uuid4())
        return super().create(vals)

    def write(self, vals):
        if vals.get('password'):
            vals['password'] = self._hash_password(vals['password'])
        return super().write(vals)

    def check_password(self, raw_password):
        """Compare the hashed DB password with raw input using pbkdf2_sha512."""
        try:
            return pwd_context.verify(raw_password, self.password)
        except Exception:
            return False
