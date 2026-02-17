# -*- coding: utf-8 -*-
from odoo import http, _
from odoo.http import request
from odoo.addons.payment.controllers.portal import PaymentPortal


from odoo.exceptions import AccessError, MissingError, ValidationError
from odoo.fields import Command

class PropertyPaymentLink(PaymentPortal):

    @http.route('/tenancy_payment_link/tenant_partner/<int:tenancy>',
                auth='public', type='http', website=True)
    def payment_link(self, tenancy, access_token, **kw):
        tenancy_record = request.env['account.analytic.account'].sudo().browse(tenancy)
        company_image_url = '/web/image?model=res.company&id=%s&field=logo' % tenancy_record.company_id.id
        # Get all unpaid invoices from rent schedules
        tenancy_account_move = tenancy_record.rent_schedule_ids.filtered(lambda rs: rs.move_check and not rs.paid).mapped('invoice_id')
        # Ensure portal tokens exist for all invoices
        for invoice in tenancy_account_move:
            invoice._portal_ensure_token()
        
        # Use the first invoice for payment context (or sum all amounts if needed)
        # If no invoices, create a dummy recordset to avoid errors
        account_move = tenancy_account_move[0] if tenancy_account_move else request.env['account.move']
        
        print("rrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrr",tenancy_account_move)
        ctx = dict(request.env.context)
        ctx.update({
            'tenancy_token': [access_token]
        })
        print(ctx,"uuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuu",access_token,"uuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuu context ",request.env.context)
        
        # Only get payment values if there's at least one invoice
        if account_move:
            # For tenancy, calculate total from all unpaid invoices
            total_amount = sum(inv.amount_residual for inv in tenancy_account_move)
            # Pass tenancy and access_token so landing_route redirects back to tenancy payment link
            values = self._invoice_get_page_view_values(
                account_move, 
                account_move.access_token, 
                tenancy=tenancy_record, 
                tenancy_access_token=access_token,
                tenancy_total_amount=total_amount,  # Pass total amount for tenancy
                **kw
            )
        else:
            values = {}
        
        values.update({
            'tenancy': tenancy_record,
            'company_image_url': company_image_url,
            'tenancy_invoices': tenancy_account_move,  # Pass all invoices to template
            'tenancy_access_token': access_token,  # Pass access token to template
            'flexible_payment': tenancy_record.flexible_payment,  # Pass flexible_payment flag
        })

        print(request.env.context,"zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz",values)
        return http.request.render('property_payment_link.tenancy_payment_link_detail', values)

    @http.route('/tenancy_payment_link/tenant_partner/payment_report/<int:invoice_id>', type='http', auth="public", website=True)
    def payment_report(self,invoice_id, **kw):
        pdf, _ = request.env['ir.actions.report'].sudo()._render_qweb_pdf('pyment_report.mm_multi_invoice_report_action', res_ids=[invoice_id])
        pdfhttpheaders = [('Content-Type', 'application/pdf'), ('Content-Length', len(pdf))]
        return request.make_response(pdf, headers=pdfhttpheaders)

    def _invoice_get_page_view_values(self, invoice, access_token, tenancy=None, tenancy_access_token=None, tenancy_total_amount=None, **kwargs):
        values = super()._invoice_get_page_view_values(invoice, access_token, **kwargs)

        if not invoice._has_to_be_paid():
            # Do not compute payment-related stuff if given invoice doesn't have to be paid.
            return values

        epd = values.get('epd_discount_amount_currency', 0.0)
        # For tenancy payments, use the total amount from all unpaid invoices
        # Otherwise use the single invoice amount
        if tenancy and tenancy_total_amount is not None:
            discounted_amount = tenancy_total_amount - epd
        else:
            discounted_amount = invoice.amount_residual - epd

        logged_in = not request.env.user._is_public()
        # We set partner_id to the partner id of the current user if logged in, otherwise we set it
        # to the invoice partner id. We do this to ensure that payment tokens are assigned to the
        # correct partner and to avoid linking tokens to the public user.
        partner_sudo = request.env.user.partner_id if logged_in else invoice.partner_id
        invoice_company = invoice.company_id or request.env.company

        # For tenancy payments, use total amount for provider compatibility check
        # Otherwise use single invoice amount
        amount_for_providers = tenancy_total_amount if (tenancy and tenancy_total_amount is not None) else invoice.amount_total
        
        # Select all the payment methods and tokens that match the payment context.
        providers_sudo = request.env['payment.provider'].sudo()._get_compatible_providers(
            invoice_company.id,
            partner_sudo.id,
            amount_for_providers,
            currency_id=invoice.currency_id.id,
            **kwargs,
        )  # In sudo mode to read the fields of providers and partner (if logged out).

        payment_methods_sudo = request.env['payment.method'].sudo()._get_compatible_payment_methods(
            providers_sudo.ids,
            partner_sudo.id,
            currency_id=invoice.currency_id.id,
        )  # In sudo mode to read the fields of providers.
        tokens_sudo = request.env['payment.token'].sudo()._get_available_tokens(
            providers_sudo.ids, partner_sudo.id
        )  # In sudo mode to read the partner's tokens (if logged out) and provider fields.

        # Make sure that the partner's company matches the invoice's company.
        company_mismatch = not PaymentPortal._can_partner_pay_in_company(
            partner_sudo, invoice_company
        )

        portal_page_values = {
            'company_mismatch': company_mismatch,
            'expected_company': invoice_company,
        }
        payment_form_values = {
            'show_tokenize_input_mapping': PaymentPortal._compute_show_tokenize_input_mapping(
                providers_sudo
            ),
        }
        
        # Use tenancy payment link as landing route if tenancy is provided
        if tenancy and tenancy_access_token:
            landing_route = f'/tenancy_payment_link/tenant_partner/{tenancy.id}?access_token={tenancy_access_token}'
            # Use custom tenancy transaction route instead of single invoice route
            transaction_route = f'/tenancy/transaction/{tenancy.id}/'
        else:
            landing_route = invoice.get_portal_url()
            transaction_route = f'/invoice/transaction/{invoice.id}/'
        
        payment_context = {
            'amount': discounted_amount,
            'currency': invoice.currency_id,
            'partner_id': partner_sudo.id,
            'providers_sudo': providers_sudo,
            'payment_methods_sudo': payment_methods_sudo,
            'tokens_sudo': tokens_sudo,
            'transaction_route': transaction_route,
            'landing_route': landing_route,
            'access_token': access_token,
        }
        print(request.env.context,"qqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqq",payment_context)
        values.update(
            **portal_page_values,
            **payment_form_values,
            **payment_context,
            **self._get_extra_payment_form_values(**kwargs),
        )
        return values

    def invoice_transaction(self, invoice_id, access_token, **kwargs):
        """ Create a draft transaction and return its processing values.

        :param int invoice_id: The invoice to pay, as an `account.move` id
        :param str access_token: The access token used to authenticate the request
        :param dict kwargs: Locally unused data passed to `_create_transaction`
        :return: The mandatory values for the processing of the transaction
        :rtype: dict
        :raise: ValidationError if the invoice id or the access token is invalid
        """
        # Check the invoice id and the access token
        try:
            invoice_sudo = self._document_check_access('account.move', invoice_id, access_token)
        except MissingError as error:
            raise error
        except AccessError:
            raise ValidationError(_("The access token is invalid."))

        logged_in = not request.env.user._is_public()
        partner_sudo = request.env.user.partner_id if logged_in else invoice_sudo.partner_id
        self._validate_transaction_kwargs(kwargs)
        print(invoice_id,"zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzwwweewewwewewewe")
        # print(invoice_id,"zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzwwweewewwewewewe",tx_sudo)

        kwargs.update({
            'currency_id': invoice_sudo.currency_id.id,
            'partner_id': partner_sudo.id,
        })  # Inject the create values taken from the invoice into the kwargs.
        tx_sudo = self._create_transaction(
            custom_create_values={'invoice_ids': [Command.set([invoice_id])]}, **kwargs,
        )
        return tx_sudo._get_processing_values()

    @http.route('/tenancy/transaction/<int:tenancy_id>/', type='json', auth='public')
    def tenancy_transaction(self, tenancy_id, access_token=None, selected_rent_schedule_ids=None, **kwargs):
        """Create a transaction for selected invoices in a tenancy"""
        tenancy = request.env['account.analytic.account'].sudo().browse(tenancy_id)
        
        # Check if selected_rent_schedule_ids is in kwargs (might be passed there instead)
        if not selected_rent_schedule_ids and 'selected_rent_schedule_ids' in kwargs:
            selected_rent_schedule_ids = kwargs.get('selected_rent_schedule_ids')
        
        # Remove non-whitelisted params from kwargs before validation
        kwargs.pop('access_token', None)
        kwargs.pop('selected_rent_schedule_ids', None)
        
        # Get all unpaid rent schedules
        all_rent_schedules = tenancy.rent_schedule_ids.filtered(
            lambda rs: rs.move_check and not rs.paid
        )
        
        # If flexible_payment is False, user must pay ALL invoices
        if not tenancy.flexible_payment:
            # Force selection of all invoices
            rent_schedules = all_rent_schedules
            # Validate that all invoices are selected
            if selected_rent_schedule_ids:
                # Parse the selected IDs if it's a string (from JSON)
                if isinstance(selected_rent_schedule_ids, str):
                    import json
                    try:
                        selected_rent_schedule_ids = json.loads(selected_rent_schedule_ids)
                    except:
                        selected_rent_schedule_ids = []
                
                selected_ids = set(selected_rent_schedule_ids) if selected_rent_schedule_ids else set()
                all_ids = set(all_rent_schedules.ids)
                
                # Check if all invoices are selected
                if selected_ids != all_ids:
                    raise ValidationError(_("When flexible payment is disabled, you must pay all invoices. Please select all invoices."))
        else:
            # If flexible_payment or normal mode, allow selection
            if selected_rent_schedule_ids:
                # Parse the selected IDs if it's a string (from JSON)
                if isinstance(selected_rent_schedule_ids, str):
                    import json
                    try:
                        selected_rent_schedule_ids = json.loads(selected_rent_schedule_ids)
                    except:
                        selected_rent_schedule_ids = []
                
                if selected_rent_schedule_ids and len(selected_rent_schedule_ids) > 0:
                    rent_schedules = all_rent_schedules.filtered(
                        lambda rs: rs.id in selected_rent_schedule_ids
                    )
                else:
                    raise ValidationError(_("Please select at least one invoice to pay."))
            else:
                raise ValidationError(_("Please select at least one invoice to pay."))
        
        # Get invoices from selected rent schedules
        invoices = rent_schedules.mapped('invoice_id')
        
        if not invoices:
            raise ValidationError(_("No invoices found for the selected items."))
        
        logged_in = not request.env.user._is_public()
        partner_sudo = request.env.user.partner_id if logged_in else invoices[0].partner_id
        
        self._validate_transaction_kwargs(kwargs)
        
        # Calculate total amount from SELECTED invoices only
        total_amount = sum(inv.amount_residual for inv in invoices)
        
        kwargs.update({
            'currency_id': invoices[0].currency_id.id,
            'partner_id': partner_sudo.id,
            'amount': total_amount,
        })
        
        # Create transaction with SELECTED invoice IDs only
        tx_sudo = self._create_transaction(
            custom_create_values={'invoice_ids': [Command.set(invoices.ids)]},
            **kwargs,
        )
        
        print(f"Created transaction for {len(invoices)} selected invoices: {invoices.ids}")
        return tx_sudo._get_processing_values()
