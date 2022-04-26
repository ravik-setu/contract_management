from odoo import fields, models, tools


class HrContractReportAnalysis(models.Model):
    _name = 'hr.contract.report.analysis'
    _description = "Report for Invoices of Project"
    _auto = False

    contract_id = fields.Many2one('hr.contract', string="Contract")
    project_id = fields.Many2one("project.project", string="Project")
    partner_id = fields.Many2one("res.partner", string="Customer")
    from_date = fields.Date(string="From Date")
    to_date = fields.Date(string="To Date")
    contract_quantity = fields.Char(string="Contract Quantity")
    total_service_hours = fields.Char(string="Total Quantity")
    invoice_id = fields.Many2one('account.move', string="Invoice")
    invoice_date = fields.Date(string="Invoice  Date")
    invoice_amount = fields.Float(string="Invoice Amount")
    payment_id = fields.Many2one('account.payment', string="Payment")
    payment_date = fields.Date(string="Payment Date")
    payment_amount = fields.Float(string="Payment Amount")

    def init(self):
        """
        Use: Update view everytime when module upgrade
        """
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute("""
            CREATE or REPLACE VIEW {} as ({} UNION {})
        """.format(self._table, self.get_contract_data_without_payment(), self.get_contract_data_with_payment()))

    def get_contract_data_without_payment(self):
        """
        Use: This method will give contract data which payment is not done yet
        """
        sub_query = self.get_contract_data_with_payment()
        self._cr.execute(sub_query)
        result = self._cr.dictfetchall()
        invoice_ids = tuple(res['invoice_id'] for res in result)

        main_query = """
            SELECT row_number() OVER () as id, 
                contract.id as contract_id,
                contract.project_id,
                partner.id as partner_id,
                contract.from_date,
                contract.to_date,
                CONCAT(contract.contract_quantity, ' ', contract.contract_uom) AS contract_quantity,
                CONCAT(contract.total_contract_service_hours, ' hours') AS total_service_hours,
                account_move.id AS invoice_id,
                account_move.invoice_date,
                account_move.amount_total AS invoice_amount,
                null AS payment_id,
                null AS payment_date,
                null AS payment_amount
            FROM account_move
                JOIN hr_contract contract ON contract.id = account_move.contract_id
                JOIN res_partner partner on partner.id = contract.partner_id
            WHERE account_move.contract_id IS NOT NULL AND account_move.state!='draft'
                    AND move_type='out_invoice' AND account_move.id NOT IN {}
        """.format(invoice_ids)
        return main_query

    def get_contract_data_with_payment(self):
        """
        Use: This method will give contract data which payment is done
        """
        main_query = """
            SELECT row_number() OVER () AS id,
                contract.id as contract_id, 
                contract.project_id,
                partner.id as partner_id,
                contract.from_date,
                contract.to_date,
                CONCAT(contract.contract_quantity, ' ', contract.contract_uom) AS contract_quantity,
                CONCAT(contract.total_contract_service_hours, ' hours') AS total_service_hours,
                invoice.id AS invoice_id,
                invoice.invoice_date,
                invoice.amount_total AS invoice_amount,
                payment.id AS payment_id,
                invoice.date AS payment_date,
                payment.amount AS payment_amount
           FROM account_payment payment
                 JOIN account_move move ON move.id = payment.move_id
                 JOIN account_move_line line ON line.move_id = move.id
                 JOIN account_partial_reconcile part ON part.debit_move_id = line.id OR part.credit_move_id = line.id
                 JOIN account_move_line counterpart_line ON part.debit_move_id = counterpart_line.id OR part.credit_move_id = counterpart_line.id
                 JOIN account_move invoice ON invoice.id = counterpart_line.move_id
                 JOIN account_account account ON account.id = line.account_id
                 JOIN hr_contract contract ON contract.id = invoice.contract_id
                 JOIN res_partner partner on partner.id = contract.partner_id
        WHERE invoice.contract_id IS NOT NULL AND  account.internal_type IN ('receivable', 'payable') 
              AND line.id != counterpart_line.id
              AND invoice.move_type in ('out_invoice', 'out_refund', 'in_invoice', 'in_refund', 'out_receipt', 'in_receipt')
        GROUP BY contract.id, contract.project_id, partner.id, payment.id, invoice.id, contract.contract_uom,  
                 contract.from_date, contract.to_date, contract.contract_quantity, invoice.invoice_date
        """
        return main_query
