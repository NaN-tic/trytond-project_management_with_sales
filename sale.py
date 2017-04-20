# This file is part of Tryton.  The COPYRIGHT file at the top level of
# this repository contains the full copyright notices and license terms.
from decimal import Decimal
from trytond.transaction import Transaction
from trytond.pool import Pool, PoolMeta

__all__ = ['SaleLine', 'Work', 'ProjectSummary']


class Work:
    __name__ = 'project.work'
    __metaclass__ = PoolMeta

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
                    Decimal(line.project.progress_quantity_percent))
            res['cost'][line.id] = (line.product.cost_price or 0)*Decimal(
                str(line.quantity or 0)) if line.product else 0
            res['progress_cost'][line.id] = Decimal(0)

        for key in res.keys():
            if key not in names:
                del res[key]

        return res

    @staticmethod
    def _get_summary_related_field():
        return 'project'
