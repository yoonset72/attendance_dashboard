from odoo import api, fields, models


class ZkMachineAttendance(models.Model):
    _name = 'zk.machine.attendance'
    _description = 'Raw punches from biometric device'
    _rec_name = 'punching_time'

    employee_id = fields.Many2one('hr.employee', required=False, index=True)
    device_id_num = fields.Char(string='Device User ID', required=True, index=True)
    attendance_type = fields.Char(string='Attendance Type')
    punch_type = fields.Char(string='Punch Type')
    punching_time = fields.Datetime(string='Punching Time', required=True, index=True)
    address_id = fields.Many2one('res.partner', string='Working Address')

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

