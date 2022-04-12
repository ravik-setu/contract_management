from odoo import api, fields, models,_
from odoo.exceptions import ValidationError

class HrContract(models.Model):
    _name = 'hr.contract'
    _inherit = ['hr.contract', 'mail.thread', 'mail.activity.mixin']

    partner_id = fields.Many2one("res.partner", string="Customer", tracking=1)
    project_id = fields.Many2one("project.project", string="Project", tracking=1)
    contract_uom = fields.Selection([('hours', 'Hours'), ('days', 'Days')], default='days', tracking=1, copy=False)
    from_date = fields.Date(string="From Date", tracking=1, copy=False)
    to_date = fields.Date(string="To Date", tracking=1, copy=False)
    hours_per_day = fields.Float(string="Hours Per Day", tracking=1, copy=False)
    total_contract_service_hours = fields.Float(string="Total Contract Service Hours",
                                                compute='_compute_total_contract_service_hours')
    contract_quantity = fields.Float(string="Contract Quantity", tracking=1, copy=False)
    remaining_quantity = fields.Float(string="Remaining Quantity")
    utilised_quantity = fields.Float(string="Utilised Quantity")
    invoice_count = fields.Integer(string='Invoice Count', compute='_compute_invoice_count')
    description = fields.Html(string="Description")
    is_maintain_timesheet = fields.Boolean(string="Maintain a timesheet ?")
    timesheet_ids = fields.One2many("account.analytic.line", 'contract_id', string="Timesheet")

    @api.depends('contract_uom', 'hours_per_day', 'contract_quantity')
    def _compute_total_contract_service_hours(self):
        """
        Added By: Jigna J Savaniya | Date: 6th April,2022 | Task : 600
        Use: This method is used to calculate contract service hours as per contract uom
        """

        for contract in self:
            sum_of_unit_amount = sum(contract.timesheet_ids.mapped('unit_amount'))
            if contract.contract_uom == 'hours':
                contract.total_contract_service_hours = contract.contract_quantity
                contract.hours_per_day = 0.00
            elif contract.contract_uom == 'days':
                contract.total_contract_service_hours = round(contract.hours_per_day * contract.contract_quantity, 2)
            contract.remaining_quantity = contract.total_contract_service_hours

            if sum_of_unit_amount <= contract.total_contract_service_hours:
                self.remaining_quantity = contract.total_contract_service_hours - sum_of_unit_amount
            if contract.total_contract_service_hours and contract.remaining_quantity > -1:
                self.utilised_quantity = (
                (contract.total_contract_service_hours - contract.remaining_quantity) / contract.total_contract_service_hours) * 100


    @api.constrains('contract_quantity','timesheet_ids')
    def check_contract_quantity(self):
        """
        Added By:Nidhi Dhruv | Date: 11th April,2022 | Task : 610
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
        invoice_ids = self.env['account.move'].search([('project_id', '=', self.project_id.id)])
        domain.append(('id', 'in', invoice_ids.ids))
        action['domain'] = domain
        return action

    @api.depends('project_id.invoice_ids')
    def _compute_invoice_count(self):
        """
        Added By: Jigna J Savaniya | Date: 7th April,2022 | Task : 600
        Use: This method is used to count invoices as per project
        """
        for contract in self:
            invoices = contract.project_id.invoice_ids.filtered(lambda r: r.move_type in ('out_invoice', 'out_refund'))
            contract.invoice_count = len(invoices)
