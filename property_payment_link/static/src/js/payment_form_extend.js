/** @odoo-module **/

import publicWidget from '@web/legacy/js/public/public_widget';
import { patch } from "@web/core/utils/patch";

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
