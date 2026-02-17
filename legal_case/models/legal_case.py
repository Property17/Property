# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import AccessError, UserError, ValidationError
import logging
_logger = logging.getLogger(__name__)
from datetime import date


class LegalCase(models.Model):
    
    _name = 'legal.case'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec = "name"
    _order = "id desc"
    _description ="Legal Case"
    
    name = fields.Char('Name', tracking=True, readonly=True, copy=False, default='New')
    legal_case_request_id = fields.Many2one('legal.case.request', tracking=True,  string="Request")
    request_type_id = fields.Many2one('request.type', tracking=True,  string="Request Type")
    lawyer_office_id = fields.Many2one('lawyer.office', tracking=True,  string="Lawyer Office")
    date_of_lawsuit = fields.Date(string="Date of Lawsuit", tracking=True, default=lambda self: date.today())
    tenancy_id = fields.Many2one('account.analytic.account', tracking=True,  string="Tenancy")
    property_id = fields.Many2one('account.asset', string="Property")
    properties = fields.Text(related='tenancy_id.multi_properitis', tracking=True,  string='Property')
    tenant_id = fields.Many2one('tenant.partner', related='tenancy_id.tenant_id', string='Tenant')
    tenancy_rent = fields.Monetary(related='tenancy_id.rent',currency_field='currency_id', string='Tenancy Tent')
    case_type_id = fields.Many2one('case.type', string="Case Type")
    currency_id = fields.Many2one("res.currency", related='tenancy_id.currency_id', string="Currency",
                                  default=lambda self: self.env.user.company_id.currency_id.id)
    total_expenditure = fields.Monetary(string='Total Expenditure', related='tenancy_id.total_deb_cre_amt', tracking=True,  currency_field='currency_id')
    case_attachments = fields.Many2many('ir.attachment', 'case_attachment', string='Case Attachment')
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)
    state = fields.Selection([
        ('new', 'New Request'),
        ('send_lwyer_office', 'Send Lwyer Office'),
        ('case_created', 'Case Created'),
        ('stop_case', 'Stop Case'),
        ('cancelled', 'Cancelled'),
    ], string="State", default='new', tracking=True)
    note = fields.Text("Note")
    electronic_case_number = fields.Char("Electronic Case Number", tracking=True)
    
    def action_send_lwyer_office(self):
        for rec in self:
            rec.write({
                'state': 'send_lwyer_office',
            })
    
    def action_case_created(self):
        for rec in self:
            rec.write({
                'state': 'case_created',
            })
            
    
    def action_stop_case(self):
        for rec in self:
            rec.write({
                'state': 'stop_case',
            })
    
    def action_cancelled(self):
        for rec in self:
            rec.write({
                'state': 'cancelled',
            })
            

    
    @api.model
    def create(self, vals):
        if vals.get('name', 'New') == 'New':
            vals['name'] = self.env['ir.sequence'].next_by_code('legal.case') or 'New'
        return super(LegalCase, self).create(vals)
