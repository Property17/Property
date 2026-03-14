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

// Reset MyFatoorah form cache when Pay is clicked so modal uses current invoice selection
publicWidget.registry.PaymentLinkPayButton = publicWidget.Widget.extend({
    selector: '.payment-link-detail-container',
    events: {
        'click a[data-bs-target="#payment_method"]': '_onPayClick',
    },
    _onPayClick: function () {
        if (typeof window.resetMyFatoorahFormCache === 'function') {
            window.resetMyFatoorahFormCache();
        }
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
        // Map modal element ids to data keys (aligned with PDF Rent Collection Receipt)
        const mapping = [
            ['modal_receipt_number', line.receipt_number || line.invoice_name],
            ['modal_tenancy_name', line.tenancy_name],
            ['modal_invoice_due_date', line.invoice_due_date],
            ['modal_unit', line.unit],
            ['modal_unit_serial_number', line.unit_serial_number],
            ['modal_customer_name', line.customer_name],
            ['modal_period_formatted', line.period_formatted || line.date],
            ['modal_paid_amount_words', line.paid_amount_words],
            ['modal_rental_value', line.invoice_amount_formatted || line.invoice_amount],
            ['modal_paid_amount', line.paid_amount_formatted || line.paid_amount],
            ['modal_paid_amount_words_2', line.paid_amount_words],
            ['modal_residual_amount', line.residual_amount_formatted != null ? line.residual_amount_formatted : (line.residual_amount != null ? String(line.residual_amount) : '0.00')],
            ['modal_payment_date', line.payment_date],
            ['modal_payment_method', line.payment_method],
            ['modal_payment_details', line.payment_details || line.reference_number],
            ['modal_collector_name', line.collector_name],
        ];
        mapping.forEach(function (pair) {
            const el = document.getElementById(pair[0]);
            if (el) el.textContent = pair[1] != null && pair[1] !== '' ? String(pair[1]) : '';
        });
    },
});

// Get the PaymentForm widget from the registry
const PaymentFormWidget = publicWidget.registry.PaymentForm;

// Patch the PaymentForm to include selected rent schedule IDs in transaction params
if (PaymentFormWidget) {
    patch(PaymentFormWidget.prototype, {
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
