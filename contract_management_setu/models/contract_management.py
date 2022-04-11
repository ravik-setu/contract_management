from odoo import api, fields, models


class HrContract(models.Model):
    _name = 'hr.contract'
    _inherit = ['hr.contract', 'mail.thread', 'mail.activity.mixin']

    partner_id = fields.Many2one("res.partner", string="Customer", tracking=1)
    project_id = fields.Many2one("project.project", string="Project", tracking=1)
    contract_uom = fields.Selection([('hours', 'Hours'), ('days', 'Days')], tracking=1, copy=False)
    from_date = fields.Date(string="From Date", tracking=1, copy=False)
    to_date = fields.Date(string="To Date", tracking=1, copy=False)
    hours_per_day = fields.Float(string="Hours Per Day", tracking=1, copy=False)
    total_contract_service_hours = fields.Float(string="Total Contract Service Hours",
                                                compute='_compute_total_contract_service_hours')
    contract_quantity = fields.Float(string="Contract Quantity", tracking=1, copy=False)
    remaining_quantity = fields.Float(string="Remaining Quantity")
    invoice_count = fields.Integer(string='Invoice Count', compute='_compute_invoice_count')
    description = fields.Html(string="Description")
    is_maintain_timesheet = fields.Boolean(string="Maintain a timesheet ?")
    # timesheet_ids = fields.One2many("account.analytic.line", 'contract_id', string="Timesheet")
    payment_count = fields.Integer(string="Payment Count", compute='_compute_payment_count')
    timesheet_count = fields.Integer(string="Timesheet Count", compute='compute_timesheet')

    @api.depends('contract_uom', 'hours_per_day', 'contract_quantity')
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
            else:
                contract.total_contract_service_hours = 0

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
