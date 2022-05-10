from collections import OrderedDict
from odoo.http import request, content_disposition
from odoo.addons.portal.controllers import portal
from dateutil.relativedelta import relativedelta
from odoo import fields, http, _
from odoo.tools import date_utils, groupby as groupbyelem
from odoo.addons.portal.controllers.portal import CustomerPortal, pager as portal_pager
from odoo.osv.expression import AND, OR
from odoo.addons.hr_timesheet.models import hr_timesheet
from operator import itemgetter



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



    def _get_searchbar_inputs(self):
        return {
            'all': {'input': 'all', 'label': _('Search in All')},
            'employee': {'input': 'employee', 'label': _('Search in Employee')},
            'project': {'input': 'project', 'label': _('Search in Project')},
            'task': {'input': 'task', 'label': _('Search in Task')},
            'name': {'input': 'name', 'label': _('Search in Description')},
        }

    def _task_get_searchbar_sortings(self):
        values = super()._task_get_searchbar_sortings()
        values['progress'] = {'label': _('Progress'), 'order': 'progress asc', 'sequence': 9}
        return values

    def _get_searchbar_groupby_for_portal_timesheet(self):
        return {
            'none': {'input': 'none', 'label': _('None')},
            'project': {'input': 'project', 'label': _('Project')},
            'task': {'input': 'task', 'label': _('Task')},
            'date': {'input': 'date', 'label': _('Date')},
            'employee': {'input': 'employee', 'label': _('Employee')}
        }


    def _get_search_domain(self, search_in, search):
        search_domain = []
        if search_in in ('project', 'all'):
            search_domain = OR([search_domain, [('project_id', 'ilike', search)]])
        if search_in in ('name', 'all'):
            search_domain = OR([search_domain, [('name', 'ilike', search)]])
        if search_in in ('employee', 'all'):
            search_domain = OR([search_domain, [('employee_id', 'ilike', search)]])
        if search_in in ('task', 'all'):
            search_domain = OR([search_domain, [('task_id', 'ilike', search)]])
        return search_domain

    def _get_groupby_mapping(self):
        return {
            'project': 'project_id',
            'task': 'task_id',
            'employee': 'employee_id',
            'date': 'date'
        }

    def _get_searchbar_sortings(self):
        return {
            'date': {'label': _('Newest'), 'order': 'date desc'},
            'employee': {'label': _('Employee'), 'order': 'employee_id'},
            'project': {'label': _('Project'), 'order': 'project_id'},
            'task': {'label': _('Task'), 'order': 'task_id'},
            'name': {'label': _('Description'), 'order': 'name'},
        }

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
    def portal_contract_timesheet(self, contract_id, sortby=None, filterby=None, search=None, search_in='all',
                                  groupby='none', **kw):
        contract = request.env['hr.contract']
        data = contract.search([('id', '=', contract_id)])

        timesheet = request.env['account.analytic.line']
        t_data = data.sudo().get_timesheet_of_contract()






        domain = []
        res = timesheet.sudo().search(domain)


        searchbar_sortings = self._get_searchbar_sortings()

        searchbar_inputs = self._get_searchbar_inputs()

        searchbar_groupby = self._get_searchbar_groupby_for_portal_timesheet()

        today = fields.Date.today()
        quarter_start, quarter_end = date_utils.get_quarter(today)
        last_week = today + relativedelta(weeks=-1)
        last_month = today + relativedelta(months=-1)
        last_year = today + relativedelta(years=-1)

        searchbar_filters = {
            'all': {'label': _('All'), 'domain': []},
            'today': {'label': _('Today'), 'domain': [("date", "=", today)]},
            'week': {'label': _('This week'), 'domain': [('date', '>=', date_utils.start_of(today, "week")),
                                                         ('date', '<=', date_utils.end_of(today, 'week'))]},
            'month': {'label': _('This month'), 'domain': [('date', '>=', date_utils.start_of(today, 'month')),
                                                           ('date', '<=', date_utils.end_of(today, 'month'))]},
            'year': {'label': _('This year'), 'domain': [('date', '>=', date_utils.start_of(today, 'year')),
                                                         ('date', '<=', date_utils.end_of(today, 'year'))]},
            'quarter': {'label': _('This Quarter'),
                        'domain': [('date', '>=', quarter_start), ('date', '<=', quarter_end)]},
            'last_week': {'label': _('Last week'), 'domain': [('date', '>=', date_utils.start_of(last_week, "week")),
                                                              ('date', '<=', date_utils.end_of(last_week, 'week'))]},
            'last_month': {'label': _('Last month'),
                           'domain': [('date', '>=', date_utils.start_of(last_month, 'month')),
                                      ('date', '<=', date_utils.end_of(last_month, 'month'))]},
            'last_year': {'label': _('Last year'), 'domain': [('date', '>=', date_utils.start_of(last_year, 'year')),
                                                              ('date', '<=', date_utils.end_of(last_year, 'year'))]},
        }

        if not sortby:
            sortby = 'date'
        order = searchbar_sortings[sortby]['order']

        if not filterby:
            filterby = 'all'
        domain = AND([domain, searchbar_filters[filterby]['domain']])

        if search and search_in:
            domain += self._get_search_domain(search_in, search)

        domain += [('id', 'in', t_data)]



        def get_timesheets_data():
            groupby_mapping = self._get_groupby_mapping()
            field = groupby_mapping.get(groupby, None)
            orderby = '%s, %s' % (field, order) if field else order
            main_res = res.sudo().search(domain, order=orderby)
            if field:
                if groupby == 'date':
                    raw_timesheets_group = timesheet.sudo().read_group(
                        domain, ["unit_amount:sum", "ids:array_agg(id)"], ["date:day"]
                    )
                    grouped_timesheets = [(timesheet.sudo().browse(group["ids"]), group["unit_amount"]) for group in raw_timesheets_group]

                else:
                    time_data = timesheet.sudo().read_group(domain, [field, 'unit_amount:sum'], [field])
                    mapped_time = dict([(m[field][0] if m[field] else False, m['unit_amount']) for m in time_data])
                    grouped_timesheets = [(timesheet.sudo().concat(*g), mapped_time[k.id]) for k, g in groupbyelem(main_res, itemgetter(field))]
                return main_res, grouped_timesheets

            grouped_timesheets = [(
                main_res,
                sum(timesheet.sudo().search(domain).mapped('unit_amount'))
            )] if main_res else []
            return main_res, grouped_timesheets

        main_res, grouped_timesheets = get_timesheets_data()


        values = {
            'data1': data,
            'timesheet': main_res,
            'page_name': 'contract',
            'default_url': '/my/contracts/%s/timesheet'%data.id,
            'search_in': search_in,
            'search': search,
            'sortby': sortby,
            'groupby': groupby,
            'filterby': filterby,
            'searchbar_filters': OrderedDict(sorted(searchbar_filters.items())),
            'searchbar_sortings': searchbar_sortings,
            'searchbar_inputs': searchbar_inputs,
            'searchbar_groupby': searchbar_groupby,

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
    def prepare_timesheets_download(self, contract_id, **kw):
        contract = request.env['hr.contract'].sudo().search([('id', '=', contract_id)])
        content, content_type = request.env.ref(
            'contract_management_setu.portal_timesheet_report').sudo()._render_qweb_pdf(
            res_ids=contract.timesheet_ids.ids)
        reporthttpheaders = [
            ('Content-Type', 'application/pdf'),
            ('Content-Length', len(content)),
        ]
        filename = contract.name + ".pdf"
        reporthttpheaders.append(('Content-Disposition', content_disposition(filename)))
        return request.make_response(content, headers=reporthttpheaders)
