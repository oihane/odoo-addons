# -*- coding: utf-8 -*-
# (c) 2015 Alfredo de la Fuente - AvanzOSC
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html
import openerp.tests.common as common
from openerp import fields
from dateutil.relativedelta import relativedelta


class TestStockPlanningRule(common.TransactionCase):

    def setUp(self):
        super(TestStockPlanningRule, self).setUp()
        self.company = self.env.ref('base.main_company')
        self.company.write({'custom_stock_planning_rule': True,
                            'stock_planning_min_days': 20,
                            'stock_planning_max_days': 60})
        to_date = fields.Date.to_string(
            fields.Date.from_string(fields.Date.today(self)) +
            relativedelta(days=31))
        wiz_vals = {'company': self.company.id,
                    'days': 7,
                    'to_date': to_date}
        self.wiz = self.env['wiz.stock.planning'].create(wiz_vals)
        self.wiz.calculate_stock_planning()
        self.wiz_orderpoint = self.env[
            'procurement.orderpoint.compute'].create({})
        self.wiz_orderpoint.selected_procure_calculation()

    def test_stock_planning_rule(self):
        orderpoint = self.env['stock.warehouse.orderpoint'].search([])
        orderpoint = orderpoint.filtered(
            lambda r: r.custom_rule_min_qty > 0 or r.custom_rule_max_qty > 0)
        self.assertNotEqual(
            len(orderpoint), 0, 'Not generated custom rules for planning')
