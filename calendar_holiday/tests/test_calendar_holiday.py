# -*- coding: utf-8 -*-
# © 2016 Alfredo de la Fuente - AvanzOSC
# © 2016 Oihane Crucelaegui - AvanzOSC
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

import openerp.tests.common as common
from openerp import fields


class TestCalendarHoliday(common.TransactionCase):

    def setUp(self):
        super(TestCalendarHoliday, self).setUp()
        self.holiday_model = self.env['calendar.holiday']
        self.contract_model = self.env['hr.contract']
        self.calendar_model = self.env['res.partner.calendar']
        self.wiz_model = self.env['wiz.calculate.workable.festive']
        self.today = fields.Date.from_string(fields.Date.today())
        self.employee = self.env['hr.employee'].create({
            'name': 'Test Employee',
        })
        calendar_line_vals = {
            'date': self.today.replace(month=1, day=6),
            'absence_type': self.ref('hr_holidays.holiday_status_comp'),
        }
        calendar_vals = {
            'name': 'Holidays calendar',
            'lines': [(0, 0, calendar_line_vals)],
        }
        self.calendar_holiday = self.holiday_model.create(calendar_vals)
        contract_vals = {
            'name': 'Test Employee Contract',
            'date_start': self.today.replace(month=1, day=1),
            'date_end': self.today.replace(month=12, day=31),
            'employee_id': self.employee.id,
            'wage': 500,
            'holiday_calendars': [(6, 0, [self.calendar_holiday.id])],
        }
        self.contract = self.contract_model.create(contract_vals)

    def test_calendar_holiday(self):
        wiz = self.wiz_model.with_context(
            active_id=self.contract.id).create({'year': self.today.year})
        wiz.button_calculate_workables_and_festives()
