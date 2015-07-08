# -*- encoding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################

from openerp.osv import orm, fields
from datetime import datetime
import openerp.addons.decimal_precision as dp
#import decimal_precision as dp
from dateutil.relativedelta import relativedelta


class ProductBudgetLine(orm.Model):

    _name = 'product.budget.line'

    def _prac_amt(self, cr, uid, ids, context=None):
        res = {}
        result = {'real_amount': 0.00,
                  'real_subtotal': 0.00,
                  'real_qty': 0.00}
        for line in self.browse(cr, uid, ids, context=context):
            budget_line = line.budget_line_id
            acc_ids = [x.id for x in budget_line.general_budget_id.account_ids]
            date_to = budget_line.date_to
            date_from = budget_line.date_from
            analytic_account = budget_line.analytic_account_id.id
            product_id = line.product_id.id
            if analytic_account:
                cr.execute("""SELECT SUM(unit_amount), SUM(amount),
                    AVG(amount/unit_amount) FROM account_analytic_line
                    WHERE account_id=%s AND (date between
                    to_date(%s,'yyyy-mm-dd') AND to_date(%s,'yyyy-mm-dd'))
                    AND general_account_id=ANY(%s) AND product_id=%s""",
                           (analytic_account, date_from, date_to, acc_ids,
                            product_id))
                sql_result = cr.fetchone()
                amount = 0.0
                subtotal = 0.0
                qty = 0.0
                if sql_result[0]:
                    qty = sql_result[0]
                if sql_result[1]:
                    subtotal = sql_result[1]
                if sql_result[2]:
                    amount = sql_result[2]
                result = {'real_amount': amount,
                          'real_subtotal': subtotal,
                          'real_qty': qty,
                          }
            res[line.id] = result
        return res

    def _prac(self, cr, uid, ids, name, args, context=None):
        res = {}
        for line in self.browse(cr, uid, ids, context=context):
            res[line.id] = {'real_amount': 0.00,
                            'real_subtotal': 0.00,
                            'real_qty': 0.00,
                            }
            budget_line = line.budget_line_id
            date_to = budget_line.date_to
            date_from = budget_line.date_from
            if (date_from and date_to and
                    budget_line.general_budget_id.account_ids):
                res[line.id] = self._prac_amt(cr, uid, [line.id],
                                              context=context)[line.id]
        return res

    def _get_subtotal(self, cr, uid, ids, name, args, context=None):
        res = {}
        for line_id in ids:
            res[line_id] = {'expected_subtotal': 0.0,
                            }
            line_o = self.browse(cr, uid, line_id, context=context)
            calc_subtotal = 0.0
            if line_o.expected_qty and line_o.expected_price:
                calc_subtotal = line_o.expected_qty * line_o.expected_price
            res[line_id].update({'expected_subtotal': calc_subtotal
                                 })
        return res
    
    def _get_crossovered(self, cr, uid, ids, context=None):
        result = set()
        crossovered_obj = self.pool['crossovered.budget.lines']
        for crossovered in crossovered_obj.browse(cr, uid, ids,
                                                  context=context):
            for line in crossovered.product_budget_ids:
                result.add(line.id)
        return list(result)

    _columns = {'product_id': fields.many2one('product.product', 'Product'),
                'account_id': fields.many2one('account.account', 'Account'),
                'expected_qty': fields.float(
                    'Expected Qty',
                    digits_compute=dp.get_precision('Product UoM')),
                'expected_price': fields.float(
                    'Unit price',
                    digits_compute=dp.get_precision('Account')),
                'expected_subtotal': fields.function(
                    _get_subtotal, method=True, type="float",
                    digits_compute=dp.get_precision('Account'),
                    string="Expected subtotal", store=True, multi="subtotal"),
                'budget_line_id': fields.many2one('crossovered.budget.lines',
                                                  'Budget Line',
                                                  ondelete="cascade"),
                'real_amount': fields.function(
                    _prac, method=True, string='Real Price', type='float',
                    digits_compute=dp.get_precision('Account'),
                    multi="practical"),
                'real_qty': fields.function(
                    _prac, method=True, string='Real Qty', type='float',
                    digits_compute=dp.get_precision('Product UoM'),
                    multi="practical"),
                'real_subtotal': fields.function(
                    _prac, method=True, string='Real Subtotal', type='float',
                    digits_compute=dp.get_precision('Account'),
                    multi="practical"),
                'categ_id': fields.related('product_id', 'categ_id',
                                           type="many2one",
                                           relation="product.category",
                                           string="Product category",
                                           store=True),
                'prod_type': fields.related('product_id', 'type',
                                            type="selection",
                                            selection=[('product',
                                                        'Stockable Product'),
                                                       ('consu', 'Consumable'),
                                                       ('service', 'Service')],
                                            string="Product type", store=True),
                'date_start': fields.related('budget_line_id', 'date_from',
                    type="date", string="Date start",
                    store={'product.budget.line':
                                (lambda self, cr, uid, ids, context=None: ids,
                                 None, 20),
                           'crossovered.budget.lines': (_get_crossovered,
                                                        ['date_from'], 20)}),
                'date_end': fields.related('budget_line_id', 'date_to',
                    type="date", string="Date end",
                    store={'product.budget.line':
                                (lambda self, cr, uid, ids, context=None: ids,
                                 None, 20),
                           'crossovered.budget.lines': (_get_crossovered,
                                                        ['date_to'], 20)}),
                'period_id': fields.related('budget_line_id', 'period_id',
                                            type="many2one",
                                            relation='account.period',
                                            string="Period",
                                            store=True),
                'analytic_account': fields.related(
                    'budget_line_id', 'analytic_account_id', type="many2one",
                    relation="account.analytic.account",
                    string="Analytic account", store=True),
                'partner_id': fields.related('budget_line_id',
                                             'analytic_account_id',
                                             'partner_id',
                                             type="many2one",
                                             relation="res.partner",
                                             string="Partner",
                                             store=True),
                'crossovered_budget_id': fields.related(
                    'budget_line_id', 'crossovered_budget_id', type="many2one",
                    relation="crossovered.budget", string="Budget", store=True)
                }

    def onchange_product_id(self, cr, uid, ids, product, context=None):
        product_obj = self.pool['product.product']
        res = {}
        if product:
            prod_o = product_obj.browse(cr, uid, product, context=context)
            res.update({'expected_price': prod_o.list_price,
                        })
        return {'value': res}


class CrossoveredBudgetLines(orm.Model):

    _inherit = 'crossovered.budget.lines'

    def _get_amount(self, cr, uid, ids, name, args, context=None):
        res = {}
        for line_id in ids:
            res[line_id] = 0.0
            line_o = self.browse(cr, uid, line_id, context=context)
            if line_o.product_budget_ids:
                kont = 0.0
                for product_line in line_o.product_budget_ids:
                    kont += (product_line.expected_qty *
                             product_line.expected_price)
                res[line_id] = kont
        return res

    def _prac(self, cr, uid, ids, name, args, context=None):
        res = {}
        for line in self.browse(cr, uid, ids, context=context):
            res[line.id] = 0.0
            if (line.date_from and line.date_to and
                    line.general_budget_id.account_ids):
                res[line.id] = self._prac_amt(cr, uid, [line.id],
                                              context=context)[line.id]
        return res

    def _theo(self, cr, uid, ids, name, args, context=None):
        res = {}
        for line in self.browse(cr, uid, ids, context=context):
            res[line.id] = 0.0
            if (line.date_from and line.date_to and
                    line.general_budget_id.account_ids):
                res[line.id] = self._theo_amt(cr, uid, [line.id],
                                              context=context)[line.id]
        return res
    def _es_trimestral(self, cr, uid, ids, name, args, context=None):
        res = {}
        date_format = "%Y-%m-%d"
        for line in self.browse(cr, uid, ids, context=context):
            res[line.id] = False
            if (line.date_from and line.date_to):
                line_start_date = datetime.strptime(line.date_from,
                                                    date_format)
                line_end_date = datetime.strptime(line.date_to, date_format)
                line_date_diff = line_end_date.month - line_start_date.month
                if line_date_diff > 0:
                    res[line.id] = True
        return res
    _columns = {'product_budget_ids': fields.one2many('product.budget.line',
                                                      'budget_line_id',
                                                      'Product budget lines'),
                'partner_id': fields.related('analytic_account_id',
                                             'partner_id', type="many2one",
                                             relation="res.partner",
                                             string="Partner", store=True),
                'es_trimestral': fields.function(_es_trimestral, method=True,
                                                 type="boolean",
                                                 string="Es trimestral"),
                'period_id': fields.many2one('account.period', 'Periodo'),
                'general_amount': fields.function(
                    _get_amount, method=True,
                    digits_compute=dp.get_precision('Account'), type="float",
                    string="General amount"),
                'date_from': fields.date('Start Date', required=False),
                'date_to': fields.date('End Date', required=False),
                'theoritical_amount': fields.function(
                    _theo, string='Theoretical Amount', type='float',
                    digits_compute=dp.get_precision('Account')),
                'practical_amount': fields.function(
                    _prac, string='Practical Amount', type='float',
                    digits_compute=dp.get_precision('Account')),
                }

    def name_get(self, cr, uid, ids, context=None):
        res = []
        if not len(ids):
            return []
        reads = self.read(cr, uid, ids, ['crossovered_budget_id',
                                         'analytic_account_id'],
                          context=context)
        for record in reads:
            name = ''
            if record['crossovered_budget_id']:
                name = record['crossovered_budget_id'][1]
            if record['analytic_account_id']:
                if record['crossovered_budget_id']:
                    name = name + ' - ' + record['analytic_account_id'][1]
                else:
                    name = record['analytic_account_id'][1]
            res.append((record['id'], name))
        return res

    def dividir_meses(self, cr, uid, ids, fecha_inicio, fecha_fin,
                      context=None):
        date_format = '%Y-%m-%d'
        start_date = datetime.strptime(fecha_inicio, date_format)
        end_date = datetime.strptime(fecha_fin, date_format)
        date_array = []
        date_diff = end_date.month - start_date.month
        while date_diff >= 0:
            date_dict = {}
            today = start_date + relativedelta(months=date_diff)
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

    def dividir_trimestres(self, cr, uid, ids, context=None):
        res = []
        result = {}
        product_line_obj = self.pool['product.budget.line']
        period_obj = self.pool['account.period']
        if not context:
            context = {}
        if ids:
            actual_id = False
            if isinstance(ids, list):
                actual_id = ids[0]
            if actual_id:
                actual_o = self.browse(cr, uid, actual_id, context=context)
                date_lst = self.dividir_meses(cr, uid, ids, actual_o.date_from,
                                              actual_o.date_to, context)
                month_count = len(date_lst)
                if date_lst:
                    first_date = date_lst.pop(0)
                    period_ids = period_obj.find(cr, uid,
                                                 first_date['start_month'],
                                                 context=context)
                    period_lst = period_obj.search(cr, uid,
                                                   [('id', 'in', period_ids),
                                                    ('special', '=', False)])
                    new_period_id = period_lst
                    if isinstance(period_lst, list):
                        new_period_id = period_lst[0]
                    write_vals = {'date_from': first_date['start_month'],
                                  'date_to': first_date['end_month'],
                                  'es_trimestral': False,
                                  'period_id': new_period_id,
                                  'planned_amount': actual_o.planned_amount /
                                  month_count,
                                  }
                    self.write(cr, uid, [actual_id], write_vals,
                               context=context)
                    res.append(actual_id)
                    if actual_o.product_budget_ids:
                        for pro_line_o in actual_o.product_budget_ids:
                            pro_line_vals = {
                                'expected_qty': pro_line_o.expected_qty /
                                month_count,
                                }
                            product_line_obj.write(cr, uid, [pro_line_o.id],
                                                   pro_line_vals,
                                                   context=context)
                    for date_o in date_lst:
                        period_ids = period_obj.find(cr, uid,
                                                     date_o['start_month'],
                                                     context=context)
                        period_lst = period_obj.search(cr, uid,
                                                       [('id', 'in',
                                                         period_ids),
                                                        ('special', '=',
                                                         False)])
                        new_period_id = period_lst
                        if isinstance(period_lst, list):
                            new_period_id = period_lst[0]
                        line_defaults = {'date_from': date_o['start_month'],
                                         'date_to': date_o['end_month'],
                                         'period_id': new_period_id,
                                         }
                        new_id = self.copy(cr, uid, actual_id, line_defaults,
                                           context=context)
                        actual = self.browse(cr, uid, actual_id,
                                             context=context)
                        for line in actual.product_budget_ids:
                            line_defaults = {'budget_line_id':new_id}
                            product_line_obj.copy(cr, uid, line.id,
                                                  line_defaults,
                                                  context=context)
                        res.append(new_id)
                    result.update({'view_type': 'form',
                                   'view_mode': 'tree,form',
                                   'res_model': 'crossovered.budget.lines',
                                   'res_id': res,
                                   'view_id': False,
                                   'type': 'ir.actions.act_window',
                                   'target': 'current',
                                   'nodestroy': True,
                                   })
        return result

    def copiar_trimestres(self, cr, uid, ids, context=None):
        res = []
        result = {}
        period_obj = self.pool['account.period']
        product_bud_obj = self.pool["product.budget.line"]
        if not context:
            context = {}
        if ids:
            actual_id = False
            if isinstance(ids, list):
                actual_id = ids[0]
            if actual_id:
                actual_o = self.browse(cr, uid, actual_id, context=context)
                date_lst = self.dividir_meses(cr, uid, ids, actual_o.date_from,
                                              actual_o.date_to,
                                              context=context)
                if date_lst:
                    first_date = date_lst.pop(0)
                    period_ids = period_obj.find(cr, uid,
                                                 first_date['start_month'],
                                                 context=context)
                    period_lst = period_obj.search(cr, uid,
                                                   [('id', 'in', period_ids),
                                                    ('special', '=', False)])
                    new_period_id = period_lst
                    if isinstance(period_lst, list):
                        new_period_id = period_lst[0]
                    write_vals = {'date_from': first_date['start_month'],
                                  'date_to': first_date['end_month'],
                                  'es_trimestral': False,
                                  'period_id': new_period_id,
                                  }
                    self.write(cr, uid, [actual_id], write_vals,
                               context=context)
                    res.append(actual_id)
                    for date_o in date_lst:
                        period_ids = period_obj.find(cr, uid,
                                                     date_o['start_month'],
                                                     context=context)
                        period_lst = period_obj.search(cr, uid,
                                                       [('id', 'in',
                                                         period_ids),
                                                        ('special', '=',
                                                         False)])
                        new_period_id = period_lst
                        if isinstance(period_lst, list):
                            new_period_id = period_lst[0]
                        line_defaults = {'date_from': date_o['start_month'],
                                         'date_to': date_o['end_month'],
                                         'period_id': new_period_id,
                                         }
                        new_id = self.copy(cr, uid, actual_id, line_defaults,
                                           context=context)
                        actual = self.browse(cr, uid, actual_id, context=context)
                        for line in actual.product_budget_ids:
                            line_defaults = {'budget_line_id':new_id}
                            product_bud_obj.copy(cr, uid, line.id,
                                                 line_defaults,
                                                 context=context)
                        res.append(new_id)
                    result.update({'view_type': 'form',
                                   'view_mode': 'tree,form',
                                   'res_model': 'crossovered.budget.lines',
                                   'res_id': res,
                                   'view_id': False,
                                   'type': 'ir.actions.act_window',
                                   'target': 'current',
                                   'nodestroy': True,
                                   })
        return result

    def copy_period(self, cr, uid, ids, context=None):
        res = {}
        product_bud_obj = self.pool['product.budget.line']
        if ids:
            actual_id = False
            if isinstance(ids, list):
                actual_id = ids[0]
            if actual_id:
                copy_defaults = {'date_to': False,
                                 'date_from': False,
                                 'period_id': False
                                 }
                new_id = self.copy(cr, uid, actual_id, copy_defaults,
                                   context=context)
                actual = self.browse(cr, uid, actual_id, context=context)
                for line in actual.product_budget_ids:
                    line_defaults = {'budget_line_id':new_id}
                    product_bud_obj.copy(cr, uid, line.id, line_defaults,
                                         context=context)
                res.update({'view_type': 'form',
                            'view_mode': 'tree,form',
                            'res_model': 'crossovered.budget.lines',
                            'res_id': [new_id],
                            'view_id': False,
                            'type': 'ir.actions.act_window',
                            'target': 'current',
                            'nodestroy': True,
                            })
        return res

    def onchange_period(self, cr, uid, ids, period, date_from, date_to,
                        context=None):
        res = {}
        period_obj = self.pool['account.period']
        es_trimestral = False
        period_id = False
        if not period:
            if date_from and date_to:
                period_ids = period_obj.find(cr, uid, date_from,
                                             context=context)
                period_lst = period_obj.search(cr, uid,
                                               [('id', 'in', period_ids),
                                                ('special', '=', False)])
                period_id = period_lst
                if isinstance(period_lst, list):
                    period_id = period_lst[0]
                period = period_id
        if period:
            period_id = period
            period_o = period_obj.browse(cr, uid, period, context=context)
            if not date_to or not date_from:
                date_to = period_o.date_stop
                date_from = period_o.date_start
            if date_to and date_from:
                date_format = '%Y-%m-%d'
                start_date = datetime.strptime(period_o.date_start,
                                               date_format)
                end_date = datetime.strptime(period_o.date_stop, date_format)
                line_start_date = datetime.strptime(date_from, date_format)
                line_end_date = datetime.strptime(date_to, date_format)
                date_diff = end_date.month - start_date.month
                line_date_diff = line_end_date.month - line_start_date.month
                if date_diff > 0 and line_date_diff > 0:
                    es_trimestral = True
        val = {'es_trimestral': es_trimestral,
               'date_to': date_to,
               'date_from': date_from,
               'period_id': period_id
               }
        res.update({'value': val})
        return res

    def load_product_accounts(self, cr, uid, ids, context=None):
        prod_line_obj = self.pool['product.budget.line']
        general_budget_obj = self.pool['account.budget.post']
        for id in ids:
            account_lst = []
            prod_domain = [('budget_line_id', '=', id)]
            prod_lst = prod_line_obj.search(cr, uid, prod_domain,
                                            context=context)
            self_o = self.read(cr, uid, id, ['general_budget_id'],
                               context=context)
            general_budget = self_o['general_budget_id']
            if general_budget:
                general_budget_id = general_budget[0]
                general_budget_o = general_budget_obj.browse(cr, uid,
                                                             general_budget_id,
                                                             context=context)
                for acc in general_budget_o.account_ids:
                    if acc.id not in account_lst:
                        account_lst.append(acc.id)
                for prod_id in prod_lst:
                    prod = prod_line_obj.browse(cr, uid, prod_id,
                                                context=context)
                    acc = False
                    if prod.product_id.property_account_income:
                        prod_acc = prod.product_id.property_account_income
                        acc = prod_acc.id
                        if prod_acc.id not in account_lst:
                            account_lst.append(prod_acc.id)
                    elif prod.product_id.categ_id:
                        categ = prod.product_id.categ_id
                        if categ.property_account_income_categ:
                            categ_account = (
                                categ.property_account_income_categ.id)
                            acc = categ_account
                            if categ_account not in account_lst:
                                account_lst.append(categ_account)
                    prod_line_obj.write(cr, uid, [prod_id],
                                        {'account_id': acc}, context=context)
                budget_vals = {'account_ids': [(6, 0, account_lst)]
                               }
                general_budget_obj.write(cr, uid, [general_budget_id],
                                         budget_vals, context=context)
        return True
