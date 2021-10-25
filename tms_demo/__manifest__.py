# Copyright 2012, Israel Cruz Argil, Argil Consulting
# Copyright 2016, Jarsa Sistemas, S.A. de C.V.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    'name': 'TMS Demo Data',
    'version': '12.0.1.0.0',
    'category': 'Transport',
    'author': 'Jarsa Sistemas, Argil Consulting',
    'website': 'https://www.jarsa.com.mx/page/transport-management-system',
    'depends': ['tms', 'l10n_mx'],
    'summary': 'Demo Data for TMS',
    'license': 'AGPL-3',
    'demo': [
        'demo/account_account.xml',
        'demo/res_partner.xml',
        'demo/hr_employee.xml',
        'demo/product_product.xml',
        'demo/tms_advance.xml',
        'demo/tms_expense_loan.xml',
        'demo/tms_waybill.xml',
        'demo/tms_expense.xml',
    ],
    'auto-install': False,
}
