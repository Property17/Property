# Part of Odoo. See LICENSE file for full copyright and licensing details.

import logging
import requests
import json
from odoo import _, fields, models
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)


class PaymentTransaction(models.Model):
    _inherit = 'payment.transaction'

    capture_manually = fields.Boolean(related='provider_id.capture_manually')

    def _create_payment(self, **extra_create_values):
        """Use only MyFatoorah InvoiceId as payment memo (ref).

        Standard ``account_payment`` builds ``{tx.reference} - {partner} - {provider_reference}``;
        we keep the provider id only (e.g. MyFatoorah InvoiceId).
        """
        self.ensure_one()
        if self.provider_code == 'myfatoorah':
            ref = (self.provider_reference or '').strip() or (self.reference or '').strip()
            return super()._create_payment(ref=ref, **extra_create_values)
        return super()._create_payment(**extra_create_values)

    #=== ACTION METHODS ===#
    def _get_tx_from_notification_data(self, provider_code, notification_data):
        tx = super()._get_tx_from_notification_data(provider_code, notification_data)
        if provider_code != 'myfatoorah':
            return tx
        payment_id = notification_data.get('paymentId')
        if not payment_id and isinstance(notification_data.get('Data'), dict):
            payment_id = notification_data['Data'].get('PaymentId')
        if not payment_id:
            _logger.warning("MyFatoorah notification without paymentId")
            return tx

        provider_recs = self.env['payment.provider'].sudo().search([
            ('code', '=', 'myfatoorah'),
            ('state', 'in', ('enabled', 'test')),
        ])
        response_data = None
        matched_provider = None
        for mf_prov in provider_recs:
            api_key = mf_prov.myfatoorah_token
            base_api_url = mf_prov._myfatoorah_get_api_url()
            url = f"{base_api_url}/v2/GetPaymentStatus"
            payload = json.dumps({
                "Key": payment_id,
                "KeyType": "paymentId"
            })
            headers = {
                'Content-Type': 'application/json',
                'Accept': 'application/json',
                'Authorization': f'Bearer {api_key}',
            }
            response = requests.request("POST", url, headers=headers, data=payload)
            try:
                response_data = response.json()
            except ValueError:
                continue
            if not isinstance(response_data, dict):
                continue
            if response_data.get('IsSuccess') and response_data.get('Data'):
                matched_provider = mf_prov
                break
            response_data = None

        if not response_data or not response_data.get('Data'):
            _logger.error(
                "MyFatoorah GetPaymentStatus failed for payment_id=%s (tried %s provider(s))",
                payment_id, len(provider_recs),
            )
            return tx

        data = response_data['Data']
        inv_txs = data.get('InvoiceTransactions') or []
        payment_status = ''
        for inv_tx in inv_txs:
            if inv_tx.get('PaymentId') == payment_id:
                payment_status = inv_tx.get('TransactionStatus') or ''
                break
        customer_reference = data.get('CustomerReference')
        if not customer_reference:
            return tx

        _logger.info("MyFatoorah Payment Status: \n%s", response_data)

        domain = [
            ('provider_code', '=', 'myfatoorah'),
            ('reference', '=', customer_reference),
        ]
        if matched_provider:
            domain.append(('provider_id', '=', matched_provider.id))
        tx = self.sudo().search(domain, limit=1)
        if not tx:
            tx = self.sudo().search([
                ('provider_code', '=', 'myfatoorah'),
                ('reference', '=', customer_reference),
            ], limit=1)
        notification_data.update({
            'invoice_status': data.get('InvoiceStatus'),
            'payment_status': payment_status,
            'reference': customer_reference,
        })
        return tx
    
    def _get_specific_rendering_values(self, processing_values):
        res = super()._get_specific_rendering_values(processing_values)
        if self.provider_code != 'myfatoorah':
            return res
        api_key = self.provider_id.myfatoorah_token
        api_url = "{}/v2/SendPayment".format(self.provider_id._myfatoorah_get_api_url())
        payload = self._prepare_myfatoorah_invoice_link_payload(processing_values)
        #Log MyFatoorah Payload
        _logger.info("Myfatoorah Payload is :\n%s", payload)
        headers = {"Content-Type": "application/json", "Authorization": "Bearer " + api_key}
        response = requests.post(api_url, data=json.dumps(payload), headers=headers)
        _logger.info("Myfatoorah Response is :\n%s", response)
        url = "https://portal.myfatoorah.com/Files/API/mf-config.json"
        mf_countries = requests.get(url).json()
        _logger.info("mf_countries: \n%s", mf_countries)
        invoice_url = '#'
        if response.status_code != 200:
            _logger.info("Failed on generating invoice with error:\n%s", response.json())
        if response.status_code == 200:
            response_data = response.json()
            self.provider_reference = response_data["Data"]["InvoiceId"]
            # self._set_pending("myfatoorah transaction pending invoice payment.")
            invoice_url = response_data["Data"]["InvoiceURL"]
        return {
            'invoice_link': invoice_url,
        }  

    def _process_notification_data(self, notification_data):
        super()._process_notification_data(notification_data)
        tx = self.search([
            ('provider_code', '=', 'myfatoorah'),
            ('reference', '=', notification_data['reference']),
        ])
        _logger.info("notification tx: \n%s", tx)
        if self.provider_code != 'myfatoorah':
            return
        else:
            if notification_data['invoice_status'] == 'Paid':
                self._set_done()
                order = tx.sale_order_ids
                _logger.info("Order ids: \n%s", order)
                order.action_confirm()
            else:
                if notification_data['invoice_status'] == 'Pending':
                    if notification_data['payment_status'] == 'Failed':
                        self._set_error(
                            "Myfatoorah: " + _("received invalid transaction status: %s",
                                               notification_data['payment_status']))
                    else:
                        self._set_pending()
                else:
                    self._set_pending()

    def _prepare_myfatoorah_invoice_link_payload(self, processing_values):
        odoo_base_url = self.env['ir.config_parameter'].get_param('web.base.url')
        language = 'ar' if self.partner_lang == 'ar_001' or self.partner_lang == 'ar_SY' else 'en'
        payload = {
            # required fields
            "CustomerName": self.partner_name,
            "InvoiceValue": processing_values['amount'],
            "NotificationOption": "LNK",
            # optional fields
            "CustomerEmail": 'lucille.pearlku@gmail.com',
            "CustomerAddress": {
                "Block": "string",
                "Street": "string",
                "HouseBuildingNo": "string",
                "Address": self.partner_address,
                "AddressInstructions": self.partner_city
            },
            "CustomerReference": processing_values['reference'],
            "CallBackUrl": f"{odoo_base_url}/invoice_link/myfatoorah/process",
            "ErrorUrl": f"{odoo_base_url}/invoice_link/myfatoorah/process",
            "DisplayCurrencyIso": self.currency_id.name if self.currency_id.name else 'KWD',
            "Language": language
            # "MobileCountryCode": self,
            # "CustomerMobile": "12345678",  # Mandatory if the NotificationOption = SMS or ALL
        }

        #invoice_items = []
        #for order in self.sale_order_ids:
        #    for line in order.order_line:
        #        invoice_items.append({
        #            "ItemName": line.name,
        #            "Quantity": int(line.product_uom_qty),
        #            "UnitPrice": self.get_decimal_points(line.price_unit, self.currency_id.name)
        #        })
        #payload.update({
        #    "InvoiceItems": invoice_items
        #})
        return payload
