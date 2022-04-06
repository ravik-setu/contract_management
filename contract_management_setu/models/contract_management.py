from odoo import api, fields, models


class HrContract(models.Model):
    _name = 'hr.contract'
    _inherit = ['hr.contract', 'mail.thread', 'mail.activity.mixin']

    partner_id = fields.Many2one("res.partner", string="Customer", tracking=1)
    project_id = fields.Many2one("project.project", string="Project", tracking=1)
    contract_uom = fields.Selection([('hours', 'Hours'), ('days', 'Days')], tracking=1)
    from_date = fields.Date(string="From Date", tracking=1)
    to_date = fields.Date(string="To Date", tracking=1)
    hours_per_day = fields.Float(string="Hours Per Day", tracking=1)
    total_contract_service_hours = fields.Float(string="Total Contract Service Hours",
                                                compute='_compute_total_contract_service_hours')
    contract_quantity = fields.Float(string="Contract Quantity", tracking=1)
    remaining_quantity = fields.Float(string="Remaining Quantity")
    invoice_count = fields.Integer(string='Invoice Count')
    description = fields.Html(string="Description")
    maintain_a_timesheet = fields.Boolean(string="Maintain a timesheet ?")
    timesheet_ids = fields.One2many("account.analytic.line", 'contract_id', string="Timesheet")

    @api.depends('contract_uom', 'hours_per_day', 'contract_quantity')
    def _compute_total_contract_service_hours(self):
        for contract in self:
            if contract.contract_uom == 'hours':
                contract.total_contract_service_hours = contract.contract_quantity
            elif contract.contract_uom == 'days':
                contract.total_contract_service_hours = round(contract.hours_per_day * contract.contract_quantity, 2)

    def action_view_customer_invoice(self):
        action = self.env["ir.actions.actions"]._for_xml_id("account.action_move_out_invoice_type")
        get_invoices = self.env['account.move'].search([('project_id', '=', self.project_id.id)])
        action['domain'] = [('id', 'in', get_invoices.ids)]
        return action
