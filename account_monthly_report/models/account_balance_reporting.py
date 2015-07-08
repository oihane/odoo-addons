# -*- encoding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################

from openerp.osv import orm, fields
from openerp.addons import decimal_precision as dp
#import decimal_precision as dp
from datetime import datetime
from dateutil.relativedelta import relativedelta
import re
import logging


class AccountBalanceReporting(orm.Model):
    """
    Account balance report.
    It stores the configuration/header fields of an account balance report,
    and the linked lines of detail with the values of the accounting concepts
    (values generated from the selected template lines of detail formulas).
    """
    _inherit = 'account.balance.reporting'

    def get_months(self, cr, uid, report_id, context=None):
        date_array = []
        date_format = '%Y-%m-%d'
        report_o = self.browse(cr, uid, report_id, context=context)
        if report_o.current_period_ids:
            date_start = report_o.current_period_ids[0].date_start
            date_end = report_o.current_period_ids[0].date_stop
            for period in report_o.current_period_ids:
                if period.date_start < date_start:
                    date_start = period.date_start
                if period.date_stop > date_end:
                    date_end = period.date_stop
            date_start = datetime.strptime(date_start, date_format)
            date_end = datetime.strptime(date_end, date_format)
            date_diff = date_end.month - date_start.month
            while date_diff >= 0:
                date_dict = {}
                today = date_start + relativedelta(months=date_diff)
                initial_date = datetime(today.year, today.month, 1)
                pre_final_date = initial_date + relativedelta(months=1)
                final_date = pre_final_date + relativedelta(days=-1)
                str_initial_date = datetime.strftime(initial_date, date_format)
                str_final_date = datetime.strftime(final_date, date_format)
                date_dict.update({'start_month': str_initial_date,
                                  'end_month': str_final_date})
                date_array.append(date_dict)
                date_diff -= 1
            date_array.reverse()
        return date_array

    _columns = {
        'monthly_line_ids': fields.one2many('account.balance.reporting.line',
                                            'month_report_id', 'Lines',
                                            states={'done': [('readonly',
                                                              True)]}),
        'jan_line_ids': fields.one2many('account.balance.reporting.line',
                                        'month_report_id', 'Lines',
                                        domain=[('month_num', '=', 1)],
                                        states={'done': [('readonly',
                                                          True)]}),
        'feb_line_ids': fields.one2many('account.balance.reporting.line',
                                        'month_report_id', 'Lines',
                                        domain=[('month_num', '=', 2)],
                                        states={'done': [('readonly',
                                                          True)]}),
        'mar_line_ids': fields.one2many('account.balance.reporting.line',
                                        'month_report_id', 'Lines',
                                        domain=[('month_num', '=', 3)],
                                        states={'done': [('readonly',
                                                          True)]}),
        'apr_line_ids': fields.one2many('account.balance.reporting.line',
                                        'month_report_id', 'Lines',
                                        domain=[('month_num', '=', 4)],
                                        states={'done': [('readonly',
                                                          True)]}),
        'may_line_ids': fields.one2many('account.balance.reporting.line',
                                        'month_report_id', 'Lines',
                                        domain=[('month_num', '=', 5)],
                                        states={'done': [('readonly',
                                                          True)]}),
        'jun_line_ids': fields.one2many('account.balance.reporting.line',
                                        'month_report_id', 'Lines',
                                        domain=[('month_num', '=', 6)],
                                        states={'done': [('readonly',
                                                          True)]}),
        'jul_line_ids': fields.one2many('account.balance.reporting.line',
                                        'month_report_id', 'Lines',
                                        domain=[('month_num', '=', 7)],
                                        states={'done': [('readonly',
                                                          True)]}),
        'aug_line_ids': fields.one2many('account.balance.reporting.line',
                                        'month_report_id', 'Lines',
                                        domain=[('month_num', '=', 8)],
                                        states={'done': [('readonly',
                                                          True)]}),
        'sep_line_ids': fields.one2many('account.balance.reporting.line',
                                        'month_report_id', 'Lines',
                                        domain=[('month_num', '=', 9)],
                                        states={'done': [('readonly',
                                                          True)]}),
        'oct_line_ids': fields.one2many('account.balance.reporting.line',
                                        'month_report_id', 'Lines',
                                        domain=[('month_num', '=', 10)],
                                        states={'done': [('readonly',
                                                          True)]}),
        'nov_line_ids': fields.one2many('account.balance.reporting.line',
                                        'month_report_id', 'Lines',
                                        domain=[('month_num', '=', 11)],
                                        states={'done': [('readonly',
                                                          True)]}),
        'dec_line_ids': fields.one2many('account.balance.reporting.line',
                                        'month_report_id', 'Lines',
                                        domain=[('month_num', '=', 12)],
                                        states={'done': [('readonly',
                                                          True)]}),
        }

    def action_calculate(self, cr, uid, ids, context=None):
        res = super(AccountBalanceReporting, self).action_calculate(
            cr, uid, ids, context=context)
        if not context:
            context = {}
        line_obj = self.pool['account.balance.reporting.line']
        for report in self.browse(cr, uid, ids, context=context):
            # Clear the report data (unlink the lines of detail)
            line_obj.unlink(cr, uid, [line.id for line in
                                      report.monthly_line_ids],
                            context=context)
            # Fill the report with a 'copy' of the lines of its template
            # (if it has one)
            date_lst = self.get_months(cr, uid, report.id, context=context)
            for month_date in date_lst:
                if report.template_id:
                    for template_line in report.template_id.line_ids:
                        line_obj.create(cr, uid,
                                        {'code': template_line.code,
                                         'name': template_line.name,
                                         'month_report_id': report.id,
                                         'report_id': False,
                                         'template_line_id': template_line.id,
                                         'parent_id': None,
                                         'current_value': None,
                                         'previous_value': None,
                                         'sequence': template_line.sequence,
                                         'css_class': template_line.css_class,
                                         'month_start_date':
                                            month_date['start_month'],
                                         'month_end_date':
                                            month_date['end_month']
                                         }, context=context)
        # Set the parents of the lines in the report
        # Note: We reload the reports objects to refresh the lines of detail.
        for report in self.browse(cr, uid, ids, context=context):
            if report.template_id:
                # Set line parents (now that they have been created)
                for line in report.monthly_line_ids:
                    tmpl_line = line.template_line_id
                    if tmpl_line and tmpl_line.parent_id:
                        parent_line_ids = line_obj.search(
                            cr, uid, [('month_report_id', '=', report.id),
                                      ('month_start_date', '=',
                                       line.month_start_date),
                                      ('code', '=', tmpl_line.parent_id.code)])
                        line_obj.write(cr, uid, line.id,
                                       {'parent_id': (parent_line_ids and
                                                      parent_line_ids[0] or
                                                      False),
                                        }, context=context)
        # Calculate the values of the lines
        # Note: We reload the reports objects to refresh the lines of detail.
        for report in self.browse(cr, uid, ids, context=context):
            if report.template_id:
                # Refresh the report's lines values
                for line in report.monthly_line_ids:
                    # =========================================================
                    # mirar el código de esta función para los mensuales
                    # =========================================================
                    context.update({'date_from': line.month_start_date,
                                    'date_to': line.month_end_date
                                    })
                    line_obj.refresh_monthly_values(cr, uid, [line.id],
                                                    context=context)
                # Set the report as calculated
                self.write(cr, uid, [report.id], {'state': 'calc_done'},
                           context=context)
            else:
                # Ouch! no template: Going back to draft state.
                self.write(cr, uid, [report.id], {'state': 'draft'},
                           context=context)
        return res


class AccountBalanceReportingLine(orm.Model):

    """
    Account balance report line / Accounting concept
    One line of detail of the balance report representing an accounting
    concept with its values.
    The accounting concepts follow a parent-children hierarchy.
    Its values (current and previous) are calculated based on the 'value'
    formula of the linked template line.
    """

    _inherit = "account.balance.reporting.line"
    _order = 'month_start_date, sequence'

    def _get_month_name(self, cr, uid, ids, name, args, context=None):
        res = {}
        for id in ids:
            value = ''
            value_int = 0
            actual_o = self.browse(cr, uid, id, context=context)
            if actual_o.month_start_date:
                start_date = actual_o.month_start_date
                start_date = datetime.strptime(start_date, '%Y-%m-%d')
                value = datetime.strftime(start_date, "%B")
                value_int = int(datetime.strftime(start_date, '%m'))
            res[id] = {'month_name': value,
                       'month_num': value_int}
        return res

    _columns = {'month_name': fields.function(_get_month_name, method=True,
                                              type="char", size=64,
                                              string="Month", store=True,
                                              multi="month"),
                'month_num': fields.function(_get_month_name, method=True,
                                             type="integer", string="Month",
                                             store=True, multi="month"),
                'month_report_id': fields.many2one('account.balance.reporting',
                                                   'Report',
                                                   ondelete='cascade'),
                'month_start_date': fields.date('Start Date'),
                'month_end_date': fields.date('End Date'),
                'acum_value': fields.float('Acumulated Value',
                                           digits_compute=dp.get_precision(
                                               'Account')),
                }

    def refresh_monthly_values(self, cr, uid, ids, context=None):

        """
        Recalculates the values of this report line using the
        linked line report values formulas:

        Depending on this formula the final value is calculated as follows:
        - Empy report value: sum of (this concept) children values.
        - Number with decimal point ("10.2"): that value (constant).
        - Account numbers separated by commas ("430,431,(437)"): Sum of the
            account balances. (The sign of the balance depends on the balance
            mode)
        - Concept codes separated by "+" ("11000+12000"): Sum of those
            concepts values.
        """

        for line in self.browse(cr, uid, ids, context=context):
            tmpl_line = line.template_line_id
            balance_mode = int(tmpl_line.template_id.balance_mode)
            current_value = 0.0
            previous_value = 0.0
            report = line.month_report_id
            # We use the same code to calculate both fiscal year values,
            # just iterating over them.
            value = 0
            tmpl_value = tmpl_line.current_value
            # Remove characters after a ";" (we use ; for comments)
            if tmpl_value:
                tmpl_value = tmpl_value.split(';')[0]
            if not report.current_fiscalyear_id:
                value = 0
            else:
                if not tmpl_value:
                    # Empy template value => sum of the children values
                    for child in line.child_ids:
                        if child.calc_date != child.month_report_id.calc_date:
                            # Tell the child to refresh its values
                            child.refresh_monthly_values()
                            # Reload the child data
                            child = self.browse(cr, uid, child.id,
                                                context=context)
                        value += child.current_value
                elif re.match(r'^\-?[0-9]*\.[0-9]*$', tmpl_value):
                    # Number with decimal points => that number value
                    # (constant).
                    value = float(tmpl_value)
                elif re.match(r'^[0-9a-zA-Z,\(\)\*_\ ]*$', tmpl_value):
                    # Account numbers separated by commas => sum of the
                    # account balances. We will use the context to filter
                    # the accounts by fiscalyear and periods.
                    value = line._get_account_month_balance(tmpl_value,
                                                            balance_mode,
                                                            context=context)
                elif re.match(r'^[\+\-0-9a-zA-Z_\*\ ]*$', tmpl_value):
                    # Account concept codes separated by "+" => sum of the
                    # concepts (template lines) values.
                    for line_code in re.findall(r'(-?\(?[0-9a-zA-Z_]*\)?)',
                                                tmpl_value):
                        sign = 1
                        if line_code.startswith('-') or \
                                (line_code.startswith('(') and
                                 balance_mode in (2, 4)):
                            sign = -1
                        line_code = line_code.strip('-()*')
                        # findall might return empty strings
                        if line_code:
                            # Search for the line (perfect match)
                            line_ids = self.search(cr, uid,
                                                   [('month_report_id', '=',
                                                     report.id),
                                                    ('code', '=', line_code),
                                                    ('month_start_date', '=',
                                                     line.month_start_date)
                                                    ], context=context)
                            for child in self.browse(cr, uid, line_ids,
                                                     context=context):
                                if (child.calc_date !=
                                        child.month_report_id.calc_date):
                                    child.refresh_monthly_values()
                                    # Reload the child data
                                    child = self.browse(cr, uid, child.id,
                                                        context=context)
                                value += child.current_value * sign
                # Negate the value if needed
                if tmpl_line.negate:
                    value = -value
                current_value = value
            search_domain = [('month_report_id', '=', line.month_report_id.id),
                             ('template_line_id', '=',
                              line.template_line_id.id),
                             ('month_num', '<', line.month_num)]
            acum_lines_ids = self.search(cr, uid, search_domain,
                                         context=context)
            acum_value = 0.0
            for acum_line in acum_lines_ids:
                acum_o = self.browse(cr, uid, acum_line, context=context)
                acum_value += acum_o.current_value
            acum_value += current_value
            # Write the values
            self.write(cr, uid, line.id,
                       {'current_value': current_value,
                        'previous_value': previous_value,
                        'acum_value': acum_value,
                        'calc_date': line.month_report_id.calc_date,
                        }, context=context)
        return True

    def _get_account_month_balance(self, cr, uid, ids, code,
                                   balance_mode=0, context=None):

        """
        It returns the (debit, credit, balance*) tuple for a account with the
        given code, or the sum of those values for a set of accounts
        when the code is in the form "400,300,(323)"

        Depending on the balance_mode, the balance is calculated as follows:
          Mode 0: debit-credit for all accounts (default);
          Mode 1: debit-credit, credit-debit for accounts in brackets;
          Mode 2: credit-debit for all accounts;
          Mode 3: credit-debit, debit-credit for accounts in brackets.

        Also the user may specify to use only the debit or credit of the
        account instead of the balance writing "debit(551)" or "credit(551)".
        """

        acc_obj = self.pool['account.account']
        logger = logging.getLogger(__name__)
        res = 0.0
        line = self.browse(cr, uid, ids[0], context=context)
        company_id = line.month_report_id.company_id.id
        # We iterate over the accounts listed in "code", so code can be
        # a string like "430+431+432-438"; accounts split by "+" will be added,
        # accounts split by "-" will be substracted.
        for acc_code in re.findall('(-?\w*\(?[0-9a-zA-Z_]*\)?)', code):
            # Check if the code is valid (findall might return empty strings)
            acc_code = acc_code.strip()
            if acc_code:
                # Check the sign of the code (substraction)
                if acc_code.startswith('-'):
                    sign = -1
                    acc_code = acc_code[1:].strip()  # Strip the sign
                else:
                    sign = 1
                if re.match(r'^debit\(.*\)$', acc_code):
                    # Use debit instead of balance
                    mode = 'debit'
                    acc_code = acc_code[6:-1]  # Strip debit()
                elif re.match(r'^credit\(.*\)$', acc_code):
                    # Use credit instead of balance
                    mode = 'credit'
                    acc_code = acc_code[7:-1]  # Strip credit()
                else:
                    mode = 'balance'
                # Calculate sign of the balance mode
                sign_mode = 1
                if balance_mode in (1, 2, 3):
                    # for accounts in brackets or mode 2, the sign is reversed
                    if (acc_code.startswith('(') and acc_code.endswith(')')) \
                            or balance_mode == 2:
                        sign_mode = -1
                # Strip the brackets (if any)
                if acc_code.startswith('(') and acc_code.endswith(')'):
                    acc_code = acc_code[1:-1]
                # Search for the account (perfect match)
                account_ids = acc_obj.search(cr, uid,
                                             [('code', '=', acc_code),
                                              ('company_id', '=', company_id)
                                              ], context=context)
                if not account_ids:
                    # Search for a subaccount ending with '0'
                    account_ids = acc_obj.search(cr, uid,
                                                 [('code', '=like',
                                                   '%s%%0' % acc_code),
                                                  ('company_id', '=',
                                                   company_id)
                                                  ], context=context)
                if not account_ids:
                    logger.warning("Account with code '%s' not found!"
                                   % acc_code)
                for account in acc_obj.browse(cr, uid, account_ids,
                                              context=context):
                    if mode == 'debit':
                        res -= account.debit * sign
                    elif mode == 'credit':
                        res += account.credit * sign
                    else:
                        res += account.balance * sign * sign_mode
        return res
