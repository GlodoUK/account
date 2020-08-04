from odoo import models, fields, api


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    reconcile_override = fields.Monetary(
        default=0.0,
        string="Reconcile Override Amount",
        help="Amount to include in this reconciliation. Leave blank to reconcile full amount",
    )

    @api.multi
    def auto_reconcile_lines(self):
        # Create list of debit and list of credit move ordered by date-currency
        debit_moves = self.filtered(lambda r: r.debit != 0 or r.amount_currency > 0)
        credit_moves = self.filtered(lambda r: r.credit != 0 or r.amount_currency < 0)
        debit_moves = debit_moves.sorted(
            key=lambda a: (a.date_maturity or a.date, a.currency_id)
        )
        credit_moves = credit_moves.sorted(
            key=lambda a: (a.date_maturity or a.date, a.currency_id)
        )
        # Compute on which field reconciliation should be based upon:
        if (
            self[0].account_id.currency_id
            and self[0].account_id.currency_id
            != self[0].account_id.company_id.currency_id
        ):
            field = "amount_residual_currency"
            check_amount = self.amount_residual_currency
        else:
            field = "amount_residual"
            check_amount = self.amount_residual

        # if all lines share the same currency, use amount_residual_currency to avoid currency rounding error
        if self[0].currency_id and all(
            [x.amount_currency and x.currency_id == self[0].currency_id for x in self]
        ):
            field = "amount_residual_currency"
            check_amount = self.amount_residual_currency

        if (
            self.reconcile_override
            and self.reconcile_override > 0
            and self.reconcile_override < check_amount
        ):
            field = "reconcile_override"

        # Reconcile lines
        ret = self._reconcile_lines(debit_moves, credit_moves, field)
        self.reconcile_override = 0
        return ret
