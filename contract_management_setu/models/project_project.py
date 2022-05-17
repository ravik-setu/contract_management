# -*- coding: utf-8 -*-
from odoo import fields, models, api, _
from odoo.exceptions import UserError


class ProjectProject(models.Model):
    _inherit = 'project.project'

    contract_invoice_count = fields.Integer(compute='_compute_contract_invoice_count', string="Contract Invoice Count")
    contract_count = fields.Integer(string="Contract", compute="_compute_project_contract")
    expire_percent = fields.Float(string="Expiry Percent",
                                  help="By this percentage, Contract/Project expiry status can be identify.")
    is_contract_use = fields.Boolean(string="Manage Contract", default=False)


    default_contract = fields.Many2one("hr.contract", string="Default Contract")


    task_create_email_to_customer = fields.Boolean(string="Send Task Create Email To Customer",default=False)
    expired_contract_email_to_customer = fields.Boolean(string="Send Contract Expiry Email To Customer", default=False)
    near_to_expire_email_to_customer = fields.Boolean(string="Send Near To Expire Email To Customer", default=False)

    task_create_email_to_reponsible = fields.Boolean(string="Send Task Create Email To Reponsible", default=False)
    expired_contract_email_to_reponsible = fields.Boolean(string="Send Contract Expiry Email To Reponsible", default=False)
    near_to_expire_email_to_reponsible = fields.Boolean(string="Send Near To Expire Email To Reponsible", default=False)
    allow_over_timesheet = fields.Boolean(string="Allow Over Timesheet", default=False)

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

    @api.constrains('expire_percent')
    def check_progress_percent(self):
        """
        Added By: Mitrarajsinh Jadeja | Date: 11th April,2022 | Task : 653
        Use: Allowing only expiry percentage between 0 to 100
        """
        for project in self:
            if not (0 <= project.expire_percent <= 1):
                raise UserError(_('Expiry Percentage should be between 0 to 100 !!'))

    def get_latest_contract(self):
        """
        Added By: Mitrarajsinh Jadeja | Date: 11th April,2022 | Task : 653
        Use: This method will give the latest contract for the project.
        """
        contract_ids = self.env['hr.contract'].search([('project_id', '=', self.id)])
        contract_ids = contract_ids.filtered(lambda contract: contract.state == 'open')
        return contract_ids and contract_ids[0] or contract_ids

    @api.model
    def default_get(self, default_fields):
        result = super().default_get(default_fields)
        if self.env.context.get('default_partner_id'):
            result.update({'partner_id': self.env.context.get('default_partner_id')})
        return result

    def raise_error_if_email_not_set(self):
        if self.partner_id and not self.partner_id.email:
            raise UserError("Email must be set into Customer {}".format(self.partner_id.name))

    @api.model
    def create(self, vals):
        res = super(ProjectProject, self).create(vals)
        if res.partner_id and (
                res.task_create_email_to_customer or res.expired_contract_email_to_customer or res.near_to_expire_email_to_customer):
            res.raise_error_if_email_not_set()
        return res

    def write(self, vals):
        if vals.get('task_create_email_to_customer') or vals.get('expired_contract_email_to_customer') or vals.get(
                'near_to_expire_email_to_customer'):
            for rec in self:
                rec.raise_error_if_email_not_set()
        return super(ProjectProject, self).write(vals)

    def action_open_project_contracts(self):
        res = super(ProjectProject, self).action_open_project_contracts()
        contracts = self.env['hr.contract'].search(
            [('analytic_account_id', '!=', False), ('analytic_account_id', 'in', self.analytic_account_id.ids)])
        if (len(contracts) == 1):
            res["views"] = [[self.env.ref('hr_contract.hr_contract_view_form').id, 'form']]
        else:
            res.update({'views': [[self.env.ref('hr_contract.hr_contract_view_kanban').id, 'kanban'],
                                  [self.env.ref('hr_contract.hr_contract_view_tree').id, 'tree'],
                                  [self.env.ref('hr_contract.hr_contract_view_form').id, 'form']]})
        return res
