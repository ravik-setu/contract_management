from odoo import fields, models


class AccountAnalyticLine(models.Model):
    _inherit = 'account.analytic.line'

    contract_id = fields.Many2one("hr.contract", string="Contract")

    def write(self, vals):
        """
        Added By:Nidhi Dhruv | Date: 7th April,2022 | Task : 610
        Use:1)To get the last record of contract
            2)This method is used to calculate the remaining quantity and used quantity of hr.contract
        """
        for contract in self:
            if contract.project_id and contract.project_id.contract_ids:
                vals.update({
                'contract_id': contract.project_id.contract_ids[-1]
                })

        super(AccountAnalyticLine, self).write(vals)
        self.contract_id.remaining_quantity -= self.unit_amount
        self.contract_id.used_quantity = ((self.contract_id.total_contract_service_hours - self.contract_id.remaining_quantity) / self.contract_id.total_contract_service_hours) * 100
