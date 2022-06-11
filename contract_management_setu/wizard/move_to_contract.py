from odoo import _, api, fields, models
from odoo.exceptions import UserError
import datetime


class MoveToContract(models.TransientModel):
    _name = 'move.to.contract'

    contract_id = fields.Many2one('hr.contract', string="Contract")
    customer_id = fields.Many2one('res.partner')

    @api.model
    def default_get(self, fields):
        defaults = super(MoveToContract, self).default_get(fields)
        res_ids = self.env.context.get('active_ids')
        res_model = self.env.context.get('active_model')
        if res_ids and res_model:
            task_ids = self.env[res_model].browse(res_ids)
            partner_id = task_ids.mapped('partner_id')
            if len(partner_id) > 1:
                raise UserError(_("Selected line having different Partner(s). \n"
                                  "Please select line for one Partner at a time !!"))
        defaults.update({
            'customer_id': partner_id
        })
        if not partner_id:
            raise UserError(_("Some of the Task line does not have Partner(s). \n"
                              "Please select Task line in which Partner is assigned !!"))
        return defaults

    def update_contract(self):
        res_model = self.env.context.get('active_model')
        res_ids = self.env.context.get('active_ids')
        records = self.env[res_model].browse(res_ids)
        if res_model == 'account.analytic.line':
            if self.contract_id.date_start:
                records = records.filtered(lambda rec: rec.create_date.date() >= self.contract_id.date_start)
            else:
                raise UserError(_("Some of the line does not have start date. \n"
                                  "Please select line in which start date is assigned"))
        for rec in records:
            if res_ids and res_model and rec.project_id.is_contract_use:
                rec.contract_id = self.contract_id
