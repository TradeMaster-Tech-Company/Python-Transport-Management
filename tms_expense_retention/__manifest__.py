# Copyright 2016, Jarsa Sistemas, S.A. de C.V.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    'name': 'Retention for TMS Expense',
    'version': '12.0.1.0.0',
    'category': 'Transport',
    'author': 'Jarsa Sistemas',
    'website': 'https://www.jarsa.com.mx',
    'depends': [
        'tms',
    ],
    'data': [
        'views/tms_retention_view.xml',
        'views/product_template.xml',
        'security/ir.model.access.csv',
    ],
    'demo': [
        'demo/product_product.xml',
        'demo/tms_retention.xml',
    ],
    'summary': 'Management System for Carriers, Trucking and other companies',
    'license': 'AGPL-3',
    'installable': False,
}
