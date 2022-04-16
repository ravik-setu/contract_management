from odoo import fields, models, api


class AccountAnalyticLine(models.Model):
    _inherit = 'account.analytic.line'

    contract_id = fields.Many2one("hr.contract", string="Contract")

    @api.model
    def create(self, vals_list):
        """
        Added By:Nidhi Dhruv | Date: 12th April,2022 | Task : 610
        Use: To get the last record of contract
        """
        record = super(AccountAnalyticLine, self).create(vals_list)
        for timesheet in record:
            if timesheet.task_id.project_id.is_contract_use:
                timesheet.contract_id = timesheet.task_id.contract_id.id
        return record
