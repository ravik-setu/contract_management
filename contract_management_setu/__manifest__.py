# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    'name': 'Contract Management',
    'version': '15.0',
    'category': 'Accounting',
    'website': 'https://www.odoo.com/app/invoicing',
    'depends': ['documents_hr_contract'],
    'data': [
        'views/contract_management_view.xml',
        'views/project_project_view.xml',
        'views/account_move_view.xml',
    ],
    'demo': [
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'LGPL-3',
}
