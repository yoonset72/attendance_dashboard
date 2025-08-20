from odoo import api, fields, models
from odoo.exceptions import ValidationError


class ZkMachineAttendance(models.Model):
    """Model to hold data from the biometric device.
    Inherits hr.attendance so we can optionally link/use those fields.
    Also acts as a staging table with idempotency helpers.
    """
    _name = 'zk.machine.attendance'
    _description = 'Attendance'
    _inherit = 'hr.attendance'
    _rec_name = 'punching_time'

    device_id_num = fields.Char(string='Biometric Device ID', help="The ID of the Biometric Device", index=True)
    punch_type = fields.Selection([
        ('0', 'Check In'), ('1', 'Check Out'),
        ('2', 'Break Out'), ('3', 'Break In'),
        ('4', 'Overtime In'), ('5', 'Overtime Out'),
        ('255', 'Duplicate')],
        string='Punching Type', help='Punching type of the attendance')

    attendance_type = fields.Selection([
        ('1', 'Finger'), ('15', 'Face'), ('2', 'Type_2'),
        ('3', 'Password'), ('4', 'Card'), ('255', 'Duplicate')],
        string='Category', help="Attendance detecting methods")

    punching_time = fields.Datetime(string='Punching Time', help="Punching time in the device", index=True)
    address_id = fields.Many2one('res.partner', string='Working Address', help="Working address of the employee")

    late_minutes = fields.Integer(string='Late Minutes', default=0)
    early_checkout_minutes = fields.Integer(string='Early Checkout Minutes', default=0)

    # Idempotency helpers
    processed = fields.Boolean(default=False, index=True)
    hr_attendance_id = fields.Many2one('hr.attendance', string='Linked Attendance')

    _sql_constraints = [
        (
            'uniq_device_punch',
            'unique(device_id_num, punching_time)',
            'This device punch is already stored.'
        ),
    ]

