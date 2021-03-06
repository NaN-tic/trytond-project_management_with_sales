# The COPYRIGHT file at the top level of this repository contains the full
# copyright notices and license terms.
from trytond.pool import Pool
from . import sale


def register():
    Pool.register(
        sale.ProjectSummary,
        sale.Work,
        sale.SaleLine,
        module='project_management_with_sales', type_='model')
