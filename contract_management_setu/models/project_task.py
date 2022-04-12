# -*- coding: utf-8 -*-

from odoo import fields, models, api


class ProjectTask(models.Model):
    """ This model is added to give relation between Task and Contract"""
    _inherit = 'project.task'

    contract_id = fields.Many2one('hr.contract', string="Contract")
    is_contract_use = fields.Boolean(string="Is Contract Use?", related="project_id.is_contract_use", store=True)

    @api.onchange('project_id')
    def _onchange_project_id(self):
        """
        This method will set latest contract from project
        """
        for task in self:
            if task.project_id.is_contract_use:
                task.contract_id = task.project_id.get_latest_contract().id
