# Copyright 2018, Jarsa Sistemas, S.A. de C.v.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
{
    'name': 'TMS Kiosk Mode for Entrance Validation',
    'summary': 'Validate entrance of trucks in kiosk mode.',
    'version': '12.0.1.0.0',
    'category': 'TMS',
    'website': 'https://www.jarsa.com.mx/',
    'author': 'Jarsa Sistemas, S.A. de C.v.',
    'license': 'AGPL-3',
    'installable': False,
    'depends': [
        'tms',
    ],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'views/tms_kiosk_view.xml',
        'views/tms_kiosk_view.xml',
        'views/web_asset_backend_template.xml',
        'views/tms_extratada.xml',
    ],
    'qweb': [
        "static/src/xml/kiosk_mode.xml",
    ],
}
