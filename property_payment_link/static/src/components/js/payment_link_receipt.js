/** @odoo-module **/

import { Component, useRef, EventBus, useSubEnv, useState} from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";

export class PaymentLinkReceipt extends Component {
    static template = "property_payment_link.tenancy_payment_invoice_receipt";

    setup(){
        super.setup();
        this.model_invoice_name = useRef('model_invoice_name')
        this.model_tenancy_name = useRef('model_tenancy_name')
        this.model_invoice_due_date = useRef('model_invoice_due_date')
        this.model_invoice_amount = useRef('model_invoice_amount')
        this.model_customer_name = useRef('model_customer_name')
        this.model_unit = useRef('model_unit')
        this.model_tenant_date = useRef('model_tenant_date')
        this.model_paid_amount = useRef('model_paid_amount')
        this.model_residual_amount = useRef('model_residual_amount')
        this.model_payment_date = useRef('model_payment_date')
        this.model_payment_transaction_id = false
        this.model_payment_method = useRef('model_payment_method')
        this.model_reference_number = useRef('model_reference_number')
        this.model_unit_serial_number = useRef('model_unit_serial_number')
        this.model_paid_amount_words = useRef('model_paid_amount_words')
        
        // Debug: Log props to console
        console.log("PaymentLinkReceipt - Props received:", this.props);
        console.log("PaymentLinkReceipt - tenancy_lines:", this.props.tenancy_lines);
        console.log("PaymentLinkReceipt - tenancy_lines keys:", this.props.tenancy_lines ? Object.keys(this.props.tenancy_lines) : 'null');
        
        // Ensure props are properly parsed (in case they come as JSON string)
        if (typeof this.props.tenancy_lines === 'string') {
            try {
                this.props.tenancy_lines = JSON.parse(this.props.tenancy_lines);
            } catch (e) {
                console.error("Failed to parse tenancy_lines:", e);
            }
        }
    }

    onViewPaymentClick(rentScheduleId){
        this.fillPaymentViewModel(rentScheduleId);
    }

    fillPaymentViewModel(rentScheduleId){
        const lineData = this.props.tenancy_lines[rentScheduleId][0];
        this.model_invoice_name.el.innerText = lineData.invoice_name
        this.model_tenancy_name.el.innerText = lineData.tenancy_name
        this.model_invoice_due_date.el.innerText = lineData.invoice_due_date
        this.model_invoice_amount.el.innerText = lineData.invoice_amount
        this.model_customer_name.el.innerText = lineData.customer_name
        this.model_unit.el.innerText = lineData.unit
        this.model_tenant_date.el.innerText = lineData.date
        this.model_paid_amount.el.innerText = lineData.paid_amount
        this.model_residual_amount.el.innerText = lineData.residual_amount
        this.model_payment_date.el.innerText = lineData.payment_date
        this.model_payment_method.el.innerText = lineData.payment_method
        this.model_reference_number.el.innerText = lineData.reference_number
        this.model_unit_serial_number.el.innerText = lineData.unit_serial_number
        this.model_paid_amount_words.el.innerText = lineData.paid_amount_words
    }
}

registry.category('public_components').add("property_payment_link.tenancy_payment_invoice_receipt", PaymentLinkReceipt);

