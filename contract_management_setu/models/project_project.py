from odoo import fields, models, api


class Project(models.Model):
    _inherit = 'project.project'

    contract_invoice_count = fields.Integer(compute='_compute_contract_invoice_count', string="Contract Invoice Count")
    contract_count = fields.Integer(string="Contract", compute="_compute_project_contract")

    def action_view_customer_invoice(self):
        """
        Added By: Jigna J Savaniya | Date: 8th April,2022 | Task : 600
        Use: This method is used to show invoices of perticular project
        """
        action = self.env["ir.actions.actions"]._for_xml_id("account.action_move_out_invoice_type")
        domain = eval(action['domain'])
        domain.append(('id', 'in', self.get_project_invoice()))
        action['domain'] = domain
        return action

    def _compute_contract_invoice_count(self):
        """
        Added By: Jigna J Savaniya | Date: 7th April,2022 | Task : 600
        Use: This method is used to count invoices as per project
        """
        for project in self:
            project.contract_invoice_count = len(project.get_project_invoice())

    def get_project_invoice(self):
        """
        Added By: Jigna J Savaniya | Date: 9th April,2022 | Task : 600
        Use: This method is used to get invoice ids based on project and contract
        """
        return self.env['account.move'].search([('project_id', '=', self.id)]).ids

    def action_view_customer_contract(self):
        """
        Added By: Jigna J Savaniya | Date: 11th April,2022 | Task : 600
        Use: This method is used to view contract ids based on project
        """
        action = self.env["ir.actions.actions"]._for_xml_id("contract_management_setu.customer_contract_action")
        action['domain'] = [('id', '=', self.get_customer_contract())]
        return action

    def _compute_project_contract(self):
        """
        Added By: Jigna J Savaniya | Date: 11th April,2022 | Task : 600
        Use: This method is used to calculate contract based on project
        """
        self.contract_count = len(self.get_customer_contract())

    def get_customer_contract(self):
        """
        Added By: Jigna J Savaniya | Date: 11th April,2022 | Task : 600
        Use: This method is used to get contract ids based on project
        """
        return self.env["hr.contract"].search([('project_id', '=', self.id)]).ids