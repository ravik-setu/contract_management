CREATE OR REPLACE FUNCTION public.get_invoice_with_payment()

    RETURNS TABLE(
        id integer
    ) AS

$BODY$

    BEGIN
    return query
        SELECT invoice.id
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
                 contract.from_date, contract.to_date, contract.contract_quantity, invoice.invoice_date;
    END;

$BODY$
LANGUAGE plpgsql VOLATILE