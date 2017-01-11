# This file is part of Tryton.  The COPYRIGHT file at the top level of
# this repository contains the full copyright notices and license terms.
from decimal import Decimal
from collections import defaultdict

from sql.aggregate import Sum
from sql.operators import Concat

from trytond.model import fields
from trytond.pyson import Eval, Id
from trytond.transaction import Transaction
from trytond.pool import Pool, PoolMeta
from datetime import date

__all__ = ['Sale', 'SaleLine', 'Work', 'ProjectSummary']


class Work:
    __name__ = 'project.work'
    __metaclass__ = PoolMeta

    sale_lines = fields.One2Many('sale.line', 'project', 'Sale lines')

    @classmethod
    def _get_summary_models(cls):
        res = super(Work, cls)._get_summary_models()
        return res + [('sale.line', 'project', 'get_total')]


class ProjectSummary:

    __name__ = 'project.work.summary'
    __metaclass__ = PoolMeta

    @classmethod
    def union_models(cls):
        res = super(ProjectSummary, cls).union_models()
        return ['sale.line'] + res


class SaleLine:
    __name__ = 'sale.line'
    __metaclass__ = PoolMeta

    project = fields.Many2One('project.work', 'Project', readonly=True,
        select=True)

    @classmethod
    def get_total(cls, lines, names):
        res = {}
        pool = Pool()
        Work = pool.get('project.work')
        for name in Work._get_summary_fields():
            res[name] = {}

        limit_date = Transaction().context.get('limit_date')
        for line in lines:
            if line.type != 'line':
                continue
            if limit_date != None and line.sale.sale_date > limit_date:
                continue
            res['revenue'][line.id] = line.amount
            res['progress_revenue'][line.id] = (line.amount *
                (line.project.progress_quantity or Decimal(0)))
            res['cost'][line.id] = (line.cost_price or 0)*Decimal(
                str(line.quantity or 0))
            res['progress_cost'][line.id] = Decimal(0)

        for key in res.keys():
            if key not in names:
                del res[key]

        return res

    @staticmethod
    def _get_summary_related_field():
        return 'project'


class Sale:
    __name__ = 'sale.sale'
    __metaclass__ = PoolMeta

    parent_project = fields.Many2One('project.work', 'Parent Project',
        select=True)

    @classmethod
    def process(cls, sales):
        super(Sale, cls).process(sales)
        cls.create_projects(sales)

    @classmethod
    def create_projects(cls, sales):
        pool = Pool()
        SaleLine = pool.get('sale.line')
        for sale in sales:
            if not sale.parent_project:
                continue
            project = sale._get_project()
            project.save()
            SaleLine.write([x for x in sale.lines], {'project': project.id})

    def _get_project(self):
        Work = Pool().get('project.work')
        project = Work()
        project.name = self.rec_name
        project.type = 'project'
        project.product_goods = self.parent_project.product_goods
        project.uom = self.parent_project.uom
        project.company = self.company
        project.project_invoice_method = self.parent_project.invoice_method
        project.invoice_product_type = self.parent_project.invoice_product_type
        project.parent = self.parent_project
        project.party = self.party
        project.party_address = self.invoice_address
        project.progress_quantity = 0
        project.quantity = 1
        project.start_date = date.today()
        project.list_price = self.untaxed_amount
        return project
