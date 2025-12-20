# See LICENSE file for full copyright and licensing details

from odoo import fields, models, _
import logging

_logger = logging.getLogger(__name__)

class TenancyRentSchedule(models.Model):
    _inherit = "tenancy.rent.schedule"
    
    failed_to_create = fields.Boolean('Failed To Create')
    
    def create_auto_invoice_rent_schedule(self):
        property_inv_type_param = self.env['ir.config_parameter'].sudo().get_param(
            'property_auto_invoice.inv_type')
        if property_inv_type_param == 'automatic':
            today = fields.Date.context_today(self)
            rent_ids = self.env['tenancy.rent.schedule'].search([('paid', '=', False), ('start_date', '=', today)])
            for rent_schedule in rent_ids.filtered(lambda l: l.tenancy_id.state == 'open'):
                if rent_schedule:
                    inv_obj = self.env['account.move'].search(
                        [('date', '=', today), ('new_tenancy_id', '=', rent_schedule.tenancy_id.id)])
                    if not inv_obj:
                        rent_schedule.create_invoice()
                        
    
    def create_invoice_rent_schedule(self):
        """
        Creates an invoice for the rent schedule if the conditions are met.
        """
        for rec in self:
            today = fields.Date.context_today(self)
            if rec.start_date and not rec.invoice_id and rec.start_date <= today:
                rec.create_invoice()


    
    # def create_invoice_rent_schedule(self):
    #     """
    #     Creates an invoice for the rent schedule if the conditions are met.
    #     """
    #     for rec in self:
    #         today = fields.Date.context_today(self)
    #         if not rec.invoice_id and rec.start_date <= today:
    #             rec.create_invoice()            
                
                
    # def create_auto_invoice_rent_schedule_new(self):
    #     """Automatically create invoices for unpaid rent schedules starting on or before today."""
    #     # Check if auto-invoicing is enabled
    #     property_inv_type_param = self.env['ir.config_parameter'].sudo().get_param('property_auto_invoice.inv_type')
    #     if property_inv_type_param != 'automatic':
    #         return

    #     # Get today's date
    #     today = fields.Date.context_today(self)
        
    #     # Search for unpaid rent schedules starting on or before today, not yet invoiced, and linked to open tenancies
    #     rent_ids = self.env['tenancy.rent.schedule'].search([
    #         ('paid', '=', False),
    #         ('start_date', '=', today),  
    #         ('has_created', '=', False),
    #         ('tenancy_id.state', '=', 'open'),  
    #     ], limit=50, order='start_date asc')

    #     if not rent_ids:
    #         return

    #     # Process each rent schedule
    #     for rent_schedule in rent_ids:
    #         try:
    #             _logger.debug(
    #                 f"Processing RentSchedule ID {rent_schedule.id} | Tenancy: {rent_schedule.tenancy_id.name} "
    #                 f"| Start: {rent_schedule.start_date} | HasCreated: {rent_schedule.has_created}"
    #             )

    #             # Check for existing invoices for this tenancy on the same date
    #             inv_obj = self.env['account.move'].search([
    #                 ('date', '=', today),
    #                 ('new_tenancy_id', '=', rent_schedule.tenancy_id.id),
    #                 ('move_type', '=', 'out_invoice'),  # Ensure it's a customer invoice
    #             ])

    #             if not inv_obj:
    #                 # Create the invoice
    #                 rent_schedule.create_invoice()
    #                 # Mark as invoiced to prevent duplicates
    #                 rent_schedule.write({'has_created': True})
    #             else:
    #                 # If an invoice already exists, mark as processed to avoid rechecking
    #                 rent_schedule.write({'has_created': True})
    #         except Exception as e:
    #             # Log the error and continue with the next record
    #             self.env['ir.logging'].create({
    #                 'name': 'Auto Invoice Creation',
    #                 'type': 'server',
    #                 'level': 'ERROR',
    #                 'message': f"Failed to create invoice for rent schedule {rent_schedule.id}: {str(e)}",
    #                 'path': 'tenancy.rent.schedule',
    #                 'func': 'create_auto_invoice_rent_schedule',
    #                 'line': '1',
    #             })
    #             continue
    
    
    # def create_auto_invoice_rent_schedule_new(self):
    #     """Automatically create invoices for unpaid rent schedules starting on or before today."""
    #     # Check if auto-invoicing is enabled
    #     property_inv_type_param = self.env['ir.config_parameter'].sudo().get_param('property_auto_invoice.inv_type')
    #     if property_inv_type_param != 'automatic':
    #         _logger.info("Auto invoice creation disabled by configuration.")
    #         return

    #     today = fields.Date.context_today(self)

    #     # Exclude rent schedules that previously failed
    #     rent_ids = self.env['tenancy.rent.schedule'].search([
    #         ('paid', '=', False),
    #         ('start_date', '=', today),
    #         ('has_created', '=', False),
    #         ('failed_to_create', '=', False),
    #         ('tenancy_id.state', '=', 'open'),
    #     ], limit=50, order='start_date asc')

    #     if not rent_ids:
    #         _logger.info("No eligible rent schedules found for invoicing.")
    #         return

    #     _logger.info(f"Found {len(rent_ids)} rent schedules for {today}: {[r.id for r in rent_ids]}")

    #     for rent_schedule in rent_ids:
    #         try:
    #             _logger.debug(
    #                 f"Processing RentSchedule ID {rent_schedule.id} | Tenancy: {rent_schedule.tenancy_id.name} "
    #                 f"| Start: {rent_schedule.start_date}"
    #             )

    #             inv_obj = self.env['account.move'].search([
    #                 ('date', '=', today),
    #                 ('new_tenancy_id', '=', rent_schedule.tenancy_id.id),
    #                 ('move_type', '=', 'out_invoice'),
    #             ])

    #             if not inv_obj:
    #                 rent_schedule.create_invoice()
    #                 rent_schedule.write({'has_created': True})
    #                 _logger.info(f"Invoice created for RentSchedule ID {rent_schedule.id}")
    #             else:
    #                 rent_schedule.write({'has_created': True})
    #                 _logger.info(f"Invoice already exists for RentSchedule ID {rent_schedule.id}, skipping.")
    #         except Exception as e:
    #             _logger.error(
    #                 f"Error creating invoice for RentSchedule ID {rent_schedule.id}: {str(e)}",
    #                 exc_info=True
    #             )
    #             rent_schedule.write({'failed_to_create': True})
    #             continue
    
    def create_auto_invoice_rent_schedule_new(self):
        """Automatically create invoices for unpaid rent schedules starting on or before today."""
        property_inv_type_param = self.env['ir.config_parameter'].sudo().get_param('property_auto_invoice.inv_type')
        if property_inv_type_param != 'automatic':
            return

        today = fields.Date.context_today(self)

        rent_ids = self.env['tenancy.rent.schedule'].search([
            ('paid', '=', False),
            ('start_date', '=', today),
            # ('start_date', '<=', today),
            ('has_created', '=', False),
            ('failed_to_create', '=', False),
            ('tenancy_id.state', '=', 'open'),
        ], limit=300, order='start_date asc')

        if not rent_ids:
            return

        for rent_schedule in rent_ids:
            try:
                _logger.debug(
                    f"Processing RentSchedule ID {rent_schedule.id} | Tenancy: {rent_schedule.tenancy_id.name} "
                    f"| Start: {rent_schedule.start_date} | HasCreated: {rent_schedule.has_created}"
                )

                inv_obj = self.env['account.move'].search([
                    ('date', '=', today),
                    ('new_tenancy_id', '=', rent_schedule.tenancy_id.id),
                    ('move_type', '=', 'out_invoice'),
                ])

                if not inv_obj:
                    rent_schedule.create_invoice()
                rent_schedule.write({'has_created': True})
            
            except Exception as e:
                _logger.error(f"Failed to create invoice for rent schedule {rent_schedule.id}: {str(e)}")
                rent_schedule.write({'failed_to_create': True})
                self.env.cr.rollback()  # rollback the failed transaction only
                continue
            
    def create_auto_invoice_failed_rent_schedule_new(self):
        """Automatically create invoices for unpaid rent schedules starting on or before today."""
        property_inv_type_param = self.env['ir.config_parameter'].sudo().get_param('property_auto_invoice.inv_type')
        if property_inv_type_param != 'automatic':
            return

        target_date = fields.Date.to_date('2025-11-01')


        rent_ids = self.env['tenancy.rent.schedule'].search([
            ('paid', '=', False),
            ('start_date', '=', target_date),
            ('move_check', '=', False),
            ('has_created', '=', False),
            ('failed_to_create', '=', False),
            ('tenancy_id.state', '=', 'open'),
        ], limit=300, order='start_date asc')

        if not rent_ids:
            return

        for rent_schedule in rent_ids:
            try:
                _logger.debug(
                    f"Processing RentSchedule ID {rent_schedule.id} | Tenancy: {rent_schedule.tenancy_id.name} "
                    f"| Start: {rent_schedule.start_date} | HasCreated: {rent_schedule.has_created}"
                )

                inv_obj = self.env['account.move'].search([
                    ('date', '=', target_date),
                    ('new_tenancy_id', '=', rent_schedule.tenancy_id.id),
                    ('move_type', '=', 'out_invoice'),
                ])

                if not inv_obj:
                    rent_schedule.create_invoice()
                rent_schedule.write({'has_created': True})
            
            except Exception as e:
                _logger.error(f"Failed to create invoice for rent schedule {rent_schedule.id}: {str(e)}")
                rent_schedule.write({'failed_to_create': True})
                self.env.cr.rollback()  # rollback the failed transaction only
                continue




    def manual_create_invoice_rent_schedule(self):
        """Automatically create invoices for unpaid rent schedules starting on or before today."""
        property_inv_type_param = self.env['ir.config_parameter'].sudo().get_param('property_auto_invoice.inv_type')
        if property_inv_type_param != 'automatic':
            return

        today = fields.Date.context_today(self)

        rent_ids = self.env['tenancy.rent.schedule'].search([
            ('paid', '=', False),
            ('start_date', '<=', today),
            ('has_created', '=', False),
            ('failed_to_create', '=', False),
            ('tenancy_id.state', '=', 'open'),
        ], limit=50, order='start_date asc')

        if not rent_ids:
            return

        for rent_schedule in rent_ids:
            try:
                _logger.debug(
                    f"Processing RentSchedule ID {rent_schedule.id} | Tenancy: {rent_schedule.tenancy_id.name} "
                    f"| Start: {rent_schedule.start_date} | HasCreated: {rent_schedule.has_created}"
                )

                inv_obj = self.env['account.move'].search([
                    ('date', '=', today),
                    ('new_tenancy_id', '=', rent_schedule.tenancy_id.id),
                    ('move_type', '=', 'out_invoice'),
                ])

                if not inv_obj:
                    rent_schedule.create_invoice()
                rent_schedule.write({'has_created': True})
            
            except Exception as e:
                _logger.error(f"Failed to create invoice for rent schedule {rent_schedule.id}: {str(e)}")
                rent_schedule.write({'failed_to_create': True})
                self.env.cr.rollback()  # rollback the failed transaction only
                continue