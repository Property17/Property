# -*- coding: utf-8 -*-

from odoo import api, fields, models
from odoo.tools.image import image_data_uri


class ResCompany(models.Model):
    _inherit = 'res.company'

    stamp = fields.Image(
        string='Stamp',
        max_width=1024,
        max_height=1024,
        help='Company stamp shown on portal payment receipts (التوقيع / الختم).',
    )

    @api.model
    def _resolve_company_for_property_receipt(self, move=None, tenancy=None, payment=None):
        """Pick the res.company whose stamp should print on property receipts."""
        Company = self.env['res.company'].sudo()
        candidates = []
        seen_ids = set()

        def _add(company):
            if company and company.id not in seen_ids:
                seen_ids.add(company.id)
                candidates.append(company)

        def _add_from_partner(partner):
            if not partner:
                return
            if partner.company_id:
                _add(partner.company_id)
            _add(Company.search([('partner_id', '=', partner.id)], limit=1))

        if move and move.company_id:
            _add(move.company_id)
        if payment and payment.company_id:
            _add(payment.company_id)
        if tenancy:
            _add(tenancy.company_id)
            _add_from_partner(tenancy.property_manager_id)
            prop = tenancy.property_id
            if prop:
                mgr = getattr(prop, 'property_manager_id', False) or getattr(
                    prop, 'property_manager', False
                )
                _add_from_partner(mgr)
        if move:
            _add_from_partner(getattr(move, 'property_manager_id', False))
            if move.property_id:
                mgr = getattr(move.property_id, 'property_manager_id', False) or getattr(
                    move.property_id, 'property_manager', False
                )
                _add_from_partner(mgr)

        for company in candidates:
            if company.stamp:
                return company
        return candidates[0] if candidates else self.env.company

    @api.model
    def get_stamp_data_uri(self, company=None, move=None, tenancy=None, payment=None):
        """Base64 data URI for QWeb/PDF stamp rendering."""
        company = company or self._resolve_company_for_property_receipt(
            move=move, tenancy=tenancy, payment=payment,
        )
        company = company.sudo()
        if not company or not company.stamp:
            return False
        return image_data_uri(company.stamp)
