from odoo import fields, models


class Project(models.Model):
    _inherit = 'project.project'

    contract_ids = fields.One2many("hr.contract", 'project_id', string="Contract")
    invoice_ids = fields.One2many("account.move", "project_id", string="Invoice")