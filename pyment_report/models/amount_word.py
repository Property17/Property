# -*- coding: utf-8 -*-

from odoo import api, fields, models,_
from datetime import datetime
from num2words import num2words
from .money_to_text_ar import amount_to_text_arabic


class AccountPaymentInherit(models.Model):
    _inherit = 'account.payment'

    def amount_text_arabic(self,amount):
        return amount_to_text_arabic(amount, self.company_id.currency_id.name)

    is_terms_or_not = fields.Boolean(compute='_compute_is_terms_or_not')
    # mm_move_id = fields.Many2one('account.move', compute='_compute_mm_move_id')
    amount_char = fields.Char(compute='_compute_amount_char')
    invoice_date = fields.Date(related='mm_move_id.invoice_date')
    
    mm_move_id = fields.Many2one('account.move', compute='_compute_mm_move_id', store=True)

    # def _compute_mm_move_id(self):
    #     moves = self.env['account.move'].search([('name', 'in', self.mapped('ref'))])
    #     move_map = {move.name: move for move in moves}
    #     for rec in self:
    #         rec.mm_move_id = move_map.get(rec.ref)


    def _compute_amount_char(self):
        for rec in self:
            rec.amount_char = num2words(rec.amount, lang='ar_001') + _(" فقط ")

    def _compute_mm_move_id(self):
        for rec in self:
            mm_move_id = self.env['account.move'].search([('name', '=', rec.ref)])
            if mm_move_id:
                for move in mm_move_id:
                    if move:
                        rec.mm_move_id = move.id
                    else:
                        rec.mm_move_id = False
            else:
                rec.mm_move_id = False