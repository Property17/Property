# -*- coding: utf-8 -*-
import json
from odoo import http, _, fields
from odoo.http import request
from odoo.addons.payment.controllers.portal import PaymentPortal
from odoo.tools.misc import formatLang

from odoo.exceptions import AccessError, MissingError, ValidationError
from odoo.fields import Command

try:
    from babel.dates import format_date as babel_format_date
except ImportError:
    babel_format_date = None


def _public_company_logo_url(company):
    """Return a company logo URL that works for anonymous portal visitors.

    ``/web/image?model=res.company&field=logo`` checks record rules; public users often get
    AccessError and Odoo serves the grey placeholder (broken image on mobile/desktop).
    Core ``/logo?company=`` (``web.controllers.binary.company_logo``) reads ``logo_web`` with
    ``auth=none`` and is intended for unauthenticated pages.
    """
    if not company:
        return ''
    return '/logo?company=%s' % int(company.id)


def _compute_unpaid_rent_schedules(tenancy):
    return tenancy.rent_schedule_ids.filtered(
        lambda rs: rs.move_check and not rs.paid
    )


def _compute_unpaid_service_rents(tenancy):
    """Unpaid invoiced services (``tenancy.service_ids`` / ``service.rent``)."""
    if 'service.rent' not in tenancy.env:
        return tenancy.env['service.rent']
    if 'service_ids' in tenancy._fields:
        return tenancy.service_ids.filtered(
            lambda sr: sr.posted and not sr.paid and sr.move_id
        )
    return tenancy.env['service.rent'].sudo().search([
        ('tenancy_id', '=', tenancy.id),
        ('posted', '=', True),
        ('paid', '=', False),
        ('move_id', '!=', False),
    ])


def _compute_all_unpaid_invoices(tenancy):
    """All customer invoices due on the payment link (rent + services)."""
    rent_invoices = _compute_unpaid_rent_schedules(tenancy).mapped('invoice_id')
    service_invoices = _compute_unpaid_service_rents(tenancy).mapped('move_id')
    return (rent_invoices | service_invoices).filtered(
        lambda inv: inv.state == 'posted' and inv.amount_residual > 0
    )


def _parse_id_list(value):
    """Parse JSON list of ids from the portal (string or list)."""
    if not value:
        return []
    if isinstance(value, str):
        try:
            value = json.loads(value)
        except (TypeError, ValueError):
            return []
    if not isinstance(value, list):
        return []
    return [int(x) for x in value if str(x).isdigit()]


def _compute_paid_rent_schedules(tenancy):
    return tenancy.rent_schedule_ids.filtered(
        lambda rs: (
            rs.move_check and rs.paid and rs.invoice_id
            and rs.invoice_id.invoice_payments_widget
            and rs.invoice_id.invoice_payments_widget.get('content')
            and len(rs.invoice_id.invoice_payments_widget['content']) > 0
        )
    )


def _compute_tenancy_invoices_props(tenancy):
    unpaid_rent_schedules = _compute_unpaid_rent_schedules(tenancy)
    unpaid_service_rents = _compute_unpaid_service_rents(tenancy)
    tenancy_lines_dict = {}
    for rs in unpaid_rent_schedules:
        inv = rs.invoice_id
        if not inv:
            continue
        line_key = f'rent_{rs.id}'
        tenancy_lines_dict[line_key] = [{
            'line_key': line_key,
            'line_type': 'rent',
            'rent_schedule_id': rs.id,
            'service_rent_id': False,
            'date': str(rs.start_date),
            'invoice_name': inv.name or '',
            'line_label': _('Rent'),
            'invoice_date_due': (
                str(inv.invoice_date_due) if inv.invoice_date_due else ''
            ),
            'invoice_amount_residual': inv.amount_residual,
        }]
    for sr in unpaid_service_rents:
        inv = sr.move_id
        if not inv:
            continue
        line_key = f'service_{sr.id}'
        tenancy_lines_dict[line_key] = [{
            'line_key': line_key,
            'line_type': 'service',
            'rent_schedule_id': False,
            'service_rent_id': sr.id,
            'date': str(sr.start_date or sr.date or ''),
            'invoice_name': inv.name or '',
            'line_label': sr.service_type_id.name or _('Service'),
            'invoice_date_due': (
                str(inv.invoice_date_due) if inv.invoice_date_due else ''
            ),
            'invoice_amount_residual': inv.amount_residual,
        }]
    return {
        'tenancy_lines': tenancy_lines_dict,
        'flexible_payment': tenancy.flexible_payment if tenancy.flexible_payment is not None else False,
    }


def _format_period_month_year(date_val):
    """Format date as month-year (e.g. January-2026) to match PDF receipt."""
    if not date_val:
        return ''
    if babel_format_date:
        return babel_format_date(date_val, format='MMMM-y', locale='en')
    return date_val.strftime('%B-%Y') if hasattr(date_val, 'strftime') else str(date_val)


def _compute_tenancy_payments_props(tenancy, company_image_url):
    """Build payment receipt data for OWL component (kept for modal View) and server-side rendering.
    Field names and formatting aligned with Rent Collection Receipt PDF (ايصال تحصيل ايجار)."""
    env = request.env
    paid_rent_schedules = _compute_paid_rent_schedules(tenancy)
    tenancy_lines = {}
    tenancy_payments_list = []  # Flat list for server-side QWeb (avoids OWL duplication)
    for rs in paid_rent_schedules:
        inv = rs.invoice_id
        widget = inv.invoice_payments_widget or {}
        content = widget.get('content', [])
        first_payment = content[0] if content else {}
        paid_amount = first_payment.get('amount', 0)
        currency = inv.currency_id or tenancy.company_id.currency_id
        # Collector name (اسم المحصل) from account.payment
        collector_name = ''
        payment_id = first_payment.get('account_payment_id')
        if payment_id:
            payment = env['account.payment'].sudo().browse(payment_id)
            if payment.exists():
                collector_name = (payment.create_uid.name or '') if payment.create_uid else ''
        ref = first_payment.get('ref', '') or ''
        residual = inv.amount_residual
        line_data = {
            'rent_schedule_id': rs.id,
            'payment_id': str(content),
            'date': str(rs.start_date),
            'invoice_id': inv.id,
            'invoice_token': inv.access_token,
            'invoice_name': inv.name,
            'receipt_number': inv.name,
            'payment_link_report_url': (
                '/tenancy_payment_link/tenant_partner/payment_report/%s?access_token=%s'
                % (inv.id, inv.access_token)
            ),
            'payment_date': str(first_payment.get('date', '')),
            'tenancy_id': tenancy.id,
            'tenancy_name': tenancy.name,
            'invoice_due_date': str(inv.invoice_date_due),
            'invoice_amount': rs.amount,
            'invoice_amount_formatted': formatLang(env, rs.amount, currency_obj=currency),
            'customer_name': tenancy.tenant_id.name,
            'unit': tenancy.property_id.name,
            'unit_serial_number': tenancy.property_id.auto_add_no or '',
            'period_formatted': _format_period_month_year(rs.start_date),
            'paid_amount': str(paid_amount),
            'paid_amount_formatted': formatLang(env, paid_amount, currency_obj=currency),
            'paid_amount_words': tenancy.change_amount_to_word(paid_amount, 'ar_001'),
            'residual_amount': residual,
            'residual_amount_formatted': formatLang(env, residual, currency_obj=currency),
            'payment_transaction_id': str(first_payment.get('date', '')),
            'payment_method': str(first_payment.get('payment_method_name', '')),
            'reference_number': ref,
            'payment_details': ref,
            'collector_name': collector_name,
        }
        tenancy_lines[rs.id] = [line_data]
        tenancy_payments_list.append(line_data)
    company = tenancy.company_id
    company_name = company.name or ''
    company_location = company.country_id.name if company and company.country_id else ''
    return {
        'tenancy_lines': tenancy_lines,
        'tenancy_payments_list': tenancy_payments_list,
        'tenancy_payments_json': json.dumps(tenancy_payments_list),
        'company_image_url': company_image_url,
        'company_name': company_name,
        'company_location': company_location,
    }


class PropertyPaymentLink(PaymentPortal):

    @http.route('/tenancy_payment_link/tenant_partner/<int:tenancy>',
                auth='public', type='http', website=True, methods=['GET', 'POST'], csrf=False)
    def payment_link(self, tenancy, access_token=None, **kw):
        # access_token is optional in signature so route matches even when param is missing
        if not access_token:
            raise request.not_found()
        # Validate access and get payment link for tracking
        payment_link = request.env['property.payment.link'].sudo().search([
            ('tenancy_id', '=', tenancy),
            ('access_token', '=', access_token),
        ], limit=1)
        if not payment_link:
            raise request.not_found()
        tenancy_record = request.env['account.analytic.account'].sudo().browse(tenancy)
        if not tenancy_record.exists():
            raise request.not_found()
        payment_link.write({'last_login_date': fields.Datetime.now()})
        company_image_url = _public_company_logo_url(tenancy_record.company_id)
        tenancy_account_move = _compute_all_unpaid_invoices(tenancy_record)
        unpaid_rent_schedules = _compute_unpaid_rent_schedules(tenancy_record)
        unpaid_service_rents = _compute_unpaid_service_rents(tenancy_record)
        has_payable = bool(unpaid_rent_schedules or unpaid_service_rents)
        # Ensure portal tokens exist for all invoices
        for invoice in tenancy_account_move:
            invoice._portal_ensure_token()
        
        # Use the first invoice for payment context (or sum all amounts if needed)
        # If no invoices, create a dummy recordset to avoid errors
        account_move = tenancy_account_move[0] if tenancy_account_move else request.env['account.move']
        
        ctx = dict(request.env.context)
        ctx.update({
            'tenancy_token': [access_token]
        })
        
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
        
        paid_rent_schedules = _compute_paid_rent_schedules(tenancy_record)
        tenancy_invoices_props = _compute_tenancy_invoices_props(tenancy_record)
        tenancy_payments_props = _compute_tenancy_payments_props(
            tenancy_record, company_image_url
        )

        tenancy_info = {
            'property_manager': tenancy_record.property_manager_id.name or '',
            'tenant': tenancy_record.tenant_id.name or '',
            'tenancy': tenancy_record.name or '',
            'phone': tenancy_record.tenant_id.phone or '',
            'property': tenancy_record.property_id.name or '',
            'email': tenancy_record.tenant_id.email or '',
        }
        values.update({
            'tenancy': tenancy_record,
            'company_image_url': company_image_url,
            'tenancy_invoices': tenancy_account_move,
            'tenancy_access_token': access_token,
            'flexible_payment': tenancy_record.flexible_payment,
            'unpaid_rent_schedules': unpaid_rent_schedules,
            'unpaid_service_rents': unpaid_service_rents,
            'has_payable': has_payable,
            'paid_rent_schedules': paid_rent_schedules,
            'tenancy_invoices_props': tenancy_invoices_props,
            'tenancy_payments_props': tenancy_payments_props,
            'tenancy_info_json': json.dumps(tenancy_info),
        })

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
        
        # Select payment providers. For tenancy + logged in: use provider from company user is in
        # (multi-company support). Fallback to invoice company if none found.
        provider_company_id = invoice_company.id
        if tenancy and logged_in:
            # Try current user's company first
            providers_sudo = request.env['payment.provider'].sudo()._get_compatible_providers(
                request.env.company.id,
                partner_sudo.id,
                amount_for_providers,
                currency_id=invoice.currency_id.id,
                **kwargs,
            )
            if providers_sudo:
                provider_company_id = request.env.company.id
            else:
                # Fallback to invoice company
                providers_sudo = request.env['payment.provider'].sudo()._get_compatible_providers(
                    invoice_company.id,
                    partner_sudo.id,
                    amount_for_providers,
                    currency_id=invoice.currency_id.id,
                    **kwargs,
                )
        else:
            providers_sudo = request.env['payment.provider'].sudo()._get_compatible_providers(
                provider_company_id,
                partner_sudo.id,
                amount_for_providers,
                currency_id=invoice.currency_id.id,
                **kwargs,
            )

        payment_methods_sudo = request.env['payment.method'].sudo()._get_compatible_payment_methods(
            providers_sudo.ids,
            partner_sudo.id,
            currency_id=invoice.currency_id.id,
        )  # In sudo mode to read the fields of providers.
        tokens_sudo = request.env['payment.token'].sudo()._get_available_tokens(
            providers_sudo.ids, partner_sudo.id
        )  # In sudo mode to read the partner's tokens (if logged out) and provider fields.

        # For tenancy payment links: allow payment regardless of logged-in user's company.
        # The tenant accesses via token; payment providers are selected by invoice/tenancy company.
        if tenancy:
            company_mismatch = False
        else:
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
            db_part = f'&db={request.db}' if request.db else ''
            landing_route = f'/tenancy_payment_link/tenant_partner/{tenancy.id}?access_token={tenancy_access_token}{db_part}'
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

        kwargs.update({
            'currency_id': invoice_sudo.currency_id.id,
            'partner_id': partner_sudo.id,
        })  # Inject the create values taken from the invoice into the kwargs.
        tx_sudo = self._create_transaction(
            custom_create_values={'invoice_ids': [Command.set([invoice_id])]}, **kwargs,
        )
        return tx_sudo._get_processing_values()

    @http.route('/tenancy/transaction/<int:tenancy_id>/', type='json', auth='public')
    def tenancy_transaction(
        self,
        tenancy_id,
        access_token=None,
        selected_rent_schedule_ids=None,
        selected_service_rent_ids=None,
        **kwargs,
    ):
        """Create a transaction for selected rent and service invoices on a tenancy."""
        tenancy = request.env['account.analytic.account'].sudo().browse(tenancy_id)
        if tenancy.is_blocked or tenancy.state == 'blocked':
            raise ValidationError(_(
                "Payments are blocked for this tenancy. Please contact the property manager."
            ))

        if not selected_rent_schedule_ids and 'selected_rent_schedule_ids' in kwargs:
            selected_rent_schedule_ids = kwargs.get('selected_rent_schedule_ids')
        if not selected_service_rent_ids and 'selected_service_rent_ids' in kwargs:
            selected_service_rent_ids = kwargs.get('selected_service_rent_ids')

        kwargs.pop('access_token', None)
        kwargs.pop('selected_rent_schedule_ids', None)
        kwargs.pop('selected_service_rent_ids', None)

        all_rent_schedules = _compute_unpaid_rent_schedules(tenancy)
        all_service_rents = _compute_unpaid_service_rents(tenancy)

        rent_schedule_ids = _parse_id_list(selected_rent_schedule_ids)
        service_rent_ids = _parse_id_list(selected_service_rent_ids)

        if not tenancy.flexible_payment:
            rent_schedules = all_rent_schedules
            service_rents = all_service_rents
        else:
            if not rent_schedule_ids and not service_rent_ids:
                raise ValidationError(_("Please select at least one invoice to pay."))
            rent_schedules = all_rent_schedules.filtered(
                lambda rs: rs.id in rent_schedule_ids
            ) if rent_schedule_ids else all_rent_schedules.browse()
            service_rents = all_service_rents.filtered(
                lambda sr: sr.id in service_rent_ids
            ) if service_rent_ids else all_service_rents.browse()

        invoices = (
            rent_schedules.mapped('invoice_id') | service_rents.mapped('move_id')
        ).filtered(lambda inv: inv.amount_residual > 0)

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
        return tx_sudo._get_processing_values()
