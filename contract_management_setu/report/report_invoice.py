from odoo import fields, models, tools


class HrContractReportAnalysis(models.Model):
    _name = 'hr.contract.report.analysis'
    _description = "Report for Invoices of Project"
    _auto = False

    partner_name = fields.Many2one("res.partner", string="Customer")
    project_id = fields.Many2one("project.project", string="Project")
    contract_name = fields.Char(string="Contract Name")

    from_date = fields.Date(string="From Date")
    to_date = fields.Date(string="To Date")
    contract_uom = fields.Selection([('hours', 'Hours'), ('days', 'Days')], default='days')
    contract_quantity = fields.Float(string="Contract Quantity")
    invoice_date = fields.Date(string="Invoice  Date")
    payment_date = fields.Date(string="Payment Date")
    payment_amount = fields.Float(string="Payment Amount")
    amount_total_signed = fields.Float(string="Invoice Amount")
    invoice_name = fields.Char(string="Inovice")

    def _select(self):
        select_str = """
        SELECT row_number() OVER () as id, 
        contract.name as contract_name,
        contract.contract_uom,
        contract.project_id,
        contract.from_date,
        contract.to_date,
        contract.contract_quantity,
        account_move.invoice_date,
        Null as payment_date,
        account_move.id AS invoice_id,
        account_move.name AS invoice_name,
        account_move.move_type,
        account_move.amount_total AS payment_amount,
        partner.name as partner_name,
        account_move.amount_total_signed
    """
        return select_str

    def _from(self):
        query = self.get_invoice_from_payment()
        self._cr.execute(query)
        store = self._cr.dictfetchall()
        invoice_ids = tuple(val['invoice_id'] for val in store)
        from_str = """
        account_move
         JOIN hr_contract contract ON contract.id = account_move.contract_id
         JOIN res_partner partner on partner.id = contract.partner_id
        WHERE account_move.contract_id IS NOT NULL 
            AND account_move.state!='draft'
            AND move_type='out_invoice' 
            AND account_move.id 
        NOT IN {}     
        UNION
        {} 
        """.format(invoice_ids, self.get_invoice_from_payment())
        return from_str

    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute("""CREATE or REPLACE VIEW %s as (
            %s
            FROM %s
            )""" % (self._table, self._select(), self._from()))

    def get_invoice_from_payment(self):
        query = """
            SELECT row_number() OVER () AS id,
                contract.name as contract_name, 
                contract.contract_uom,
                contract.project_id,
                contract.from_date,
                contract.to_date,
                contract.contract_quantity,
                invoice.invoice_date,
                invoice.date as payment_date,
                invoice.id AS invoice_id,
                invoice.name AS invoice_name,
                invoice.move_type,
                 payment.amount as payment_amount ,
                partner.name as partner_name,
                move.amount_total_signed
           FROM account_payment payment
                 JOIN account_move move ON move.id = payment.move_id
                 JOIN account_move_line line ON line.move_id = move.id
                 JOIN account_partial_reconcile part ON part.debit_move_id = line.id OR part.credit_move_id = line.id
                 JOIN account_move_line counterpart_line ON part.debit_move_id = counterpart_line.id OR part.credit_move_id = counterpart_line.id
                 JOIN account_move invoice ON invoice.id = counterpart_line.move_id
                 JOIN account_account account ON account.id = line.account_id
                 JOIN hr_contract contract ON contract.id = invoice.contract_id
                 JOIN res_partner partner on partner.id = contract.partner_id
             
        WHERE invoice.contract_id IS NOT NULL 
                    AND  account.internal_type IN ('receivable', 'payable') 
                    AND line.id != counterpart_line.id
                    AND invoice.move_type in ('out_invoice', 'out_refund', 'in_invoice', 'in_refund', 'out_receipt', 'in_receipt')
        GROUP BY payment.id, 
                 invoice.move_type,
                 invoice.id,
                 contract.name,
                 contract.contract_uom,
                 contract.project_id,
                 contract.from_date,
                 contract.to_date,
                 contract.contract_quantity,
                 invoice.invoice_date ,
                 partner.name,
                 move.amount_total_signed   
        """
        return query

# WHERE id NOT IN ()
# ids = [val['id'] for val in values]
# invoice.name as invoice_name,
#                     invoice.move_type,
#                     payment.amount
#                 FROM account_payment payment
#                     JOIN account_move move ON move.id = payment.move_id
#                     JOIN account_move_line line ON line.move_id = move.id
#                     JOIN account_partial_reconcile part ON part.debit_move_id = line.id OR part.credit_move_id = line.id
#                     JOIN account_move_line counterpart_line ON part.debit_move_id = counterpart_line.id OR part.credit_move_id = counterpart_line.id
#                     JOIN account_move invoice ON invoice.id = counterpart_line.move_id
#                     JOIN account_account account ON account.id = line.account_id
#                 WHERE invoice.contract_id IS NOT NULL AND account.internal_type IN ('receivable', 'payable') AND line.id != counterpart_line.id
#                     AND invoice.move_type in ('out_invoice', 'out_refund', 'in_invoice', 'in_refund', 'out_receipt', 'in_receipt')
#                 GROUP BY payment.id, invoice.move_type, invoice.id
