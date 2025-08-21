# -*- coding: utf-8 -*-
################################################################################
#
#    Biometric Device Integration for Odoo
#    Extended to support multiple calendars and night shifts with idempotency
#
################################################################################

import datetime
import time
import logging
import pytz
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)

try:
    from zk import ZK, const
except Exception:  # pragma: no cover - optional dependency at runtime
    ZK = None


class BiometricDeviceDetails(models.Model):
    _name = 'biometric.device.details'
    _description = 'Biometric Device Details'

    name = fields.Char(string='Name', required=True)
    device_ip = fields.Char(string='Device IP', required=True)
    port_number = fields.Integer(string='Port Number', required=True)
    address_id = fields.Many2one('res.partner', string='Working Address')
    company_id = fields.Many2one('res.company', default=lambda self: self.env.user.company_id.id)
    last_pull_at = fields.Datetime(string='Last Pull At')

    def _get_connection_object(self):
        if ZK is None:
            raise UserError(_("Pyzk module not found. Please install it with 'pip3 install pyzk'."))
        try:
            return ZK(self.device_ip, port=self.port_number, timeout=30, password=0, ommit_ping=False)
        except Exception as exc:  # defensive
            raise UserError(str(exc))

    def device_connect(self, zk):
        try:
            return zk.connect()
        except Exception as e:
            _logger.error("Connection failed: %s", e)
            return False

    def action_test_connection(self):
        zk = self._get_connection_object()
        try:
            conn = zk.connect()
            conn.disconnect()
            return {'type': 'ir.actions.client', 'tag': 'display_notification',
                    'params': {'message': 'Successfully Connected', 'type': 'success', 'sticky': False}}
        except Exception as error:
            raise ValidationError(f'{error}')

    def action_set_timezone(self):
        for info in self:
            zk = info._get_connection_object()
            conn = info.device_connect(zk)
            if conn:
                try:
                    user_tz = self.env.context.get('tz') or self.env.user.tz or 'UTC'
                    now_utc = pytz.utc.localize(fields.Datetime.now())
                    user_time = now_utc.astimezone(pytz.timezone(user_tz))
                    conn.set_time(user_time)
                    conn.disconnect()
                    return {
                        'type': 'ir.actions.client',
                        'tag': 'display_notification',
                        'params': {
                            'message': 'Successfully Set the Time',
                            'type': 'success',
                            'sticky': False
                        }
                    }
                except Exception as e:
                    raise UserError(_("Failed to set device time: %s") % str(e))
            else:
                raise UserError(_("Connection failed. Please check the device settings."))

    def action_clear_attendance(self):
        for info in self:
            self._cr.execute("DELETE FROM zk_machine_attendance")

    # --- Helpers ---
    def _float_hour_to_time(self, float_hour):
        if float_hour is None:
            return None
        hours = int(float_hour)
        minutes = int(round((float_hour - hours) * 60))
        if minutes >= 60:
            hours += 1
            minutes -= 60
        return datetime.time(hours % 24, minutes)

    def _get_employee_working_hours(self, employee, punch_date):
        # Support either single or multi calendars
        calendars = getattr(employee, 'resource_calendar_ids', False) or employee.resource_calendar_id
        if not calendars:
            return []
        if isinstance(calendars, models.Model):
            calendars = [calendars]
        weekday = punch_date.weekday()
        lines = self.env['resource.calendar.attendance']
        for cal in calendars:
            lines |= cal.attendance_ids.filtered(lambda a: int(a.dayofweek) == weekday)
        return lines.sorted('hour_from')

    def _select_shift_type(self, employee, punch_datetime):
        punch_date = punch_datetime.date()
        working_hours = self._get_employee_working_hours(employee, punch_date)
        if not working_hours:
            return 'night', [(datetime.time(16, 45), datetime.time(8, 45))]
        slots = [(self._float_hour_to_time(s.hour_from), self._float_hour_to_time(s.hour_to)) for s in working_hours]
        # Night shift if a slot crosses midnight
        if slots[0][1] < slots[0][0]:
            return 'night', slots
        else:
            return 'day', slots

    def _compute_night_window(self, employee, punch_dt, device_tz):
        """Compute night-shift window using calendar days, not generic anchors.

        - First day start: the latest slot start time of the FIRST day
          (previous day if punch is morning, current day if punch is evening)
        - Second day end: the earliest slot end time of the SECOND day
          (current day if punch is morning, next day if punch is evening)
        """
        today = punch_dt.date()
        slots_today = self._get_employee_working_hours(employee, today)
        if not slots_today:
            # fallback
            first_start_time = datetime.time(16, 45)
            second_end_time = datetime.time(8, 45)
            # decide orientation by time
            if punch_dt.time() <= second_end_time:
                start_date = today - datetime.timedelta(days=1)
                end_date = today
            else:
                start_date = today
                end_date = today + datetime.timedelta(days=1)
            return (
                device_tz.localize(datetime.datetime.combine(start_date, first_start_time)),
                device_tz.localize(datetime.datetime.combine(end_date, second_end_time)),
            )

        # derive day-specific times
        first_start_today = max((self._float_hour_to_time(s.hour_from) for s in slots_today), default=datetime.time(16, 45))
        second_end_today = min((self._float_hour_to_time(s.hour_to) for s in slots_today), default=datetime.time(8, 45))

        if punch_dt.time() <= second_end_today:
            # Morning side → first day is yesterday, second day is today
            prev_date = today - datetime.timedelta(days=1)
            slots_prev = self._get_employee_working_hours(employee, prev_date)
            first_start_prev = max((self._float_hour_to_time(s.hour_from) for s in slots_prev), default=first_start_today)
            start_dt = device_tz.localize(datetime.datetime.combine(prev_date, first_start_prev))
            end_dt = device_tz.localize(datetime.datetime.combine(today, second_end_today))
        else:
            # Evening side → first day is today, second day is tomorrow
            next_date = today + datetime.timedelta(days=1)
            slots_next = self._get_employee_working_hours(employee, next_date)
            second_end_next = min((self._float_hour_to_time(s.hour_to) for s in slots_next), default=second_end_today)
            start_dt = device_tz.localize(datetime.datetime.combine(today, first_start_today))
            end_dt = device_tz.localize(datetime.datetime.combine(next_date, second_end_next))

        return start_dt, end_dt

    # --- Core download and processing ---
    def action_download_attendance(self):
        start_time = time.time()
        _logger.info("Downloading attendance...")

        zk_attendance = self.env['zk.machine.attendance']
        hr_attendance = self.env['hr.attendance']

        today_local = fields.Date.context_today(self)
        device_tz = pytz.timezone('Asia/Rangoon')

        for info in self:
            zk = self._get_connection_object()
            conn = self.device_connect(zk)
            if not conn:
                raise UserError(_("Unable to connect to device"))

            try:
                conn.disable_device()
                # Pull from device
                all_attendance = conn.get_attendance()

                # Stage to zk.machine.attendance with unique constraint
                for att in all_attendance:
                    raw_ts = att.timestamp
                    local_dt = device_tz.localize(raw_ts) if raw_ts.tzinfo is None else raw_ts.astimezone(device_tz)
                    att_date = local_dt.date()
                    # Only keep recent data (today by default)
                    if att_date != today_local:
                        continue
                    employee = self.env['hr.employee'].search([('employee_number', '=', att.user_id)], limit=1)
                    if not employee:
                        continue
                    utc_dt = local_dt.astimezone(pytz.utc)
                    punching_time = fields.Datetime.to_string(utc_dt)
                    if not zk_attendance.search([('device_id_num', '=', str(att.user_id)),
                                                 ('punching_time', '=', punching_time)], limit=1):
                        zk_attendance.create({
                            'employee_id': employee.id,
                            'device_id_num': str(att.user_id),
                            'attendance_type': str(getattr(att, 'status', '1')),
                            'punch_type': str(getattr(att, 'punch', '0')),
                            'punching_time': punching_time,
                            'address_id': info.address_id.id,
                        })

                # Process unprocessed punches for today
                to_process = zk_attendance.search([
                    ('processed', '=', False),
                ])

                for row in to_process:
                    emp = row.employee_id
                    if not emp:
                        continue

                    punch = fields.Datetime.from_string(row.punching_time)
                    punch = pytz.utc.localize(punch) if punch.tzinfo is None else punch
                    punch = punch.astimezone(device_tz)

                    shift_type, slots = self._select_shift_type(emp, punch)

                    # Idempotency: skip if already materialized
                    punch_utc_str = fields.Datetime.to_string(punch.astimezone(pytz.utc))
                    exists = hr_attendance.search(['|', ('check_in', '=', punch_utc_str), ('check_out', '=', punch_utc_str),
                                                   ('employee_id', '=', emp.id)], limit=1)
                    if exists:
                        row.write({'processed': True, 'hr_attendance_id': exists.id})
                        continue

                    created_or_found_id = False

                    if shift_type == 'day':
                        first_start, first_end = slots[0]
                        second_start, second_end = slots[1] if len(slots) > 1 else (None, None)

                        if punch.time() <= first_end:
                            created_or_found_id = hr_attendance.create({
                                'employee_id': emp.id,
                                'check_in': punch_utc_str,
                            }).id
                        elif second_start and first_end < punch.time() <= second_end:
                            prev_att = hr_attendance.search([
                                ('employee_id', '=', emp.id),
                                ('check_out', '=', False),
                                ('check_in', '!=', False),
                                ('check_in', '>=', fields.Datetime.to_string(datetime.datetime.combine(punch.date(), datetime.time(0, 0))))
                            ], order="check_in desc", limit=1)
                            if prev_att:
                                prev_att.write({'check_out': punch_utc_str})
                                created_or_found_id = prev_att.id
                            else:
                                created_or_found_id = hr_attendance.create({
                                    'employee_id': emp.id,
                                    'check_in': punch_utc_str,
                                }).id
                        else:
                            prev_att = hr_attendance.search([
                                ('employee_id', '=', emp.id),
                                ('check_out', '=', False)
                            ], order="check_in desc", limit=1)
                            if prev_att:
                                prev_att.write({'check_out': punch_utc_str})
                                created_or_found_id = prev_att.id
                            else:
                                created_or_found_id = hr_attendance.create({
                                    'employee_id': emp.id,
                                    'check_in': False,
                                    'check_out': punch_utc_str,
                                }).id

                    else:
                        # Night shift handling: build window from day-specific calendar
                        shift_start_dt, shift_end_dt = self._compute_night_window(emp, punch, device_tz)

                        checkin_window_start = shift_start_dt - datetime.timedelta(hours=2)
                        checkin_window_end = shift_start_dt + datetime.timedelta(hours=4)
                        morning_checkout_cutoff = shift_end_dt + datetime.timedelta(hours=2)

                        if checkin_window_start <= punch <= checkin_window_end:
                            created_or_found_id = hr_attendance.create({
                                'employee_id': emp.id,
                                'check_in': punch_utc_str,
                            }).id
                        elif punch <= morning_checkout_cutoff:
                            prev_att = hr_attendance.search([
                                ('employee_id', '=', emp.id),
                                ('check_out', '=', False)
                            ], order="check_in desc", limit=1)
                            if prev_att:
                                prev_att.write({'check_out': punch_utc_str})
                                created_or_found_id = prev_att.id
                            else:
                                created_or_found_id = hr_attendance.create({
                                    'employee_id': emp.id,
                                    'check_in': False,
                                    'check_out': punch_utc_str,
                                }).id
                        else:
                            prev_att = hr_attendance.search([
                                ('employee_id', '=', emp.id),
                                ('check_out', '=', False)
                            ], order="check_in desc", limit=1)
                            if prev_att:
                                prev_att.write({'check_out': punch_utc_str})
                                created_or_found_id = prev_att.id
                            else:
                                created_or_found_id = hr_attendance.create({
                                    'employee_id': emp.id,
                                    'check_in': False,
                                    'check_out': punch_utc_str,
                                }).id

                    row.write({'processed': True, 'hr_attendance_id': created_or_found_id or False})

            finally:
                try:
                    conn.enable_device()
                except Exception:
                    pass
                try:
                    conn.disconnect()
                except Exception:
                    pass

        total_time = time.time() - start_time
        _logger.info(f"Attendance download completed in {total_time:.2f} seconds.")
        return True

