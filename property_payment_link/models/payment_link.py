# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError, RedirectWarning
import logging
_logger = logging.getLogger(__name__)

try:
    from num2words import num2words
except ImportError:
    _logger.warning("The num2words python library is not installed, amount-to-text features won't be fully available.")
    num2words = None


class PropertyPaymentLink(models.Model):
    _name = 'property.payment.link'
    _description = 'Property Payment Link'
    _inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin']
    _rec_name = 'name'

    name = fields.Char(compute='_compute_name', string="Name", store=True, readonly=True)
    tenancy_id = fields.Many2one('account.analytic.account', string="Tenancy", required=True, tracking=True)
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company, tracking=True)
    
    # Related fields from tenancy_id - no need for @api.depends, Odoo handles related fields automatically
    property_manager_id = fields.Many2one(related='tenancy_id.property_manager_id', string="Property Manager", store=False)
    property_id = fields.Many2one(related='tenancy_id.property_id', string="Property", store=False)
    property_parent_id = fields.Many2one(related='property_id.parent_id', string="Property Parent", store=False)
    tenant_id = fields.Many2one(related='tenancy_id.tenant_id', string="Tenant", store=False)
    tenant_phone = fields.Char(related='tenant_id.phone', string="Phone", store=False)
    tenancy_status = fields.Selection(
        [('template', 'Template'),
         ('draft', 'New'),
         ('book', 'Booked'),
         ('open', 'In Progress'),
         ('pending', 'To Renew'),
         ('close', 'Closed'),
         ('blocked', 'Blocked'),
         ('cancelled', 'Cancelled')],
        related='tenancy_id.state', string="Tenancy Status", store=False)
    flexible_payment = fields.Boolean(related='tenancy_id.flexible_payment', string="Flexible Payment", store=False)
    block_payment = fields.Boolean(compute='_compute_block_payment', string="Block Payments", store=False)
    # Computed fields
    multi_properitis = fields.Char(compute='_compute_multi_properties', string="Properties", store=False)
    total_amount_due = fields.Float(compute='_compute_total_amount_due', string="Total Amount Due", store=False)
    
    # Direct fields
    last_sent_date = fields.Datetime(string="Last Sent Date", tracking=True)
    last_login_date = fields.Datetime(string="Last Login Date", tracking=True)
    tenant_url = fields.Char()
    access_url = fields.Char()

    @api.depends('tenancy_id', 'tenant_id')
    def _compute_name(self):
        """Compute name based on tenancy and tenant"""
        for link in self:
            if link.tenancy_id and link.tenant_id:
                link.name = f"{link.tenancy_id.name} - {link.tenant_id.name}"
            elif link.tenancy_id:
                link.name = link.tenancy_id.name
            else:
                link.name = f"Payment Link #{link.id}" if link.id else "New Payment Link"

    @api.depends('tenancy_id', 'tenancy_id.rent_schedule_ids', 'tenancy_id.rent_schedule_ids.move_check', 
                 'tenancy_id.rent_schedule_ids.paid', 'tenancy_id.rent_schedule_ids.invoice_id', 
                 'tenancy_id.rent_schedule_ids.invoice_id.amount_residual')
    def _compute_total_amount_due(self):
        """Compute total outstanding amount from unpaid invoices"""
        for link in self:
            if link.tenancy_id:
                # Get unpaid rent schedules that have invoices
                unpaid_rent_schedules = link.tenancy_id.rent_schedule_ids.filtered(
                    lambda rs: rs.move_check and not rs.paid and rs.invoice_id
                )
                # Get invoices from unpaid rent schedules
                unpaid_invoices = unpaid_rent_schedules.mapped('invoice_id')
                # Sum the outstanding amounts
                link.total_amount_due = sum(inv.amount_residual for inv in unpaid_invoices)
            else:
                link.total_amount_due = 0.0

    @api.depends('flexible_payment')
    def _compute_block_payment(self):
        """Compute block_payment as inverse of flexible_payment"""
        for link in self:
            link.block_payment = not link.flexible_payment

    @api.depends('property_id')
    def _compute_multi_properties(self):
        """Compute multi properties from property_id"""
        for link in self:
            if link.property_id:
                # Check if multi_properties field exists on the property model
                try:
                    if 'multi_properties' in link.property_id._fields:
                        link.multi_properitis = link.property_id.multi_properties
                    else:
                        # Fallback: use property name if multi_properties doesn't exist
                        link.multi_properitis = link.property_id.name or False
                except Exception:
                    link.multi_properitis = link.property_id.name or False
            else:
                link.multi_properitis = False

    def _compute_access_url(self):
        super()._compute_access_url()
        for link in self:
            link.access_url = '/tenancy_payment_link/tenant_partner/%s' % (link.tenancy_id.id)

    def _whatsapp_get_portal_url(self):
        """Return portal URL for WhatsApp template (tenant payment link)"""
        self.ensure_one()
        return self.get_portal_url()

    def _wa_get_safe_phone_fields(self):
        """Phone fields allowed for WhatsApp template on property.payment.link"""
        return {'tenant_phone', 'tenant_id.phone', 'tenant_id.mobile'}

    def create_payment_link_message(self):
        for link in self:
            link.tenant_url = link.get_portal_url()

    def send_payment_link(self):
        """Open WhatsApp composer to send payment link to tenant via WhatsApp (with template selection)"""
        self.ensure_one()
        self.tenant_url = self.get_portal_url()
        self.last_sent_date = fields.Datetime.now()

        if not self.tenant_phone and not (self.tenant_id and self.tenant_id.phone):
            raise UserError(_('Please set a phone number on the tenant (%s) before sending the payment link via WhatsApp.') % (self.tenant_id.name or ''))

        wa_template = self.env['whatsapp.template']._find_default_for_model('property.payment.link')
        if not wa_template:
            wa_template = self.env['whatsapp.template'].search([
                ('model', '=', 'property.payment.link'),
                ('status', 'in', ('draft', 'pending', 'approved')),
            ], limit=1)
        if not wa_template:
            action = self.env.ref(
                'property_payment_link.action_create_whatsapp_template',
                raise_if_not_found=False
            )
            if action:
                raise RedirectWarning(
                    _('No WhatsApp template is configured for Payment Links. Click "Create Template" to create one.'),
                    action.id,
                    _('Create Template'),
                )
            raise UserError(_(
                'No WhatsApp template is configured for Payment Links. '
                'Go to WhatsApp > Templates and create a template with Applies to = "Property Payment Link".'
            ))

        return {
            'type': 'ir.actions.act_window',
            'name': _('Send via WhatsApp'),
            'res_model': 'whatsapp.composer',
            'view_mode': 'form',
            'views': [(False, 'form')],
            'target': 'new',
            'context': {
                'active_model': 'property.payment.link',
                'active_id': self.id,
                'active_ids': [self.id],
                'default_phone': self.tenant_phone or (self.tenant_id.phone if self.tenant_id else ''),
                'default_wa_template_id': wa_template.id,
            },
        }

    def action_send_payment_link_bulk(self):
        """Open WhatsApp composer for bulk send - works on multiple selected property.payment.link records"""
        if not self:
            raise UserError(_('Please select at least one Payment Link to send.'))
        records_without_phone = self.filtered(
            lambda r: not r.tenant_phone and not (r.tenant_id and r.tenant_id.phone)
        )
        if records_without_phone:
            raise UserError(_(
                'The following Payment Links have no phone number set on the tenant: %s. '
                'Please set a phone number before sending.'
            ) % ', '.join(records_without_phone.mapped('name')))

        for link in self:
            link.tenant_url = link.get_portal_url()
        self.write({'last_sent_date': fields.Datetime.now()})

        wa_template = self.env['whatsapp.template']._find_default_for_model('property.payment.link')
        if not wa_template:
            wa_template = self.env['whatsapp.template'].search([
                ('model', '=', 'property.payment.link'),
                ('status', 'in', ('draft', 'pending', 'approved')),
            ], limit=1)
        if not wa_template:
            action = self.env.ref(
                'property_payment_link.action_create_whatsapp_template',
                raise_if_not_found=False
            )
            if action:
                raise RedirectWarning(
                    _('No WhatsApp template is configured for Payment Links. Click "Create Template" to create one.'),
                    action.id,
                    _('Create Template'),
                )
            raise UserError(_(
                'No WhatsApp template is configured for Payment Links. '
                'Go to WhatsApp > Templates and create a template with Applies to = "Property Payment Link".'
            ))

        return {
            'type': 'ir.actions.act_window',
            'name': _('Send via WhatsApp (Bulk)'),
            'res_model': 'whatsapp.composer',
            'view_mode': 'form',
            'views': [(False, 'form')],
            'target': 'new',
            'context': {
                'active_model': 'property.payment.link',
                'active_id': self[0].id,
                'active_ids': self.ids,
                'default_wa_template_id': wa_template.id,
            },
        }

    def action_create_whatsapp_template(self):
        """Create WhatsApp template for Property Payment Link if missing, then open it."""
        Template = self.env['whatsapp.template']
        template = Template.search([('model', '=', 'property.payment.link')], limit=1)
        if not template:
            model_id = self.env['ir.model']._get_id('property.payment.link')
            if not model_id:
                raise UserError(_('Model Property Payment Link not found.'))
            template = Template.create({
                'name': 'Payment Link',
                'model_id': model_id,
                'phone_field': 'tenant_phone',
                'body': 'Hello! Your payment link is ready. Please use the link below to complete your payment:\n\n{{1}}',
                'template_type': 'utility',
                'footer_text': 'Thank you for your payment.',
            })
            var = template.variable_ids.filtered(lambda v: v.name == '{{1}}' and v.line_type == 'body')
            if var:
                var.write({
                    'field_type': 'portal_url',
                    'demo_value': 'https://example.com/tenancy_payment_link/tenant_partner/1',
                })
        return {
            'type': 'ir.actions.act_window',
            'name': _('WhatsApp Template - Payment Link'),
            'res_model': 'whatsapp.template',
            'res_id': template.id,
            'view_mode': 'form',
            'target': 'current',
            'context': {'search_default_model': 'property.payment.link'},
        }

    def action_open_tenancy(self):
        """Open the related tenancy using property_management form view"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Tenancy',
            'res_model': 'account.analytic.account',
            'res_id': self.tenancy_id.id,
            'view_mode': 'form',
            'view_id': self.env.ref('property_management.property_analytic_view_form').id,
            'target': 'current',
        }


class AccountMove(models.Model):
    _inherit = 'account.analytic.account'

    is_blocked = fields.Boolean('Block')
    flexible_payment = fields.Boolean('Flexible Payment')
    payment_link_count = fields.Integer(
        string='Payment Link Count',
        compute='_compute_payment_link_count')
    
    def _compute_payment_link_count(self):
        for tenancy in self:
            tenancy.payment_link_count = self.env['property.payment.link'].search_count([
                ('tenancy_id', '=', tenancy.id)
            ])
    
    def action_view_payment_links(self):
        """Open payment links for this tenancy. Create one if none exists."""
        self.ensure_one()
        payment_link = self.env['property.payment.link'].search([
            ('tenancy_id', '=', self.id)
        ], limit=1)
        if not payment_link:
            payment_link = self.create_payment_link()
        if payment_link:
            return {
                'type': 'ir.actions.act_window',
                'name': _('Link Payment'),
                'res_model': 'property.payment.link',
                'res_id': payment_link.id,
                'view_mode': 'form',
                'target': 'current',
                'context': {
                    'default_tenancy_id': self.id,
                    'default_company_id': self.company_id.id if self.company_id else self.env.company.id,
                },
            }
        action = self.env.ref(
            'property_payment_link.action_tenant_payment_link_view',
            raise_if_not_found=False
        )
        if not action:
            return {'type': 'ir.actions.act_window_close'}
        return {
            **action.read()[0],
            'domain': [('tenancy_id', '=', self.id)],
            'context': {
                'default_tenancy_id': self.id,
                'default_company_id': self.company_id.id if self.company_id else self.env.company.id,
            },
        }

    def button_start(self):
        """Override: create payment link when contract starts."""
        res = super().button_start()
        for tenancy in self:
            tenancy.create_payment_link()
        return res

    def create_payment_link(self):
        """Create a property.payment.link record for this tenancy"""
        self.ensure_one()
        payment_link_obj = self.env['property.payment.link']
        
        # Check if payment link already exists for this tenancy
        existing_link = payment_link_obj.search([('tenancy_id', '=', self.id)], limit=1)
        
        if existing_link:
            return existing_link
        
        # Create new payment link
        payment_link = payment_link_obj.create({
            'tenancy_id': self.id,
            'company_id': self.company_id.id if self.company_id else self.env.company.id,
        })
        
        # Generate the portal URL
        payment_link.create_payment_link_message()
        
        return payment_link

    def change_amount_to_word(self, number, lang):
        if num2words is None:
            _logger.warning("The library 'num2words' is missing, cannot render textual amounts.")
            return ""

        return num2words(number, lang=lang).title()