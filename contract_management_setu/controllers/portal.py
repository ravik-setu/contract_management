import binascii

from odoo.exceptions import AccessError, MissingError, ValidationError
from odoo.fields import Command
from odoo.http import request

from odoo.addons.payment.controllers import portal as payment_portal
from odoo.addons.payment import utils as payment_utils
from odoo.addons.portal.controllers.mail import _message_post_helper
from odoo.addons.portal.controllers import portal
from odoo.addons.portal.controllers.portal import pager as portal_pager, get_records_pager
from odoo import fields
from odoo.http import request,content_disposition
from odoo.addons.portal.controllers import portal
from odoo import http, _
from odoo.exceptions import AccessError, MissingError, ValidationError
from odoo.addons.portal.controllers.portal import CustomerPortal, pager as portal_pager


class CustomerPortal(portal.CustomerPortal):
    def _prepare_contracts_domian(self):
        info = request.env.user.self.id
        return [
            ('partner_id', '=', info)
        ]

    def _prepare_home_portal_values(self, counters):
        values = super()._prepare_home_portal_values(counters)

        contract = request.env['hr.contract']
        domain = self._prepare_contracts_domian()
        if 'contract_count' in counters:
            values['contract_count'] = contract.search_count(domain)
        return values

    @http.route(['/my/contracts'], type='http', auth="user", website=True)
    def portal_my_contracts(self, **kw):
        contract = request.env['hr.contract']
        domain = self._prepare_contracts_domian()
        data = contract.search(domain)

        values = {
            'data': data,
            'page_name': 'contract'
        }
        return request.render("contract_management_setu.portal_my_contracts", values)

    @http.route(['/my/contracts/<int:contract_id>'], type='http', auth="user", website=True)
    def portal_contract_page(self, contract_id, report_type=None, download=False, **kw):
        contract = request.env['hr.contract']
        data = contract.search([('id', '=', contract_id)])

        invoice = request.env['account.move']
        info = invoice.search([('contract_id', '=', contract_id)])

        payment = request.env['account.payment']
        p_data = data.sudo().get_payment_of_invoices()
        p_res = payment.sudo().search([('move_id', 'in', p_data)])

        values = {
            'data1': data,
            'info': info,
            'p_res': p_res,
            'page_name': 'contract'
        }
        return request.render("contract_management_setu.contract_portal_template", values)

    @http.route(['/my/contracts/<int:contract_id>/invoices'], type='http', auth="user", website=True)
    def portal_contract_invoices(self, contract_id, **kw):
        contract = request.env['hr.contract']
        data = contract.search([('id', '=', contract_id)])

        invoice = request.env['account.move']
        info = invoice.search([('contract_id', '=', contract_id)])

        values = {
            'data1': data,
            'invoices': info,
            'page_name': 'contract'
        }
        return request.render("contract_management_setu.portal_my_invoices", values)

    @http.route(['/my/contracts/<int:contract_id>/payments'], type='http', auth="user", website=True)
    def portal_contract_payments(self, contract_id, **kw):
        contract = request.env['hr.contract']
        data = contract.search([('id', '=', contract_id)])

        payment = request.env['account.payment']
        p_data = data.sudo().get_payment_of_invoices()
        p_res = payment.sudo().search([('move_id', 'in', p_data)])

        values = {
            'data1': data,
            'payments': p_res,
            'page_name': 'contract'

        }

        return request.render("contract_management_setu.portal_my_contracts_payments", values)

    @http.route(['/my/contracts/<int:contract_id>/timesheet'], type='http', auth="user", website=True)
    def portal_contract_timesheet(self, contract_id, **kw):
        contract = request.env['hr.contract']
        data = contract.search([('id', '=', contract_id)])

        timesheet = request.env['account.analytic.line']
        t_data = data.sudo().get_timesheet_of_contract()
        res = timesheet.sudo().search([('id', 'in', t_data)])

        values = {
            'data1': data,
            'timesheet': res,
            'page_name': 'contract'

        }

        return request.render("contract_management_setu.portal_my_contracts_timesheets", values)

    @http.route(['/my/reports'], type='http', auth="user", website=True)
    def portal_my_contracts_reports(self, **kw):
        contract = request.env['hr.contract']
        domain = self._prepare_contracts_domian()
        data = contract.search(domain)

        values = {
            'contract': data,
            'page_name': 'report',

        }
        return request.render("contract_management_setu.portal_my_reports", values)


    @http.route(['/my/contracts/<int:contract_id>/download/timesheet'], type='http', auth="user", website=True)
    def prepare_timesheets_download(self, contract_id,**kw):
        contract = request.env['hr.contract'].sudo().search([('id', '=', contract_id)])
        content, content_type = request.env.ref('contract_management_setu.portal_timesheet_report').sudo()._render_qweb_pdf(res_ids=contract.timesheet_ids.ids)
        reporthttpheaders = [
            ('Content-Type', 'application/pdf'),
            ('Content-Length', len(content)),
        ]
        filename = "demo.pdf"
        reporthttpheaders.append(('Content-Disposition', content_disposition(filename)))
        return request.make_response(content, headers=reporthttpheaders)