/** @odoo-module **/

import { Component, useRef, EventBus, onWillStart, useSubEnv, useState } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";

export class PaymentLinkInvoice extends Component {
    static template = "property_payment_link.tenancy_payment_invoice_line";

    setup(){
        super.setup();

        // Parse props if passed as JSON string (from t-att-props="json.dumps(...)")
        let props = this.props;
        if (typeof props === 'string') {
            try {
                props = JSON.parse(props);
            } catch (e) {
                console.error("PaymentLinkInvoice: Failed to parse props:", e);
                props = { tenancy_lines: {}, flexible_payment: false };
            }
        }
        if (typeof props.tenancy_lines === 'string') {
            try {
                props.tenancy_lines = JSON.parse(props.tenancy_lines);
            } catch (e) {
                props.tenancy_lines = {};
            }
        }
        
        // Get payment flags from props
        this.flexiblePayment = props.flexible_payment || false;
        this.parsedProps = props;

        // Sort invoices by date (oldest first) for chronological selection
        this.sortedInvoiceIds = [];
        if (props.tenancy_lines) {
            // Create array of [rentScheduleId, date] pairs and sort by date
            const invoiceDates = Object.entries(props.tenancy_lines).map(([rentScheduleId, lines]) => {
                const dateStr = lines && lines.length > 0 ? lines[0].date : '';
                // Parse date string (format: YYYY-MM-DD)
                const date = dateStr ? new Date(dateStr) : new Date(0);
                return { rentScheduleId: parseInt(rentScheduleId), date: date };
            });
            
            // Sort by date (oldest first)
            invoiceDates.sort((a, b) => a.date - b.date);
            this.sortedInvoiceIds = invoiceDates.map(item => item.rentScheduleId);
        }
        
        // Initialize state - if flexible_payment is False, select all invoices
        let initialSelectedIds = [];
        let initialTotal = 0.00;
        
        if (!this.flexiblePayment && props.tenancy_lines) {
            initialSelectedIds = Object.keys(props.tenancy_lines || {}).map(id => parseInt(id));
            Object.entries(props.tenancy_lines || {}).forEach(([rentScheduleId, lines]) => {
                if (lines && lines.length > 0) {
                    const line = lines[0];
                    initialTotal += line.invoice_amount_residual || 0;
                }
            });
        }
        
        this.state = useState({
            totalInvoice: initialTotal,
            selectedRentScheduleIds: initialSelectedIds,
        });
        
        // Update hidden input and total display after component renders
        onWillStart(() => {
            if (!this.flexiblePayment && initialSelectedIds.length > 0) {
                // Use setTimeout to ensure DOM is ready
                setTimeout(() => {
                    const totalElement = document.getElementById('InvoiceTotal');
                    if (totalElement) {
                        totalElement.innerText = initialTotal;
                    }
                    
                    const hiddenInput = document.getElementById('selected_rent_schedule_ids');
                    if (hiddenInput) {
                        hiddenInput.value = JSON.stringify(initialSelectedIds);
                    }
                }, 50);
            }
        });
    }

    isSelected(rentScheduleId){
        return this.state.selectedRentScheduleIds.includes(rentScheduleId);
    }

    isCheckboxDisabled(rentScheduleId){
        // If not flexible payment, checkbox is disabled (all must be selected)
        if (!this.flexiblePayment) {
            return true;
        }
        
        const isSelected = this.isSelected(rentScheduleId);
        
        // If invoice is selected, check if it can be deselected
        if (isSelected) {
            return !this.canDeselectInvoice(rentScheduleId);
        }
        
        // If invoice is not selected, check if it can be selected
        return !this.canSelectInvoice(rentScheduleId);
    }

    canSelectInvoice(rentScheduleId){
        // Check if invoice can be selected (all older invoices must be selected first)
        if (!this.flexiblePayment) {
            return true; // If not flexible, all invoices are auto-selected
        }
        
        // Find the index of this invoice in the sorted list
        const currentIndex = this.sortedInvoiceIds.indexOf(rentScheduleId);
        if (currentIndex === -1) {
            return false; // Invoice not found
        }
        
        // Check if all previous (older) invoices are selected
        for (let i = 0; i < currentIndex; i++) {
            const olderInvoiceId = this.sortedInvoiceIds[i];
            if (!this.state.selectedRentScheduleIds.includes(olderInvoiceId)) {
                return false; // There's an older invoice that's not selected
            }
        }
        
        return true; // All older invoices are selected, can select this one
    }

    canDeselectInvoice(rentScheduleId){
        // Check if invoice can be deselected (no newer invoices can be selected)
        if (!this.flexiblePayment) {
            return false; // If not flexible, cannot deselect
        }
        
        // Find the index of this invoice in the sorted list
        const currentIndex = this.sortedInvoiceIds.indexOf(rentScheduleId);
        if (currentIndex === -1) {
            return false; // Invoice not found
        }
        
        // Check if any newer invoices are selected
        for (let i = currentIndex + 1; i < this.sortedInvoiceIds.length; i++) {
            const newerInvoiceId = this.sortedInvoiceIds[i];
            if (this.state.selectedRentScheduleIds.includes(newerInvoiceId)) {
                return false; // There's a newer invoice that's selected, cannot deselect this one
            }
        }
        
        return true; // No newer invoices selected, can deselect this one
    }

    onCheckboxClick(ev){
        const rentScheduleId = parseInt(ev.target.getAttribute('data-schedule-id'));
        const lineData = this.parsedProps.tenancy_lines[rentScheduleId][0];
        this.addToTotal(ev, lineData);
    }

    addToTotal(ev, line){
        // If flexible_payment is False, prevent unchecking
        if (!this.flexiblePayment && !ev.target.checked) {
            ev.preventDefault();
            ev.target.checked = true;
            return;
        }
        
        // If flexible_payment is False, prevent any changes
        if (!this.flexiblePayment) {
            ev.preventDefault();
            ev.target.checked = true;
            return;
        }
        
        const rentScheduleId = line.rent_schedule_id;
        const isCurrentlySelected = this.state.selectedRentScheduleIds.includes(rentScheduleId);
        
        // Check the actual checkbox state after click
        const willBeChecked = ev.target.checked;
        
        // Prevent duplicate additions/removals
        if (willBeChecked && isCurrentlySelected) {
            // Already selected, don't add again
            ev.target.checked = true;
            return;
        }
        
        if (!willBeChecked && !isCurrentlySelected) {
            // Already unselected, don't remove again
            ev.target.checked = false;
            return;
        }
        
        // Enforce chronological selection rules for flexible payment
        if (this.flexiblePayment) {
            if (willBeChecked && !isCurrentlySelected) {
                // Trying to select: check if all older invoices are selected
                if (!this.canSelectInvoice(rentScheduleId)) {
                    ev.preventDefault();
                    ev.target.checked = false;
                    alert('Please select older invoices first. You must pay invoices in chronological order.');
                    return;
                }
            } else if (!willBeChecked && isCurrentlySelected) {
                // Trying to deselect: check if any newer invoices are selected
                if (!this.canDeselectInvoice(rentScheduleId)) {
                    ev.preventDefault();
                    ev.target.checked = true;
                    alert('Please deselect newer invoices first. You can only remove invoices in reverse chronological order.');
                    return;
                }
            }
        }
        
        // Update state based on checkbox action
        if (willBeChecked && !isCurrentlySelected) {
            // Adding: checkbox is checked and not in selected list
            this.state.totalInvoice = this.state.totalInvoice + line.invoice_amount_residual;
            // Create new array to trigger reactivity
            this.state.selectedRentScheduleIds = [...this.state.selectedRentScheduleIds, rentScheduleId];
        } else if (!willBeChecked && isCurrentlySelected) {
            // Removing: checkbox is unchecked and in selected list
            this.state.totalInvoice = this.state.totalInvoice - line.invoice_amount_residual;
            // Create new array without the removed item to trigger reactivity
            this.state.selectedRentScheduleIds = this.state.selectedRentScheduleIds.filter(id => id !== rentScheduleId);
        }
        
        // Update the total display (using setTimeout to ensure state is updated)
        setTimeout(() => {
            const totalElement = document.getElementById('InvoiceTotal');
            if (totalElement) {
                totalElement.innerText = this.state.totalInvoice.toFixed(2);
            }
            
            // Update the hidden input with selected IDs (for the payment form)
            const hiddenInput = document.getElementById('selected_rent_schedule_ids');
            if (hiddenInput) {
                hiddenInput.value = JSON.stringify(this.state.selectedRentScheduleIds);
                console.log("Updated selected rent schedule IDs:", this.state.selectedRentScheduleIds);
            }
        }, 0);
    }
}

registry.category('public_components').add("property_payment_link.tenancy_payment_invoice_line", PaymentLinkInvoice);
