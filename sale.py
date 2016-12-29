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
from trytond.tools import reduce_ids, grouped_slice
from datetime import date
from trytond.modules.product import price_digits

__all__ = ['Sale', 'SaleLine', 'Work', 'ProjectSummary']


class Work:
    __name__ = 'project.work'
    __metaclass__ = PoolMeta

    @classmethod
    def _get_related_cost_and_revenue(cls):
        res = super(Work, cls)._get_related_cost_and_revenue()
        return res + [('sale.line', 'project', '_get_revenue',
            '_get_cost')]


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
    def _get_cost(cls, lines):
        return dict((w.id, w.cost_price*Decimal(str(w.quantity)))
                for w in lines)

    @classmethod
    def _get_revenue(cls, lines):
        return dict((w.id, w.unit_price*Decimal(str(w.quantity)))
            for w in lines)

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
