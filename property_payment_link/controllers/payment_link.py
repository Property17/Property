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


def _compute_unpaid_deposit_invoices(tenancy):
    """Posted deposit receive invoices still due on the tenancy."""
    if hasattr(tenancy, '_payment_link_get_unpaid_deposit_invoices'):
        return tenancy._payment_link_get_unpaid_deposit_invoices()
    invoices = tenancy.env['account.move'].sudo().browse()
    if 'acc_inv_dep_rec_id' in tenancy._fields and tenancy.acc_inv_dep_rec_id:
        invoices |= tenancy.acc_inv_dep_rec_id
    return invoices.filtered(
        lambda inv: inv.state == 'posted' and inv.amount_residual > 0
    )


def _compute_all_unpaid_invoices(tenancy):
    """All customer invoices due on the payment link (rent + services + deposit)."""
    rent_invoices = _compute_unpaid_rent_schedules(tenancy).mapped('invoice_id')
    service_invoices = _compute_unpaid_service_rents(tenancy).mapped('move_id')
    deposit_invoices = _compute_unpaid_deposit_invoices(tenancy)
    return (rent_invoices | service_invoices | deposit_invoices).filtered(
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


def _iter_tenancy_deposit_invoices(tenancy):
    """Posted deposit receive invoices for this tenancy."""
    Move = tenancy.env['account.move'].sudo()
    invoices = Move.browse()
    if 'acc_inv_dep_rec_id' in tenancy._fields and tenancy.acc_inv_dep_rec_id:
        invoices |= tenancy.acc_inv_dep_rec_id
    if 'is_deposit_receive' in Move._fields:
        invoices |= Move.search([
            ('tenancy_id', '=', tenancy.id),
            ('move_type', '=', 'out_invoice'),
            ('is_deposit_receive', '=', True),
            ('state', '=', 'posted'),
        ])
    return invoices


def _compute_paid_deposit_invoices(tenancy):
    """Deposit invoices paid (portal / MyFatoorah / manual), with or without rent schedule."""
    return _iter_tenancy_deposit_invoices(tenancy).filtered(
        lambda inv: inv.payment_state in ('paid', 'in_payment', 'partial')
        and (
            inv.amount_residual == 0
            or (inv.invoice_payments_widget or {}).get('content')
        )
    )


def _payment_for_invoice(env, invoice):
    """Resolve ``account.payment`` linked to a paid customer invoice."""
    widget = invoice.invoice_payments_widget or {}
    content = widget.get('content') or []
    if content:
        payment_id = content[0].get('account_payment_id')
        if payment_id:
            payment = env['account.payment'].sudo().browse(payment_id)
            if payment.exists():
                return payment
    Payment = env['account.payment'].sudo()
    if 'reconciled_invoice_ids' in Payment._fields:
        payment = Payment.search([
            ('reconciled_invoice_ids', 'in', invoice.ids),
            ('state', '=', 'posted'),
        ], limit=1, order='create_date desc, id desc')
        if payment:
            return payment
    return Payment.browse()


def _build_payment_receipt_line(env, tenancy, inv, *, rent_schedule=None, access_token=None):
    """One payment-receipt row for the portal (rent schedule or deposit invoice)."""
    widget = inv.invoice_payments_widget or {}
    content = widget.get('content') or []
    first_payment = content[0] if content else {}
    paid_amount = first_payment.get('amount', 0) or (inv.amount_total - inv.amount_residual)
    currency = inv.currency_id or tenancy.company_id.currency_id
    payment = _payment_for_invoice(env, inv)
    collector_name = ''
    if payment:
        collector_name = (payment.create_uid.name or '') if payment.create_uid else ''
    ref = first_payment.get('ref', '') or (payment.ref if payment else '') or ''
    residual = inv.amount_residual
    is_deposit = bool(
        getattr(inv, 'is_deposit_receive', False)
        or (
            'acc_inv_dep_rec_id' in tenancy._fields
            and tenancy.acc_inv_dep_rec_id
            and tenancy.acc_inv_dep_rec_id.id == inv.id
        )
    )
    inv._portal_ensure_token()
    if is_deposit and payment and access_token:
        report_url = (
            '/tenancy_payment_link/tenant_partner/deposit_report/%s?access_token=%s'
            % (payment.id, access_token)
        )
    else:
        report_url = (
            '/tenancy_payment_link/tenant_partner/payment_report/%s?access_token=%s'
            % (inv.id, inv.access_token)
        )
    line_date = (
        str(rent_schedule.start_date) if rent_schedule
        else str(inv.invoice_date or inv.invoice_date_due or '')
    )
    period_date = rent_schedule.start_date if rent_schedule else inv.invoice_date
    invoice_amount = rent_schedule.amount if rent_schedule else inv.amount_total
    return {
        'line_type': 'deposit' if is_deposit else 'rent',
        'line_label': _('Deposit') if is_deposit else _('Rent'),
        'rent_schedule_id': rent_schedule.id if rent_schedule else False,
        'deposit_invoice_id': inv.id if is_deposit else False,
        'payment_id': str(content),
        'date': line_date,
        'invoice_id': inv.id,
        'invoice_token': inv.access_token,
        'invoice_name': inv.name,
        'receipt_number': inv.name,
        'payment_link_report_url': report_url,
        'payment_date': str(first_payment.get('date', '') or (payment.date if payment else '')),
        'tenancy_id': tenancy.id,
        'tenancy_name': tenancy.name,
        'invoice_due_date': str(inv.invoice_date_due),
        'invoice_amount': invoice_amount,
        'invoice_amount_formatted': formatLang(env, invoice_amount, currency_obj=currency),
        'customer_name': tenancy.tenant_id.name,
        'unit': tenancy.property_id.name,
        'unit_serial_number': tenancy.property_id.auto_add_no or '',
        'period_formatted': _format_period_month_year(period_date),
        'paid_amount': str(paid_amount),
        'paid_amount_formatted': formatLang(env, paid_amount, currency_obj=currency),
        'paid_amount_words': tenancy.change_amount_to_word(paid_amount, 'ar_001'),
        'residual_amount': residual,
        'residual_amount_formatted': formatLang(env, residual, currency_obj=currency),
        'payment_transaction_id': str(first_payment.get('date', '')),
        'payment_method': str(
            first_payment.get('payment_method_name', '')
            or (payment.payment_method_line_id.name if payment and payment.payment_method_line_id else '')
        ),
        'reference_number': ref,
        'payment_details': ref,
        'collector_name': collector_name,
    }


def _compute_tenancy_invoices_props(tenancy):
    unpaid_rent_schedules = _compute_unpaid_rent_schedules(tenancy)
    unpaid_service_rents = _compute_unpaid_service_rents(tenancy)
    unpaid_deposit_invoices = _compute_unpaid_deposit_invoices(tenancy)
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
    for inv in unpaid_deposit_invoices:
        line_key = f'deposit_{inv.id}'
        tenancy_lines_dict[line_key] = [{
            'line_key': line_key,
            'line_type': 'deposit',
            'rent_schedule_id': False,
            'service_rent_id': False,
            'deposit_invoice_id': inv.id,
            'date': str(inv.invoice_date or inv.invoice_date_due or ''),
            'invoice_name': inv.name or '',
            'line_label': _('Deposit'),
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


def _compute_tenancy_payments_props(tenancy, company_image_url, access_token=None):
    """Build payment receipt data for portal (rent schedules + paid deposit invoices)."""
    env = request.env
    paid_rent_schedules = _compute_paid_rent_schedules(tenancy)
    paid_deposit_invoices = _compute_paid_deposit_invoices(tenancy)
    tenancy_lines = {}
    tenancy_payments_list = []
    for rs in paid_rent_schedules:
        inv = rs.invoice_id
        if not inv:
            continue
        line_data = _build_payment_receipt_line(
            env, tenancy, inv, rent_schedule=rs, access_token=access_token,
        )
        tenancy_lines[rs.id] = [line_data]
        tenancy_payments_list.append(line_data)
    for inv in paid_deposit_invoices:
        line_data = _build_payment_receipt_line(
            env, tenancy, inv, access_token=access_token,
        )
        tenancy_lines[f'deposit_{inv.id}'] = [line_data]
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
        unpaid_deposit_invoices = _compute_unpaid_deposit_invoices(tenancy_record)
        has_payable = bool(
            unpaid_rent_schedules or unpaid_service_rents or unpaid_deposit_invoices
        )
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
        paid_deposit_invoices = _compute_paid_deposit_invoices(tenancy_record)
        tenancy_invoices_props = _compute_tenancy_invoices_props(tenancy_record)
        tenancy_payments_props = _compute_tenancy_payments_props(
            tenancy_record, company_image_url, access_token=access_token,
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
            'paid_deposit_invoices': paid_deposit_invoices,
            'has_payment_receipts': bool(tenancy_payments_props.get('tenancy_payments_list')),
            'tenancy_invoices_props': tenancy_invoices_props,
            'tenancy_payments_props': tenancy_payments_props,
            'tenancy_info_json': json.dumps(tenancy_info),
        })

        return http.request.render('property_payment_link.tenancy_payment_link_detail', values)

    @http.route('/tenancy_payment_link/tenant_partner/payment_report/<int:invoice_id>', type='http', auth="public", website=True)
    def payment_report(self, invoice_id, **kw):
        pdf, _ = request.env['ir.actions.report'].sudo()._render_qweb_pdf(
            'pyment_report.mm_multi_invoice_report_action', res_ids=[invoice_id],
        )
        pdfhttpheaders = [('Content-Type', 'application/pdf'), ('Content-Length', len(pdf))]
        return request.make_response(pdf, headers=pdfhttpheaders)

    def _validate_payment_link_access(self, tenancy, access_token):
        if not access_token:
            raise request.not_found()
        link = request.env['property.payment.link'].sudo().search([
            ('tenancy_id', '=', tenancy.id),
            ('access_token', '=', access_token),
        ], limit=1)
        if not link:
            raise request.not_found()
        return link

    @http.route(
        '/tenancy_payment_link/tenant_partner/deposit_report/<int:payment_id>',
        type='http', auth='public', website=True,
    )
    def deposit_report(self, payment_id, access_token=None, **kw):
        """Deposit insurance receipt PDF (ايصال تأمين) for portal download."""
        payment = request.env['account.payment'].sudo().browse(payment_id)
        if not payment.exists():
            raise request.not_found()
        tenancy = payment.tenancy_id
        if not tenancy and payment.reconciled_invoice_ids:
            tenancy = payment.reconciled_invoice_ids[:1].tenancy_id
        if not tenancy:
            raise request.not_found()
        self._validate_payment_link_access(tenancy, access_token)
        deposit_invoices = _iter_tenancy_deposit_invoices(tenancy)
        if payment.reconciled_invoice_ids:
            if not (deposit_invoices & payment.reconciled_invoice_ids):
                raise request.not_found()
        pdf, _ = request.env['ir.actions.report'].sudo()._render_qweb_pdf(
            'pyment_report.action_report_payment_deposite_receipt',
            res_ids=[payment_id],
        )
        headers = [('Content-Type', 'application/pdf'), ('Content-Length', len(pdf))]
        return request.make_response(pdf, headers=headers)

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
        selected_deposit_invoice_ids=None,
        **kwargs,
    ):
        """Create a transaction for selected rent, service, and deposit invoices on a tenancy."""
        tenancy = request.env['account.analytic.account'].sudo().browse(tenancy_id)
        if tenancy.is_blocked or tenancy.state == 'blocked':
            raise ValidationError(_(
                "Payments are blocked for this tenancy. Please contact the property manager."
            ))

        if not selected_rent_schedule_ids and 'selected_rent_schedule_ids' in kwargs:
            selected_rent_schedule_ids = kwargs.get('selected_rent_schedule_ids')
        if not selected_service_rent_ids and 'selected_service_rent_ids' in kwargs:
            selected_service_rent_ids = kwargs.get('selected_service_rent_ids')
        if not selected_deposit_invoice_ids and 'selected_deposit_invoice_ids' in kwargs:
            selected_deposit_invoice_ids = kwargs.get('selected_deposit_invoice_ids')

        kwargs.pop('access_token', None)
        kwargs.pop('selected_rent_schedule_ids', None)
        kwargs.pop('selected_service_rent_ids', None)
        kwargs.pop('selected_deposit_invoice_ids', None)

        all_rent_schedules = _compute_unpaid_rent_schedules(tenancy)
        all_service_rents = _compute_unpaid_service_rents(tenancy)
        all_deposit_invoices = _compute_unpaid_deposit_invoices(tenancy)

        rent_schedule_ids = _parse_id_list(selected_rent_schedule_ids)
        service_rent_ids = _parse_id_list(selected_service_rent_ids)
        deposit_invoice_ids = _parse_id_list(selected_deposit_invoice_ids)

        if not tenancy.flexible_payment:
            rent_schedules = all_rent_schedules
            service_rents = all_service_rents
            deposit_invoices = all_deposit_invoices
        else:
            if not rent_schedule_ids and not service_rent_ids and not deposit_invoice_ids:
                raise ValidationError(_("Please select at least one invoice to pay."))
            rent_schedules = all_rent_schedules.filtered(
                lambda rs: rs.id in rent_schedule_ids
            ) if rent_schedule_ids else all_rent_schedules.browse()
            service_rents = all_service_rents.filtered(
                lambda sr: sr.id in service_rent_ids
            ) if service_rent_ids else all_service_rents.browse()
            deposit_invoices = all_deposit_invoices.filtered(
                lambda inv: inv.id in deposit_invoice_ids
            ) if deposit_invoice_ids else all_deposit_invoices.browse()

        invoices = (
            rent_schedules.mapped('invoice_id')
            | service_rents.mapped('move_id')
            | deposit_invoices
        ).filtered(lambda inv: inv.amount_residual > 0 and inv.state == 'posted')

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
