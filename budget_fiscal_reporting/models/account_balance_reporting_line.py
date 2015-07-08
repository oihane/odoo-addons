# -*- encoding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################

from openerp.osv import orm, fields
import openerp.addons.decimal_precision as dp
#import decimal_precision as dp
import re
from datetime import date, datetime


class AccountBalanceReportingLine(orm.Model):

    """
    Account balance report line / Accounting concept
    One line of detail of the balance report representing an accounting
    concept with its values.
    The accounting concepts follow a parent-children hierarchy.
    Its values (current and previous) are calculated based on the 'value'
    formula of the linked template line.
    """

    _inherit = 'account.balance.reporting.line'

    _columns = {'budget_amount': fields.float("Budget Amount",
                                              digits_compute=dp.get_precision(
                                                  'Account')),
                'acubud_amount': fields.float('Acumulated Budget Amount',
                                              digits_compute=dp.get_precision(
                                                  'Account'))
                }

    def refresh_monthly_values(self, cr, uid, ids, context=None):
        super(AccountBalanceReportingLine, self).refresh_monthly_values(
            cr, uid, ids, context=context)
        acc_obj = self.pool['account.account']
        for id in ids:
            self_o = self.browse(cr, uid, id, context=context)
            if (self_o.month_start_date and self_o.month_end_date and
                    self_o.month_report_id):
                account_ids = []
                tmp_line = self_o.template_line_id
                if tmp_line:
                    tmpl_value = tmp_line.current_value
                    if tmpl_value:
                        tmpl_value = tmpl_value.split(';')[0]
                        for acc_code in re.findall(
                                '(-?\w*\(?[0-9a-zA-Z_]*\)?)', tmpl_value):
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
                            account_lst = acc_obj.search(
                                cr, uid, [('code', '=', acc_code),
                                          ('company_id', '=', comp_id)],
                                context=context)
                            if not isinstance(account_lst, list):
                                account_lst = [account_lst]
                            for acc_id in account_lst:
                                child_ids = acc_obj._get_children_and_consol(
                                    cr, uid, acc_id, context=context)
                                account_ids.extend(child_ids)
                value = 0.0
                value2 = 0.0
                if account_ids:
                    if not isinstance(account_ids, list):
                        account_ids = [account_ids]
                    start_date = datetime.strptime(self_o.month_start_date,
                                                   '%Y-%m-%d')
                    year_start_date = date(start_date.year, 1, 1)
                    print year_start_date
                    query = ("""SELECT sum(expected_subtotal) FROM
                        product_budget_line pbl INNER JOIN
                        crossovered_budget_lines cbl ON pbl.budget_line_id =
                        cbl.id INNER JOIN account_account aa ON aa.id =
                        pbl.account_id WHERE pbl.budget_line_id is not null
                        AND cbl.date_from >= '%s' AND cbl.date_to <= '%s' AND
                        """ % (str(self_o.month_start_date),
                               str(self_o.month_end_date)))
                    query2 = ("""SELECT sum(expected_subtotal) FROM
                        product_budget_line pbl INNER JOIN
                        crossovered_budget_lines cbl ON pbl.budget_line_id =
                        cbl.id INNER JOIN account_account aa ON aa.id =
                        pbl.account_id WHERE pbl.budget_line_id is not null
                        AND cbl.date_from >= '%s' AND cbl.date_to <= '%s' AND
                        """ % (str(year_start_date),
                               str(self_o.month_end_date)))
                    if len(account_ids) == 1:
                        query += "aa.id = " + str(account_ids[0]) + ";"
                        query2 += "aa.id = " + str(account_ids[0]) + ";"
                    else:
                        query += "aa.id in " + str(tuple(account_ids)) + ";"
                        query2 += "aa.id in " + str(tuple(account_ids)) + ";"
                    cr.execute(query)
                    res = cr.fetchall()
                    res_val = res[0][0]
                    if res_val:
                        value = res_val
                    cr.execute(query2)
                    res2 = cr.fetchall()
                    res_val2 = res2[0][0]
                    if res_val2:
                        value2 = res_val2
                self.write(cr, uid, id, {'budget_amount': value,
                                         'acubud_amount': value2},
                           context=context)
        return True
