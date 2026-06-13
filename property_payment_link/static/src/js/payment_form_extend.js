/** @odoo-module **/

import publicWidget from '@web/legacy/js/public/public_widget';
import { patch } from "@web/core/utils/patch";

function getPartialPaymentAmount() {
    const allowPartial = document.getElementById('allow_partial_payment_flag');
    if (!allowPartial) {
        return null;
    }
    const hidden = document.getElementById('partial_payment_amount');
    const input = document.getElementById('partial_payment_amount_input');
    const raw = (hidden && hidden.value) || (input && input.value) || '';
    const amount = parseFloat(raw);
    return Number.isFinite(amount) && amount > 0 ? amount : null;
}

function syncPartialAmountToPaymentForm(paymentFormWidget) {
    const amount = getPartialPaymentAmount();
    if (amount === null) {
        return;
    }
    const hidden = document.getElementById('partial_payment_amount');
    if (hidden) {
        hidden.value = String(amount);
    }
    const form = document.getElementById('o_payment_form');
    if (form) {
        form.dataset.amount = String(amount);
    }
    if (paymentFormWidget && paymentFormWidget.paymentContext) {
        paymentFormWidget.paymentContext.amount = String(amount);
    }
}

function isTenancyPaymentLinkPage() {
    const form = document.getElementById('o_payment_form');
    const route = form && form.dataset ? form.dataset.transactionRoute : '';
    return (
        (route && route.includes('/tenancy/transaction/'))
        || window.location.href.includes('tenancy_payment_link')
    );
}

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
    _onPayClick: function (ev) {
        const allowPartial = document.getElementById('allow_partial_payment_flag');
        const partialAmountInput = document.getElementById('partial_payment_amount_input');
        const partialAmountHidden = document.getElementById('partial_payment_amount');
        if (allowPartial && partialAmountInput) {
            const amount = parseFloat(partialAmountInput.value);
            if (!Number.isFinite(amount) || amount <= 0) {
                ev.preventDefault();
                return;
            }
            if (partialAmountHidden) {
                partialAmountHidden.value = String(amount);
            }
            syncPartialAmountToPaymentForm();
        }
        const rentInput = document.getElementById('selected_rent_schedule_ids');
        const serviceInput = document.getElementById('selected_service_rent_ids');
        const depositInput = document.getElementById('selected_deposit_invoice_ids');
        let rentIds = [];
        let serviceIds = [];
        let depositIds = [];
        try {
            if (rentInput && rentInput.value) {
                rentIds = JSON.parse(rentInput.value);
            }
            if (serviceInput && serviceInput.value) {
                serviceIds = JSON.parse(serviceInput.value);
            }
            if (depositInput && depositInput.value) {
                depositIds = JSON.parse(depositInput.value);
            }
        } catch (e) {
            rentIds = [];
            serviceIds = [];
            depositIds = [];
        }
        const payBtn = document.getElementById('payment_link_pay_btn');
        if (
            payBtn
            && (payBtn.classList.contains('disabled')
                || payBtn.getAttribute('aria-disabled') === 'true')
        ) {
            ev.preventDefault();
            return;
        }
        if (
            !allowPartial
            && !rentIds.length
            && !serviceIds.length
            && !depositIds.length
        ) {
            ev.preventDefault();
            return;
        }
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
        const depositInvoiceId = parseInt(ev.currentTarget.getAttribute('data-deposit-invoice-id'), 10);
        const line = this.receiptData.find(function (l) {
            if (depositInvoiceId && l.deposit_invoice_id === depositInvoiceId) {
                return true;
            }
            if (scheduleId && l.rent_schedule_id === scheduleId) {
                return true;
            }
            return false;
        });
        if (!line) return;
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

const PaymentFormWidget = publicWidget.registry.PaymentForm;

if (PaymentFormWidget) {
    patch(PaymentFormWidget.prototype, {
        /**
         * Defer MyFatoorah auto-expand on tenancy payment pages until the modal opens.
         * @override
         */
        async start() {
            this.paymentContext = {};
            Object.assign(this.paymentContext, this.el.dataset);

            await publicWidget.Widget.prototype.start.call(this);

            const deferExpand = isTenancyPaymentLinkPage();
            const checkedRadio = document.querySelector('input[name="o_payment_radio"]:checked');
            if (checkedRadio && !deferExpand) {
                await this._expandInlineForm(checkedRadio);
                this._enableButton(false);
            } else if (!checkedRadio) {
                this._setPaymentFlow();
            }

            this.$('[data-bs-toggle="tooltip"]').tooltip();

            const modal = document.getElementById('payment_method');
            if (modal && deferExpand) {
                modal.addEventListener('shown.bs.modal', () => this._onTenancyPaymentModalShown());
            }
        },

        async _onTenancyPaymentModalShown() {
            syncPartialAmountToPaymentForm(this);
            if (typeof window.resetMyFatoorahFormCache === 'function') {
                window.resetMyFatoorahFormCache();
            }
            const checkedRadio = this.el.querySelector('input[name="o_payment_radio"]:checked');
            if (checkedRadio) {
                this._disableButton();
                await this._expandInlineForm(checkedRadio);
                this._enableButton(false);
            }
        },

        /**
         * @override
         * Pass tenancy invoice selection and partial amount to the transaction route.
         */
        _prepareTransactionRouteParams() {
            const params = super._prepareTransactionRouteParams(...arguments);

            if (
                this.paymentContext
                && this.paymentContext['transactionRoute']
                && this.paymentContext['transactionRoute'].includes('/tenancy/transaction/')
            ) {
                const rentInput = document.getElementById('selected_rent_schedule_ids');
                if (rentInput && rentInput.value && rentInput.value !== '[]') {
                    params.selected_rent_schedule_ids = rentInput.value;
                }
                const serviceInput = document.getElementById('selected_service_rent_ids');
                if (serviceInput && serviceInput.value && serviceInput.value !== '[]') {
                    params.selected_service_rent_ids = serviceInput.value;
                }
                const depositInput = document.getElementById('selected_deposit_invoice_ids');
                if (depositInput && depositInput.value && depositInput.value !== '[]') {
                    params.selected_deposit_invoice_ids = depositInput.value;
                }

                const partialAmount = getPartialPaymentAmount();
                if (partialAmount !== null) {
                    params.partial_payment_amount = String(partialAmount);
                    params.amount = partialAmount;
                    this.paymentContext.amount = String(partialAmount);
                    const form = document.getElementById('o_payment_form');
                    if (form) {
                        form.dataset.amount = String(partialAmount);
                    }
                }
            }

            return params;
        },
    });
}

export default PaymentFormWidget;
