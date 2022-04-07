from odoo import api, fields, models


class Partner(models.Model):
    _inherit = 'res.partner'

    contract_count = fields.Integer(string="Contracts", compute='_compute_contract_count')

    def action_view_customer_contract(self):
        """
        Added By: Jigna J Savaniya | Date: 6th April,2022 | Task : 600
        Use: This method is used to show contracts of perticular partner
        """
        action = self.env["ir.actions.actions"]._for_xml_id("contract_management_setu.customer_contract_action")
        contract_ids = self.env['hr.contract'].search([('partner_id', '=', self.contract_ids.partner_id.id)])
        action['domain'] = [('id', 'in', contract_ids.ids)]
        return action

    def _compute_contract_count(self):
        """
        Added By: Jigna J Savaniya | Date: 7th April,2022 | Task : 600
        Use: This method is used to count contract as per partner
        """
        for partner in self:
            contract = self.env['hr.contract'].search([('partner_id', '=', partner.id)])
            partner.contract_count = len(contract)
