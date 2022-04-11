from odoo import fields, models, _
from odoo.exceptions import ValidationError


class AccountAnalyticLine(models.Model):
    _inherit = 'account.analytic.line'

    contract_id = fields.Many2one("hr.contract", string="Contract")

    def write(self, vals):
        """
        Added By:Nidhi Dhruv | Date: 7th April,2022 | Task : 610
        Use: 1)To get the last record of contract
            2) Generates Error if sum_of_unit_amount exceeds the total_contract_service_hours
          """
        for timesheet in self:
            if timesheet.project_id.contract_ids:
                contract_id = timesheet.project_id.contract_ids[-1]
                sum_of_unit_amount = sum(contract_id.timesheet_ids.mapped('unit_amount'))
                if sum_of_unit_amount > contract_id.total_contract_service_hours:
                    raise ValidationError(_("NOT ALLLOWED."))
                else:
                    vals.update({
                        'contract_id': contract_id
                    })
                    super(AccountAnalyticLine, self).write(vals)
        return True
