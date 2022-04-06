from odoo import fields, models


class AccountAnalyticLine(models.Model):
    _inherit = 'account.analytic.line'

    contract_id = fields.Many2one("hr.contract", string="Contract")