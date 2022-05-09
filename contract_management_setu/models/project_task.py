# -*- coding: utf-8 -*-

from odoo import fields, models, api
import logging
_logger = logging.getLogger(__name__)

class ProjectTask(models.Model):
    """ This model is added to give relation between Task and Contract"""
    _inherit = 'project.task'

    contract_id = fields.Many2one('hr.contract', string="Contract", tracking=1)
    is_contract_use = fields.Boolean(string="Is Contract Use?", related="project_id.is_contract_use", store=True)

    @api.onchange('project_id')
    def _onchange_project_id(self):
        """
        This method will set latest contract from project
        """
        for task in self:
            if task.project_id.is_contract_use:
                if not self.env.context.get('default_contract_id'):
                    task.contract_id = task.project_id.get_latest_contract().id if not task.project_id.default_contract else task.project_id.default_contract.id

    @api.model
    def create(self, vals):
        res = super(ProjectTask, self).create(vals)
        for record in res:
            if record.is_contract_use:
                emails = self.env['res.partner']
                if record.project_id.task_create_email_to_customer:
                    emails += record.contract_id.partner_id
                if record.project_id.task_create_email_to_reponsible:
                    emails += record.contract_id.hr_responsible_id.partner_id

                view_context = dict(record._context)
                view_context.update(
                    {'email_subject_task_create_customer': '',
                     'email_subject_task_create_responsible': '', })

                email_values = {
                    'email_to': ','.join(partner.email for partner in emails)
                }

                temp_id = self.env.ref('contract_management_setu.email_template_for_task_created_customer').id
                template_customer = self.env['mail.template'].browse(temp_id)
                try:
                    template_customer.with_context(view_context).send_mail(record.id, force_send=True,
                                                                           email_values=email_values)
                except Exception as e:
                    _logger.info(
                        "Error {} comes at the time of sending task create email, Task {}: {}".format(e, record.id,
                                                                                                           record.name))

        return res
