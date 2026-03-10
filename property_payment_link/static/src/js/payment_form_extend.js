/** @odoo-module **/

import publicWidget from '@web/legacy/js/public/public_widget';
import { patch } from "@web/core/utils/patch";

// Tenant/Property info - inject via JS (bypasses theme/CSS that may hide server-rendered content)
publicWidget.registry.PaymentLinkTenantInfo = publicWidget.Widget.extend({
    selector: '.payment-link-detail-container',

    start: function () {
        const container = document.getElementById('payment-link-tenant-info');
        if (container) {
            const raw = container.getAttribute('data-tenant-info');
            if (raw) {
                try {
                    const info = JSON.parse(raw);
                    const rows = [
                        ['Property Manager', info.property_manager],
                        ['Tenant', info.tenant],
                        ['Tenancy', info.tenancy],
                        ['Phone', info.phone],
                        ['Property', info.property],
                        ['Email', info.email],
                    ];
                    let html = '';
                    rows.forEach(function (r) {
                        html += '<div class="info-row" style="display:flex;flex-wrap:wrap;padding:0.5rem 0;border-bottom:1px solid #dee2e6;">';
                        html += '<span class="info-label" style="font-weight:600;flex:0 0 110px;font-size:0.85rem;">' + (r[0] || '') + '</span>';
                        html += '<span class="info-value" style="flex:1 1 auto;word-break:break-word;font-size:0.9rem;">' + (r[1] || '') + '</span>';
                        html += '</div>';
                    });
                    container.innerHTML = html;
                } catch (e) {
                    console.warn('PaymentLinkTenantInfo: parse error', e);
                }
            }
        }
        return this._super.apply(this, arguments);
    },
});

// Payment Receipt View modal - populate when View link clicked (server-rendered, no OWL duplication)
publicWidget.registry.PaymentReceiptView = publicWidget.Widget.extend({
    selector: '#payment-receipt-section',
    events: {
        'click .payment-receipt-view-btn': '_onViewClick',
    },

    start: function () {
        const section = this.el;
        this.receiptData = [];
        if (section) {
            const raw = section.getAttribute('data-receipt-list');
            if (raw) {
                try {
                    this.receiptData = JSON.parse(raw);
                } catch (e) {
                    console.warn('Payment receipt data parse error:', e);
                }
            }
        }
        return this._super.apply(this, arguments);
    },

    _onViewClick: function (ev) {
        ev.preventDefault();
        const scheduleId = parseInt(ev.currentTarget.getAttribute('data-schedule-id'), 10);
        const line = this.receiptData.find(function (l) { return l.rent_schedule_id === scheduleId; });
        if (!line) return;
        const ids = ['modal_tenancy_name', 'modal_invoice_name', 'modal_invoice_due_date', 'modal_invoice_amount',
            'modal_customer_name', 'modal_unit', 'modal_tenant_date', 'modal_unit_serial_number',
            'modal_paid_amount', 'modal_paid_amount_words', 'modal_residual_amount', 'modal_payment_date',
            'modal_reference_number', 'modal_payment_method'];
        const keys = ['tenancy_name', 'invoice_name', 'invoice_due_date', 'invoice_amount',
            'customer_name', 'unit', 'date', 'unit_serial_number',
            'paid_amount', 'paid_amount_words', 'residual_amount', 'payment_date',
            'reference_number', 'payment_method'];
        for (let i = 0; i < ids.length; i++) {
            const el = document.getElementById(ids[i]);
            if (el) el.textContent = line[keys[i]] || '';
        }
    },
});

// Get the PaymentForm widget from the registry
const PaymentFormWidget = publicWidget.registry.PaymentForm;

// Patch the PaymentForm for tenancy payment links
if (PaymentFormWidget) {
    patch(PaymentFormWidget.prototype, {
        async start() {
            var isTenancyPage = typeof window !== 'undefined' && window.location.href.indexOf('tenancy_payment_link') !== -1;
            if (isTenancyPage) {
                var r = document.querySelector('input[name="o_payment_radio"]:checked');
                if (r) r.checked = false;
            }
            await this._super.apply(this, arguments);
        },
        /**
         * @override
         * Add selected_rent_schedule_ids to the transaction route params
         */
        _prepareTransactionRouteParams() {
            // Call the original method
            const params = super._prepareTransactionRouteParams(...arguments);
            
            // Check if this is a tenancy transaction (by checking the route)
            if (this.paymentContext && this.paymentContext['transactionRoute'] && 
                this.paymentContext['transactionRoute'].includes('/tenancy/transaction/')) {
                
                // Get selected rent schedule IDs from hidden input
                const hiddenInput = document.getElementById('selected_rent_schedule_ids');
                if (hiddenInput && hiddenInput.value && hiddenInput.value !== '[]') {
                    params.selected_rent_schedule_ids = hiddenInput.value;
                    console.log("PaymentForm patch: Added selected_rent_schedule_ids:", hiddenInput.value);
                } else {
                    console.log("PaymentForm patch: No selected_rent_schedule_ids found");
                }
            }
            
            return params;
        },
    });
}

export default PaymentFormWidget;
