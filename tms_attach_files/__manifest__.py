# Copyright 2016, Jarsa Sistemas, S.A. de C.V.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    'name': 'Attach Travel Expense Line Files',
    'summary': 'Attach xml and pdf files to Travel Expenses Lines',
    'author': 'Jarsa Sistemas',
    'website': 'https://www.jarsa.com.mx',
    'category': 'Transport',
    'version': '12.0.1.0.0',
    "license": "AGPL-3",
    'depends': ['tms'],
    'data': [
        'views/tms_expense_line_view.xml'
    ],
    'installable': False,
}
