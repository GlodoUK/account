from odoo import _, api, fields, models
from odoo.exceptions import UserError
from odoo.tools import float_is_zero


class AccountPaymentBetterMatching(models.TransientModel):
    _name = "account.payment.better.matching"

    payment_id = fields.Many2one(
        "account.payment", domain=[("move_reconciled", "=", False)], required=True
    )

    payment_currency_id = fields.Many2one(related="payment_id.currency_id")

    payment_amount = fields.Monetary(
        compute="_compute_payment_amount", currency_field="payment_currency_id"
    )

    payment_amount_signed = fields.Monetary(
        related="payment_id.amount", currency_field="payment_currency_id"
    )

    partner_id = fields.Many2one(
        related="payment_id.partner_id", string="Payment Partner", store=False
    )

    mode = fields.Selection(related="payment_id.partner_type", store=False)

    move_line_id = fields.Many2one(
        "account.move.line",
        compute="_compute_move_line_id",
        string="Payment Move Line",
        required=True,
    )

    move_line_residual = fields.Monetary(
        related="move_line_id.amount_residual", currency_field="company_currency_id"
    )

    account_id = fields.Many2one(
        related="move_line_id.account_id",
        string="Payment Move Line Account",
        store=False,
    )

    matched_move_line_ids = fields.Many2many(
        "account.move.line",
        "account_payment_better_matching_lines",
        "wizard_id",
        "move_line_id",
        ondelete="cascade",
    )

    matched_amount_signed = fields.Monetary(
        compute="_compute_matched_total_signed",
        currency_field="company_currency_id",
        string="Matched Amount",
    )

    company_currency_id = fields.Many2one(
        related="move_line_id.account_id.company_id.currency_id",
    )

    balanced = fields.Boolean(compute="_compute_balanced")

    partial_reconcile = fields.Boolean(string="Manually Assign Amounts")

    amount_unmatched = fields.Monetary(
        compute="_compute_matched_total_signed", currency_field="company_currency_id"
    )

    """
    @api.onchange("move_line_id")
    def _onchange_move_line_id(self):
        domain = [
            ('partner_id', '=', self.partner_id.id),
            ('reconciled', '=', False),
            ('account_id', '=', self.account_id.id),
            ('id', '!=', self.move_line_id.id)
        ]
        if self.move_line_id.credit:
            domain += [("debit",">",0)]
        else:
            domain += [("credit",">",0)]
        return {'domain':{'matched_move_line_ids': domain}}
    """

    @api.onchange("partial_reconcile")
    def _update_override_amounts(self):
        for line in self.matched_move_line_ids:
            line.reconcile_override = 0

    @api.depends("matched_move_line_ids", "partial_reconcile")
    def _compute_matched_total_signed(self):
        for record in self:
            lines = record.matched_move_line_ids
            total = 0
            for line in lines:
                if self.partial_reconcile:
                    total += line.reconcile_override
                else:
                    total += line.amount_residual
            record.matched_amount_signed = total
            if record.move_line_residual < 0:
                record.amount_unmatched = (
                    record.move_line_residual + record.matched_amount_signed
                )
            else:
                record.amount_unmatched = (
                    record.move_line_residual - record.matched_amount_signed
                )

    @api.depends("payment_id")
    def _compute_payment_amount(self):
        for record in self:
            if not record.payment_id:
                record.payment_amount = 0.0
                continue

            amount = record.payment_id.amount
            if record.payment_id.payment_type in ["outbound"]:
                amount = amount * -1

            record.payment_amount = amount

    @api.depends("payment_id")
    def _compute_move_line_id(self):
        for record in self:
            if not record.payment_id:
                record.move_line_id = None
                continue

            record.move_line_id = None
            if record.payment_id.payment_type == "outbound":
                record.move_line_id = record.payment_id.line_ids.filtered(
                    lambda r: r.account_id.reconcile and r.debit > 0
                ).id
            else:
                record.move_line_id = record.payment_id.line_ids.filtered(
                    lambda r: r.account_id.reconcile and r.credit > 0
                ).id

    @api.depends("move_line_residual", "matched_amount_signed")
    def _compute_balanced(self):
        for record in self:
            record.balanced = float_is_zero(
                record.amount_unmatched,
                record.company_currency_id.decimal_places,
            )

    def process(self):
        if not self.partner_id:
            raise UserError(_("Payments without a partner can't be matched"))

        if not self.move_line_id:
            raise UserError(_("No move needing to be reconcilced"))

        if not self.matched_move_line_ids:
            raise UserError(_("No moves selected for reconciliation"))

        records = self.env["account.move.line"]

        records |= self.move_line_id
        records |= self.matched_move_line_ids

        context = dict(self._context.copy())
        context.update(
            {
                "partial_reconcile": self.partial_reconcile,
                "payment_move_line": self.move_line_id,
            }
        )
        records.with_context(**context).reconcile()
