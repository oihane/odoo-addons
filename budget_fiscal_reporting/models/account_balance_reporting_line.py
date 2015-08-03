# -*- encoding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################

from openerp import models, fields, api
from openerp.addons import decimal_precision as dp
from datetime import datetime
import re


class AccountBalanceReportingLine(models.Model):

    """
    Account balance report line / Accounting concept
    One line of detail of the balance report representing an accounting
    concept with its values.
    The accounting concepts follow a parent-children hierarchy.
    Its values (current and previous) are calculated based on the 'value'
    formula of the linked template line.
    """

    _inherit = 'account.balance.reporting.line'

    budget_amount = fields.Float(string="Budget Amount",
                                 digits=dp.get_precision('Account'))
    acubud_amount = fields.Float(string='Acumulated Budget Amount',
                                 digits=dp.get_precision('Account'))

    @api.multi
    def refresh_monthly_values(self):
        super(AccountBalanceReportingLine, self).refresh_monthly_values()
        acc_obj = self.env['account.account']
        pro_bgt_obj = self.env['product.budget.line']
        for self_o in self:
            if not (self_o.month_start_date and self_o.month_end_date and
                    self_o.month_report_id):
                continue
            account_ids = []
            if (self_o.template_line_id and
                    self_o.template_line_id.current_value):
                tmpl_value = self_o.template_line_id.current_value
                tmpl_value = tmpl_value.split(';')[0]
                for acc_code in re.findall(
                        r'(-?\w*\(?[0-9a-zA-Z_]*\)?)', tmpl_value):
                    if acc_code.startswith('-'):
                        # Strip the sign
                        acc_code = acc_code[1:].strip()
                    if re.match(r'^debit\(.*\)$', acc_code):
                        # Strip debit()
                        acc_code = acc_code[6:-1]
                    elif re.match(r'^credit\(.*\)$', acc_code):
                        # Strip credit()
                        acc_code = acc_code[7:-1]
                    if acc_code.startswith('(') and \
                            acc_code.endswith(')'):
                        acc_code = acc_code[1:-1]
                        # Search for the account (perfect match)
                    comp_id = self_o.month_report_id.company_id.id
                    account_lst = acc_obj.search([('code', '=', acc_code),
                                                  ('company_id', '=', comp_id)
                                                  ])
                    for acc_id in account_lst:
                        child_ids = acc_id._get_children_and_consol()
                        account_ids.extend(child_ids)
            value = 0.0
            value2 = 0.0
            if account_ids:
                start_date = fields.Date.to_string(self_o.month_start_date)
                year_start_date = datetime(start_date.year, 1, 1)
                p_budget_lines = pro_bgt_obj.search(
                    [('budget_line_id', '!=', False),
                     ('budget_line_id.date_from', '>=',
                      self_o.month_start_date),
                     ('budget_line_id.date_to', '<=', self_o.month_end_date),
                     ('account_id', 'in', account_ids)])
                value = sum([x.expected_subtotal for x in p_budget_lines])
                acum_budget_lines = pro_bgt_obj.search(
                    [('budget_line_id', '!=', False),
                     ('budget_line_id.date_from', '>=', year_start_date),
                     ('budget_line_id.date_to', '<=', self_o.month_end_date),
                     ('account_id', 'in', account_ids)])
                value2 = sum([x.expected_subtotal for x in acum_budget_lines])
            self_o.budget_amount = value
            self_o.acubud_amount = value2
        return True
