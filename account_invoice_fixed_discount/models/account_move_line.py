# Copyright 2017 ForgeFlow S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl)

from odoo import _, api, fields, models
from odoo.tools import float_is_zero, frozendict


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    discount_fixed = fields.Monetary(
        string="Discount (Fixed)",
        default=0.0,
        currency_field="currency_id",
        help=(
            "Fixed discount amount per unit (multiplied by quantity). "
            "Line total and journal discount entries use this exact amount, "
            "not a rounded percentage."
        ),
    )

    def _get_fixed_discount_amount_currency(self):
        """Total line discount in document currency (discount_fixed × quantity)."""
        self.ensure_one()
        currency = self.currency_id or self.company_id.currency_id
        return currency.round(self.quantity * self.discount_fixed)

    def _get_discount_price_unit(self):
        """Unit price after applying the exact fixed discount (for taxes and totals)."""
        self.ensure_one()
        currency = self.currency_id or self.company_id.currency_id
        if float_is_zero(self.discount_fixed, precision_rounding=currency.rounding):
            return self.price_unit
        if float_is_zero(self.quantity, precision_rounding=currency.rounding):
            return self.price_unit
        gross = currency.round(self.quantity * self.price_unit)
        net = gross - self._get_fixed_discount_amount_currency()
        return net / self.quantity

    def _get_discount_from_fixed_discount(self):
        """Display discount % (informational; journal uses exact fixed amount)."""
        self.ensure_one()
        currency = self.currency_id or self.company_id.currency_id
        if float_is_zero(self.discount_fixed, precision_rounding=currency.rounding):
            return 0.0
        if float_is_zero(self.price_unit, precision_rounding=currency.rounding):
            return 0.0
        return (self.discount_fixed / self.price_unit) * 100

    @api.depends(
        "quantity",
        "discount",
        "discount_fixed",
        "price_unit",
        "tax_ids",
        "currency_id",
    )
    def _compute_totals(self):
        """Use exact fixed discount amount for subtotals (e.g. 300 − 10 = 290)."""
        done_lines = self.env["account.move.line"]
        for line in self:
            if float_is_zero(
                line.discount_fixed, precision_rounding=line.currency_id.rounding
            ):
                continue
            line_discount_price_unit = line._get_discount_price_unit()
            if line.tax_ids:
                taxes_res = line.tax_ids.compute_all(
                    line_discount_price_unit,
                    quantity=line.quantity,
                    currency=line.currency_id,
                    product=line.product_id,
                    partner=line.partner_id,
                    is_refund=line.is_refund,
                )
                line.price_subtotal = taxes_res["total_excluded"]
                line.price_total = taxes_res["total_included"]
            else:
                currency = line.currency_id
                line.price_subtotal = currency.round(
                    line.quantity * line.price_unit
                ) - line._get_fixed_discount_amount_currency()
                line.price_total = line.price_subtotal

            done_lines |= line

        return super(AccountMoveLine, self - done_lines)._compute_totals()

    @api.depends(
        "account_id",
        "company_id",
        "discount",
        "discount_fixed",
        "price_unit",
        "quantity",
        "currency_rate",
    )
    def _compute_discount_allocation_needed(self):
        """Post journal discount using exact ``discount_fixed``, not rounded %."""
        lines_fixed = self.filtered(
            lambda l: l.display_type == "product"
            and not l.currency_id.is_zero(l.discount_fixed)
        )
        lines_other = self - lines_fixed
        if lines_other:
            super(AccountMoveLine, lines_other)._compute_discount_allocation_needed()

        for line in lines_fixed:
            line.discount_allocation_dirty = True
            discount_allocation_account = line.move_id._get_discount_allocation_account()
            if not discount_allocation_account:
                line.discount_allocation_needed = False
                continue

            discounted_amount_currency = line.currency_id.round(
                line.move_id.direction_sign * line._get_fixed_discount_amount_currency()
            )
            if line.currency_id.is_zero(discounted_amount_currency):
                line.discount_allocation_needed = False
                continue

            discount_allocation_needed = {}
            discount_allocation_needed_vals = discount_allocation_needed.setdefault(
                frozendict({
                    "account_id": line.account_id.id,
                    "move_id": line.move_id.id,
                    "currency_rate": line.currency_rate,
                }),
                {
                    "display_type": "discount",
                    "name": _("Discount"),
                    "amount_currency": 0.0,
                },
            )
            discount_allocation_needed_vals["amount_currency"] += (
                discounted_amount_currency
            )
            discount_allocation_needed_vals = discount_allocation_needed.setdefault(
                frozendict({
                    "move_id": line.move_id.id,
                    "account_id": discount_allocation_account.id,
                    "currency_rate": line.currency_rate,
                }),
                {
                    "display_type": "discount",
                    "name": _("Discount"),
                    "amount_currency": 0.0,
                },
            )
            discount_allocation_needed_vals["amount_currency"] -= (
                discounted_amount_currency
            )
            line.discount_allocation_needed = {
                k: frozendict(v) for k, v in discount_allocation_needed.items()
            }

    @api.model_create_multi
    def create(self, vals_list):
        lines = super().create(vals_list)
        lines._sync_fixed_discount_to_percent()
        return lines

    def write(self, vals):
        res = super().write(vals)
        if any(key in vals for key in ("discount_fixed", "price_unit", "quantity")):
            self._sync_fixed_discount_to_percent()
        return res

    def _sync_fixed_discount_to_percent(self):
        """Keep ``discount`` in sync for UI; amounts use ``discount_fixed`` exactly."""
        for line in self:
            if line.display_type not in (False, "product"):
                continue
            currency = line.currency_id or line.company_id.currency_id
            if float_is_zero(line.discount_fixed, precision_rounding=currency.rounding):
                continue
            discount = line._get_discount_from_fixed_discount()
            if line.discount != discount:
                line.with_context(
                    ignore_discount_onchange=True,
                    check_move_validity=False,
                ).discount = discount

    @api.onchange("discount_fixed")
    def _onchange_discount_fixed(self):
        if self.env.context.get("ignore_discount_onchange"):
            return
        self.env.context = self.with_context(ignore_discount_onchange=True).env.context
        self.discount = self._get_discount_from_fixed_discount()

    @api.onchange("price_unit", "quantity")
    def _onchange_price_unit_quantity_discount_fixed(self):
        if self.env.context.get("ignore_discount_onchange"):
            return
        currency = self.currency_id or self.company_id.currency_id
        if not float_is_zero(self.discount_fixed, precision_rounding=currency.rounding):
            self._onchange_discount_fixed()

    @api.onchange("discount")
    def _onchange_discount(self):
        if self.env.context.get("ignore_discount_onchange"):
            return
        self.env.context = self.with_context(ignore_discount_onchange=True).env.context
        self.discount_fixed = 0.0
