from odoo import api, fields, models, _
from odoo.exceptions import ValidationError, UserError
import logging
_logger = logging.getLogger(__name__)

class HrContract(models.Model):
    _name = 'hr.contract'
    _inherit = ['hr.contract', 'mail.thread', 'mail.activity.mixin']
    _order = 'id desc'

    partner_id = fields.Many2one("res.partner", string="Customer", tracking=1)
    project_id = fields.Many2one("project.project", string="Project", tracking=1,
                                 domain="[('partner_id', '=', partner_id)]")
    contract_uom = fields.Selection([('hours', 'Hours'), ('days', 'Days')], default='days', tracking=1, copy=False)
    from_date = fields.Date(string="From Date", tracking=1, copy=False)
    to_date = fields.Date(string="To Date", tracking=1, copy=False)
    hours_per_day = fields.Float(string="Hours Per Day", tracking=1, copy=False)
    total_contract_service_hours = fields.Float(string="Total Contract Service Hours",
                                                compute='_compute_total_contract_service_hours', store=True)
    contract_quantity = fields.Float(string="Contract Quantity", tracking=1, copy=False)
    remaining_quantity = fields.Float(string="Remaining Quantity")
    utilised_quantity = fields.Float(string="Utilised Quantity")
    invoice_count = fields.Integer(string='Invoice Count', compute='_compute_invoice_count')
    description = fields.Html(string="Description")
    is_maintain_timesheet = fields.Boolean(string="Maintain a timesheet ?")
    timesheet_ids = fields.One2many("account.analytic.line", 'contract_id', string="Timesheet")
    payment_count = fields.Integer(string="Payment Count", compute='_compute_payment_count')
    timesheet_count = fields.Integer(string="Timesheet Count", compute='compute_timesheet')

    task_ids = fields.One2many('project.task', 'contract_id', string="Tasks")
    task_count = fields.Integer(string='Tasks', compute='_compute_task_count')
    expiry_status = fields.Selection([
        ('running', 'Running'), ('near_to_expire', 'Near To Expire'), ('expired', 'Expired')],
        string="Expiry Status", compute="_compute_expiry_status", store=True)

    @api.depends('contract_uom', 'hours_per_day', 'contract_quantity', 'timesheet_ids.unit_amount')
    def _compute_total_contract_service_hours(self):
        """
        Added By: Jigna J Savaniya | Date: 6th April,2022 | Task : 600
        Use: This method is used to calculate contract service hours as per contract uom
        """
        for contract in self:
            if contract.contract_uom == 'hours':
                contract.total_contract_service_hours = contract.contract_quantity
                contract.hours_per_day = 0.00
            elif contract.contract_uom == 'days':
                contract.total_contract_service_hours = round(contract.hours_per_day * contract.contract_quantity, 2)

            total_timesheet = sum(contract.timesheet_ids.mapped('unit_amount'))
            contract.remaining_quantity = contract.total_contract_service_hours - total_timesheet
            contract.utilised_quantity = contract.total_contract_service_hours and (
                        total_timesheet / contract.total_contract_service_hours) * 100 or 0.0
            if contract.utilised_quantity > contract.total_contract_service_hours and not contract.project_id.allow_over_timesheet:
                raise UserError("Sorry you can not enter task entry more than contract hours")

    @api.constrains('contract_quantity', 'timesheet_ids')
    def check_contract_quantity(self):
        """
        Added By: Nidhi Dhruv | Date: 11th April,2022 | Task : 610
        Use:  Generates Error if contract_quantity is decreased then the mentioned contract_quantity
        """
        for contract in self:
            sum_of_unit_amount = sum(contract.timesheet_ids.mapped('unit_amount'))
            if self.contract_quantity < sum_of_unit_amount or sum_of_unit_amount > contract.total_contract_service_hours:
                raise ValidationError(_("Cannot descrease the Contract Quantity as timesheet already exists "))

    def action_view_customer_invoice(self):
        """
        Added By: Jigna J Savaniya | Date: 6th April,2022 | Task : 600
        Use: This method is used to show invoices of perticular project
        """
        action = self.env["ir.actions.actions"]._for_xml_id("account.action_move_out_invoice_type")
        domain = eval(action['domain'])
        domain.append(('id', 'in', self.get_project_and_contract_invoice()))
        context = {
            'default_move_type': 'out_invoice',
        }
        if len(self) == 1:
            context.update({
                'default_partner_id': self.partner_id.id,
                'default_project_id': self.project_id.id,
                'default_contract_id': self.id,
            })
        action['context'] = context
        action['domain'] = domain
        return action

    def _compute_invoice_count(self):
        """
        Added By: Jigna J Savaniya | Date: 7th April,2022 | Task : 600
        Use: This method is used to count invoices as per project
        """
        for contract in self:
            contract.invoice_count = len(self.get_project_and_contract_invoice())

    def get_project_and_contract_invoice(self):
        """
        Added By: Jigna J Savaniya | Date: 9th April,2022 | Task : 600
        Use: This method is used to get invoice ids based on project and contract
        """
        return self.env['account.move'].search(
            [('project_id', '=', self.project_id.id), ('contract_id', '=', self.id)]).ids

    def action_view_customer_payment(self):
        """
        Added By: Jigna J Savaniya | Date: 9th April,2022 | Task : 600
        Use: This method is used to show payments of invoices based on contract invoice
        """
        action = self.env["ir.actions.actions"]._for_xml_id("account.action_account_payments")
        move_ids = self.get_payment_of_invoices()
        action['domain'] = [('move_id', 'in', move_ids)]
        return action

    def _compute_payment_count(self):
        """
        Added By: Jigna J Savaniya | Date: 9th April,2022 | Task : 600
        Use: This method is used to calculate payments of invoices based on contract invoice
        """
        move_ids = self.get_payment_of_invoices()
        self.payment_count = len(move_ids)

    def get_payment_of_invoices(self):
        """
        Added By: Jigna J Savaniya | Date: 9th April,2022 | Task : 600
        Use: This method is used to get move ids based on contract
        """
        invoices = self.env['account.move'].search([('contract_id', '=', self.id)])
        move_ids = []
        for move in invoices:
            for partial, amount, counterpart_line in move._get_reconciled_invoices_partials():
                data = (move._get_reconciled_vals(partial, amount, counterpart_line))
                data and move_ids.append(data.get('move_id'))
        return move_ids

    def action_view_time_sheet(self):
        """
        Added By: Jigna J Savaniya | Date: 11th April,2022 | Task : 600
        Use: This method is used to show timesheet as per contract
        """
        action = self.env["ir.actions.actions"]._for_xml_id("hr_timesheet.act_hr_timesheet_line")
        action['domain'] = [('id', 'in', self.get_timesheet_of_contract())]
        return action

    def compute_timesheet(self):
        """
        Added By: Jigna J Savaniya | Date: 11th April,2022 | Task : 600
        Use: This method is used to calculate timesheet as per contract
        """
        self.timesheet_count = len(self.get_timesheet_of_contract())

    def get_timesheet_of_contract(self):
        """
        Added By: Jigna J Savaniya | Date: 11th April,2022 | Task : 600
        Use: This method is used to get timesheet ids based on contract
        """
        return self.env['account.analytic.line'].search([('contract_id', '=', self.id)]).ids

    def _compute_task_count(self):
        """
        Added By: Mitrarajsinh Jadeja | Date: 11th April,2022 | Task : 653
        Use: This method will count the task for the Contract
        """
        for contract in self:
            contract.task_count = len(contract.task_ids)

    def action_view_tasks(self):
        """
        Added By: Mitrarajsinh Jadeja | Date: 11th April,2022 | Task : 653
        Use: This method will count the task related to particular Contract
             Pass default value to create task under that project/contract
        """
        if not self.task_ids and self.state == 'draft':
            raise UserError('There is no Task in the Contract.\n'
                            'Please move contract to `Running` status to create task.')
        action = self.env["ir.actions.actions"]._for_xml_id("project.action_view_all_task")
        action['domain'] = [('id', 'in', self.task_ids.ids)]
        action['context'] = {
            'default_project_id': self.project_id.id,
            'default_contract_id': self.id
        }
        return action

    @api.depends('remaining_quantity', 'utilised_quantity')
    def _compute_expiry_status(self):
        """
        Added By: Mitrarajsinh Jadeja | Date: 11th April,2022 | Task : 653
        Use: This method will set the expiry status for the contract
        """
        for contract in self:
            contract_expire_percent = contract.project_id.expire_percent
            contract_used = contract.utilised_quantity and (contract.utilised_quantity / 100)
            if contract_expire_percent < contract_used < 1:
                contract.expiry_status = 'near_to_expire'
            elif contract_used == 1:
                contract.expiry_status = 'expired'
            else:
                contract.expiry_status = 'running'

    @api.model
    def default_get(self, fields):
        res = super(HrContract, self).default_get(fields)
        context = self.env.context
        if context.get('active_model') == 'project.project':
            project = self.env["project.project"].browse(context.get('active_id'))
            res.update({'partner_id': project.partner_id.id, 'project_id': project.id})
        if context.get('active_model') == 'res.partner':
            res.update({'partner_id': context.get('active_id')})
        return res

    @api.model
    def create(self, vals):
        res = super(HrContract, self).create(vals)
        if res.contract_quantity <= 0:
            raise UserError("Total Contract Service Hours must be positive")
        if res.to_date < res.from_date:
            raise UserError("End date must be greater than start date")
        return res

    def write(self, vals):
        res = super(HrContract, self).write(vals)
        if vals.get('state') == 'close':
            for rec in self:
                if rec.project_id.is_contract_use:
                    rec.send_email_on_contract_expired()
        return res

    def send_email_on_contract_expired(self):
        for contract in self:
            emails = self.env['res.partner']
            if contract.project_id.expired_contract_email_to_customer:
                emails += contract.partner_id
            if contract.project_id.expired_contract_email_to_reponsible:
                emails += contract.hr_responsible_id.partner_id
            emil_to = ','.join(partner.email for partner in emails)
            if emil_to:
                view_context = self.env.context.copy()
                email_values = {
                    'email_to': emil_to
                }
                temp_id = self.env.ref('contract_management_setu.contract_expired_email_template').id
                template_responsible = self.env['mail.template'].browse(temp_id)
                try:
                    template_responsible.send_mail(contract.id, force_send=True,
                                                                              email_values=email_values)
                except Exception as e:
                    _logger.info(
                        "Error {} comes at the time of sending contract expire mail {}:{}".format(e, contract.id,
                                                                                                  contract.name))

    def near_to_expire_email_automation(self):
        projects = self.env['project.project'].search([('is_contract_use', '=', True)])
        contracts = self.env['hr.contract'].search(
            [('expiry_status', '=', 'near_to_expire'), ('state', '=', 'open'), ('project_id', '!=', False),
             ('project_id', 'in', projects.ids)])
        for record in contracts:
            emails = self.env['res.partner']
            if record.project_id.near_to_expire_email_to_customer:
                emails += record.partner_id
            if record.project_id.near_to_expire_email_to_reponsible:
                emails += record.hr_responsible_id.partner_id
            emil_to = ','.join(partner.email for partner in emails)
            view_context = self.env.context.copy()
            if emil_to:
                email_values = {
                    'email_to': emil_to
                }
                temp_id = self.env.ref(
                    'contract_management_setu.contract_expiry_email_template').id
                template_customer = self.env['mail.template'].browse(temp_id)
                try:
                    template_customer.with_context(view_context).send_mail(record.id, force_send=True,
                                                                           email_values=email_values)
                except Exception as e:
                    _logger.info(
                        "Error {} comes at the time of sending near to expire email contract {}:{}".format(e, record.id,
                                                                                                           record.name))
