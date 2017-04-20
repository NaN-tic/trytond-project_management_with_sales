# This file is part of Tryton.  The COPYRIGHT file at the top level of
# this repository contains the full copyright notices and license terms.
import unittest
import trytond.tests.test_tryton
from trytond.tests.test_tryton import ModuleTestCase, with_transaction
from trytond.pool import Pool


class ProjectManagementWithSalesTestCase(ModuleTestCase):
    'Test GoogleMaps module'
    module = 'project_management_with_sales'

def suite():
    suite = trytond.tests.test_tryton.suite()
    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(
        ProjectManagementWithSalesTestCase))
    return suite
