# -*- coding: utf-8 -*-
# See LICENSE file for full copyright and licensing details

from odoo import models, fields, api
from odoo import SUPERUSER_ID
from odoo.tools.translate import _


class WebsiteSetting(models.Model):
    _name = 'website.setting'
    _description="Website Settings"

    name = fields.Binary('Image')


class CrmLeadExt(models.Model):
    _inherit = "crm.lead"

    phone_type = fields.Selection([('mob', 'Mobile'), ('work', 'Work'),
                                   ('home', 'Home')], 'Phone Type')
    when_to_call = fields.Selection([
        ('anytime', 'Anytime'),
        ('morning', 'Morning'),
        ('afternoon', 'Afternoon'),
        ('evening', 'Evening')], 'When to Call?')
    property_id = fields.Many2one('account.asset', 'Property')


class ResPartnerExt(models.Model):
    _inherit = "res.partner"

    fav_assets_ids = fields.Many2many(
        'account.asset',
        'account_asset_partner_rel',
        'partner_id',
        'asset_id',
        string='Favorite Property')


class website(models.Model):
    _inherit = 'website'

    def get_fav_property(self):
        user = self.env['res.users'].browse(SUPERUSER_ID)
        for partner in user:
            partner_id = partner.partner_id
        partner_dic = partner_id.read(['fav_assets_ids'])[0]
        fav_assets = len(partner_dic.get('fav_assets_ids')) or 0
        return fav_assets
