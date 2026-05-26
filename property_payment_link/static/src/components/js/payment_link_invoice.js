/** @odoo-module **/

import { Component, onWillStart, useState } from "@odoo/owl";
import { registry } from "@web/core/registry";

export class PaymentLinkInvoice extends Component {
    static template = "property_payment_link.tenancy_payment_invoice_line";

    setup() {
        super.setup();

        let props = this.props;
        if (typeof props === "string") {
            try {
                props = JSON.parse(props);
            } catch (e) {
                console.error("PaymentLinkInvoice: Failed to parse props:", e);
                props = { tenancy_lines: {}, flexible_payment: false };
            }
        }
        if (typeof props.tenancy_lines === "string") {
            try {
                props.tenancy_lines = JSON.parse(props.tenancy_lines);
            } catch (e) {
                props.tenancy_lines = {};
            }
        }

        this.flexiblePayment = props.flexible_payment || false;
        this.parsedProps = props;

        const lineEntries = Object.entries(props.tenancy_lines || {}).map(
            ([lineKey, lines]) => {
                const line = lines && lines.length > 0 ? lines[0] : {};
                const dateStr = line.date || "";
                const date = dateStr ? new Date(dateStr) : new Date(0);
                return { lineKey, line, date };
            }
        );
        lineEntries.sort((a, b) => a.date - b.date);
        this.sortedLineKeys = lineEntries.map((e) => e.lineKey);

        let initialSelectedKeys = [];
        let initialTotal = 0.0;

        if (!this.flexiblePayment && props.tenancy_lines) {
            initialSelectedKeys = [...this.sortedLineKeys];
            for (const lineKey of initialSelectedKeys) {
                const lines = props.tenancy_lines[lineKey];
                if (lines && lines[0]) {
                    initialTotal += lines[0].invoice_amount_residual || 0;
                }
            }
        }

        this.state = useState({
            totalInvoice: initialTotal,
            selectedLineKeys: initialSelectedKeys,
        });

        onWillStart(() => {
            setTimeout(() => this._syncHiddenInputs(), 50);
        });
    }

    _updatePayButton() {
        const btn = document.getElementById("payment_link_pay_btn");
        if (!btn) {
            return;
        }
        const hasSelection = this.state.selectedLineKeys.length > 0;
        const disabled = this.flexiblePayment && !hasSelection;
        if (disabled) {
            btn.classList.remove("btn-primary");
            btn.classList.add("btn-secondary", "disabled");
            btn.setAttribute("aria-disabled", "true");
            btn.style.pointerEvents = "none";
            btn.style.opacity = "0.65";
            btn.removeAttribute("data-bs-toggle");
            btn.removeAttribute("data-bs-target");
        } else {
            btn.classList.add("btn-primary");
            btn.classList.remove("btn-secondary", "disabled");
            btn.removeAttribute("aria-disabled");
            btn.style.pointerEvents = "";
            btn.style.opacity = "";
            btn.setAttribute("data-bs-toggle", "modal");
            btn.setAttribute("data-bs-target", "#payment_method");
        }
    }

    _syncHiddenInputs() {
        const totalElement = document.getElementById("InvoiceTotal");
        if (totalElement) {
            totalElement.innerText = this.state.totalInvoice.toFixed(2);
        }
        this._updatePayButton();
        const rentIds = [];
        const serviceIds = [];
        const depositIds = [];
        for (const lineKey of this.state.selectedLineKeys) {
            const line = this.parsedProps.tenancy_lines[lineKey]?.[0];
            if (!line) {
                continue;
            }
            if (line.line_type === "deposit" && line.deposit_invoice_id) {
                depositIds.push(line.deposit_invoice_id);
            } else if (line.line_type === "service" && line.service_rent_id) {
                serviceIds.push(line.service_rent_id);
            } else if (line.rent_schedule_id) {
                rentIds.push(line.rent_schedule_id);
            }
        }
        const rentInput = document.getElementById("selected_rent_schedule_ids");
        const serviceInput = document.getElementById("selected_service_rent_ids");
        const depositInput = document.getElementById("selected_deposit_invoice_ids");
        if (rentInput) {
            rentInput.value = JSON.stringify(rentIds);
        }
        if (serviceInput) {
            serviceInput.value = JSON.stringify(serviceIds);
        }
        if (depositInput) {
            depositInput.value = JSON.stringify(depositIds);
        }
    }

    isSelected(lineKey) {
        return this.state.selectedLineKeys.includes(lineKey);
    }

    isCheckboxDisabled(lineKey) {
        if (!this.flexiblePayment) {
            return true;
        }
        const isSelected = this.isSelected(lineKey);
        if (isSelected) {
            return !this.canDeselectLine(lineKey);
        }
        return !this.canSelectLine(lineKey);
    }

    canSelectLine(lineKey) {
        if (!this.flexiblePayment) {
            return true;
        }
        const currentIndex = this.sortedLineKeys.indexOf(lineKey);
        if (currentIndex === -1) {
            return false;
        }
        for (let i = 0; i < currentIndex; i++) {
            if (!this.state.selectedLineKeys.includes(this.sortedLineKeys[i])) {
                return false;
            }
        }
        return true;
    }

    canDeselectLine(lineKey) {
        if (!this.flexiblePayment) {
            return false;
        }
        const currentIndex = this.sortedLineKeys.indexOf(lineKey);
        if (currentIndex === -1) {
            return false;
        }
        for (let i = currentIndex + 1; i < this.sortedLineKeys.length; i++) {
            if (this.state.selectedLineKeys.includes(this.sortedLineKeys[i])) {
                return false;
            }
        }
        return true;
    }

    onCheckboxClick(ev) {
        const lineKey = ev.target.getAttribute("data-line-key");
        const lineData = this.parsedProps.tenancy_lines[lineKey]?.[0];
        if (!lineData) {
            return;
        }
        this.addToTotal(ev, lineKey, lineData);
    }

    addToTotal(ev, lineKey, line) {
        if (!this.flexiblePayment && !ev.target.checked) {
            ev.preventDefault();
            ev.target.checked = true;
            return;
        }
        if (!this.flexiblePayment) {
            ev.preventDefault();
            ev.target.checked = true;
            return;
        }

        const isCurrentlySelected = this.state.selectedLineKeys.includes(lineKey);
        const willBeChecked = ev.target.checked;

        if (willBeChecked && isCurrentlySelected) {
            ev.target.checked = true;
            return;
        }
        if (!willBeChecked && !isCurrentlySelected) {
            ev.target.checked = false;
            return;
        }

        if (this.flexiblePayment) {
            if (willBeChecked && !isCurrentlySelected && !this.canSelectLine(lineKey)) {
                ev.preventDefault();
                ev.target.checked = false;
                alert(
                    "Please select older invoices first. You must pay invoices in chronological order."
                );
                return;
            }
            if (!willBeChecked && isCurrentlySelected && !this.canDeselectLine(lineKey)) {
                ev.preventDefault();
                ev.target.checked = true;
                alert(
                    "Please deselect newer invoices first. You can only remove invoices in reverse chronological order."
                );
                return;
            }
        }

        if (willBeChecked && !isCurrentlySelected) {
            this.state.totalInvoice += line.invoice_amount_residual || 0;
            this.state.selectedLineKeys = [...this.state.selectedLineKeys, lineKey];
        } else if (!willBeChecked && isCurrentlySelected) {
            this.state.totalInvoice -= line.invoice_amount_residual || 0;
            this.state.selectedLineKeys = this.state.selectedLineKeys.filter(
                (k) => k !== lineKey
            );
        }

        setTimeout(() => this._syncHiddenInputs(), 0);
    }
}

registry.category("public_components").add(
    "property_payment_link.tenancy_payment_invoice_line",
    PaymentLinkInvoice
);
