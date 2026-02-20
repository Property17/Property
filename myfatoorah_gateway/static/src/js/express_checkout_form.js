/** @odoo-module */

import publicWidget from '@web/legacy/js/public/public_widget';
import { debounce } from '@web/core/utils/timing';
import { _t } from "@web/core/l10n/translation";
import { jsonrpc, RPCError } from "@web/core/network/rpc_service";

import { paymentExpressCheckoutForm } from '@payment/js/express_checkout_form';

paymentExpressCheckoutForm.include({ 
    events: Object.assign({}, publicWidget.Widget.prototype.events, {
        'click button[name="o_payment_submit_button"]': '_initiateExpressPayment',
    }),

    start: async function () {
        await this._super(...arguments);
        var is_google_pay_enabled = false;
        var is_apple_pay_enabled = false;
        var is_card_view_enabled = false;
        var invoice_id = null;
        var tenancy_id = null;
        var currentURL = window.location.href;
        if (currentURL.includes("invoices")) {
            var match = currentURL.match(/invoices\/(\d+)/);
            if (match) invoice_id = match[1];
        } else if (currentURL.includes("tenancy_payment_link")) {
            var tenancyMatch = currentURL.match(/tenancy_payment_link\/tenant_partner\/(\d+)/);
            if (tenancyMatch) tenancy_id = parseInt(tenancyMatch[1], 10);
        }

        var initiateParams = {};
        if (invoice_id) initiateParams.invoice_id = invoice_id;
        if (tenancy_id) {
            initiateParams.tenancy_id = tenancy_id;
            var hiddenInput = document.getElementById('selected_rent_schedule_ids');
            if (hiddenInput && hiddenInput.value && hiddenInput.value !== '[]') {
                try {
                    initiateParams.selected_rent_schedule_ids = JSON.parse(hiddenInput.value);
                } catch (e) {
                    initiateParams.selected_rent_schedule_ids = hiddenInput.value;
                }
            }
        }

        jsonrpc('/payment/myfatoorah/initiate-payment', initiateParams).then((initiatePaymentResult) => 
        {
            if (!initiatePaymentResult.success){
                this._displayErrorDialog(_t("Validation Error"), initiatePaymentResult.message);
                this._enableButton();
                return;
            }
            const country_code = initiatePaymentResult.country_code;
            const state = initiatePaymentResult.state;
            const checkout_gateways = initiatePaymentResult.checkout_gateways;
            const cards_payment_methods = checkout_gateways?.cards;

            _prepareGooglePay(country_code, state);
            _prepareApplePay(country_code, state);
            _prepareForm(country_code, state);
            _prepareCards(cards_payment_methods);
            
            if(checkout_gateways.gp){
                is_google_pay_enabled = true;
            }
    
            if(checkout_gateways.ap && window.ApplePaySession){
                is_apple_pay_enabled = true;
            }
    
            if(checkout_gateways.form.length > 0){
                is_card_view_enabled = true;
            }
    
            if(!is_google_pay_enabled){
                document.getElementById('mf-sectionGP')?.remove();
                if(!is_apple_pay_enabled && window.ApplePaySession){
                    document.getElementById('mf-or-cardsDivider')?.remove();
                }
            }
    
            if(!is_apple_pay_enabled){
                document.getElementById('mf-sectionAP')?.remove();
            }
    
            if(!is_card_view_enabled){
                document.getElementById('mf-cardView')?.remove();
            }    
              
            if(cards_payment_methods.length === 0){
                document.getElementById('mf-sectionCard')?.remove();
                if(!is_google_pay_enabled && !is_apple_pay_enabled && window.ApplePaySession){
                    document.getElementById('mf-or-formDivider')?.remove();
                }
            }
    
            if(!is_google_pay_enabled 
                && (!is_apple_pay_enabled) 
                && !is_card_view_enabled
                && cards_payment_methods.length === 0){
                document.getElementById('mf-paymentGateways')?.remove();
                document.getElementById('mf-noPaymentGateways').style.display = 'block';
            }

            jsonrpc('/payment/myfatoorah/initiate-session', {}).then((initiateSessionResponse) => 
            {
                var sessionId = initiateSessionResponse?.response.Data?.SessionId;

                // Load Google Pay
                if(is_google_pay_enabled){
                    //_loadGooglePay(checkout_gateways.gp.GatewayTotalAmount, country_code, checkout_gateways.gp.PaymentCurrencyIso, sessionId)
                    var gpConfig = {
                        sessionId: sessionId,
                        amount: `${checkout_gateways.gp.GatewayTotalAmount}`,
                        currencyCode: checkout_gateways.gp.PaymentCurrencyIso,
                        countryCode: country_code,
                        cardViewId: "mf-gp-element",
                        callback: this._onClickPayment.bind(this),
                        style: { 
                            frameHeight: 51,
                            button: {
                                height: "40px",
                                text: "Pay", // Accepted texts: ["book", "buy", "checkout", "donate", "order", "pay", "plain", "subscribe"]
                                borderRadius: "8px",
                                color: "black", // Accepted colors: ["black", "white", "default"]
                                language: "en"
                            }
                        }
                    };
                
                    myFatoorahGP.init(gpConfig);
                    window.addEventListener("message", myFatoorahGP.recievedMessage);
                }

                // Load Apple pay
                if(is_apple_pay_enabled){
                    var apConfig = {
                    sessionId: sessionId,
                    countryCode: country_code,
                    currencyCode: checkout_gateways.ap.PaymentCurrencyIso,
                    amount: `${checkout_gateways.ap.GatewayTotalAmount}`,
                    cardViewId: "mf-ap-element",
                    callback: this._onClickPayment.bind(this),
                    };
                    myFatoorahAP.init(apConfig);
                    window.addEventListener("message", myFatoorahAP.recievedMessage);
                }

                if(is_card_view_enabled){
                    var config = {
                        countryCode: country_code,
                        sessionId: sessionId,
                        cardViewId: "mf-form-element",
                        style: {
                            direction: "ltr",
                            error:
                            {
                                borderRadius: "0px"
                            },
                            input: {
                                inputMargin: "-1px",
                                borderRadius: "0px"
                            }
                        },
                    };
                    myFatoorah.init(config);
                    window.addEventListener("message", myFatoorah.recievedMessage);
                }
                is_form_prepared = true;
                return;
            });
        })
        .catch(error => {
            if (error instanceof RPCError) {
                this._displayErrorDialog(_t("Payment processing failed"), "Ops! Something went wrong on initiating MyFatoorah Payment, Please contact admin");
                this._enableButton?.(); // This method doesn't exists in Express Checkout form.
            } else {
                return Promise.reject(error);
            }
        });


        document.querySelector('[name="o_payment_submit_button"]')?.removeAttribute('disabled');
        this._initiateMyFatoorahExpressPayment = debounce(this._initiateExpressPayment, 500, true);
    },

    _onClickPayment: function(response) {
        var button = document.querySelector("button[name='o_payment_submit_button']");
        if (button) {
            this.myFatoorahSessionId = response.sessionId;
            button.click();
        } else {
            console.error('Button not found');
        }
    },

    _displayErrorDialog: function(title, message) {
        // Implement the logic to show the error dialog.
        // For simplicity, let's use an alert.
        alert(`${title}: ${message}`);

        // Alternatively, you can integrate with Odoo's dialog system if available.
    },

    async _initiateExpressPayment(ev) {
        ev.stopPropagation();
        ev.preventDefault();

        const providerId = ev.target.parentElement.dataset.providerId;

        console.log(providerId);

        if (myFatoorahPaymentMethodId !== undefined) { /* Cards */
            return this._myfatoorahExecutePayment(null, myFatoorahPaymentMethodId);
        } else if (this.myFatoorahSessionId !== undefined) { /* Google and Apple pay */
            return this._myfatoorahExecutePayment(this.myFatoorahSessionId);
        } else { /* Card view */
            myFatoorah.submit()
                .then((response) => {
                    var sessionId = response.sessionId;
                    return this._myfatoorahExecutePayment(sessionId);
                }).catch((error) => {
                    this._displayErrorDialog(_t("Payment processing failed"), error);
                    this._enableButton?.();
                });
        }
    },

    _myfatoorahExecutePayment: function(session_id = null, payment_method_id = null){
        if(session_id == null && payment_method_id == null){
            this._displayErrorDialog(_t("Missing Data"), "Session and payment method cannot be null");
            this._enableButton();
            return;
        }

        return jsonrpc('/payment/myfatoorah/execute-payment', {
            SessionId: session_id,
            PaymentMethodId: payment_method_id,
        }).then((data) => {
            if (!data.success){
                this._displayErrorDialog(_t("Validation Error"), data.message);
                this._enableButton();
                return;
            }
            var mf_response = JSON.parse(data.data)
            if (mf_response.IsSuccess) {
                var paymentUrl = mf_response.Data.PaymentURL;
                window.location = paymentUrl;
            } else {
                var errorMessage = '';
                if (mf_response.ValidationErrors && mf_response.ValidationErrors.length > 0) {
                    mf_response.ValidationErrors.forEach((error) => {
                        errorMessage = error.Error; // Print each error message
                    });
                }
                this._displayErrorDialog(_t("Payment processing failed"), errorMessage);
                this._enableButton();
            }
        }).catch((error) => {
            this._displayErrorDialog(_t("Payment processing failed"), error);
            this._enableButton?.();
        });;
    },

    
});