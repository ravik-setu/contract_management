# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    'name': 'Contract Management System',
    'version': '15.0',
    'category': 'Accounting',
    'description': 'Contract Management System',
    'website': 'https://www.odoo.com/app/invoicing',
    'depends': ['documents_hr_contract', 'timesheet_grid', 'project', 'account','hr_contract','hr_expense'],
    'data': [
        'security/ir.model.access.csv',
        'views/contract_management_view.xml',
        'views/project_project_view.xml',
        'views/account_move_view.xml',
        'views/res_partner_view.xml',
        'views/contract_utilization_report.xml',
        'views/project_task_view.xml',
        'views/account_analytic_line_view.xml',
        'views/contract_portal_templates.xml',
        'views/contract_report.xml',
        'report/hr_contract_report_analysis.xml',
        'data/email_template.xml',
        'data/ir_cron.xml'
    ],
    'demo': [
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'LGPL-3',
}
