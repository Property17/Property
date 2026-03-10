/** @odoo-module **/

import paymentForm from '@payment/js/payment_form';
import { jsonrpc, RPCError } from "@web/core/network/rpc_service";
import { _t } from "@web/core/l10n/translation";

paymentForm.include({

    myFatoorahSessionId: undefined,

    // #=== DOM MANIPULATION ===#

    /**
     * Prepare the inline form of myfatoorah for direct payment.
     *
     * @override method from @payment/js/payment_form
     * @private
     * @param {number} providerId - The id of the selected payment option's provider.
     * @param {string} providerCode - The code of the selected payment option's provider.
     * @param {number} paymentOptionId - The id of the selected payment option
     * @param {string} paymentMethodCode - The code of the selected payment method, if any.
     * @param {string} flow - The online payment flow of the selected payment option.
     * @return {void}
     */
    async _prepareInlineForm(providerId, providerCode, paymentOptionId, paymentMethodCode, flow) {

        if (formPreparationPromise) {
            console.log("Form preparation is already in progress. Please wait.");
            return formPreparationPromise;
        }

        var currentURL = window.location.href;
        var isTenancyPage = currentURL.includes("tenancy_payment_link");
        if (isTenancyPage && typeof resetMyFatoorahFormState === 'function') {
            resetMyFatoorahFormState();
        }
        if(is_form_prepared || is_form_preparing){
            return;
        }
        if (providerCode !== 'myfatoorah') {
            this._super(...arguments);
            return;
        } else if (flow === 'token') {
            return;
        }

        const myFatoorahRadio = document.querySelector('input[data-provider-code="myfatoorah"]');

        if (myFatoorahRadio) {
            myFatoorahRadio.disabled = true;
        }

        is_form_preparing = true;

        formPreparationPromise = (async () => {
            try {
                this._setPaymentFlow('direct');

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
                    if (hiddenInput && hiddenInput.value) {
                        var rawVal = hiddenInput.value.trim();
                        if (rawVal && rawVal !== '[]') {
                            try {
                                initiateParams.selected_rent_schedule_ids = JSON.parse(rawVal);
                            } catch (e) {
                                initiateParams.selected_rent_schedule_ids = rawVal;
                            }
                        }
                    }
                }

                const initiatePaymentResult = await jsonrpc('/payment/myfatoorah/initiate-payment', initiateParams);

                if (!initiatePaymentResult.success){
                    this._displayErrorDialog(_t("Validation Error"), initiatePaymentResult.message);
                    this._enableButton();
                    is_form_preparing = false;
                    return;
                }

                const { country_code, state, checkout_gateways } = initiatePaymentResult;
                const cards_payment_methods = checkout_gateways?.cards;

                is_google_pay_enabled = !!checkout_gateways.gp;
                is_apple_pay_enabled = !!(checkout_gateways.ap && window.ApplePaySession);
                is_card_view_enabled = checkout_gateways.form?.length > 0;

                if(!is_google_pay_enabled){
                    document.getElementById('mf-sectionGP')?.remove();
                    if(!is_apple_pay_enabled && window.ApplePaySession){
                        document.getElementById('mf-or-cardsDivider')?.remove();
                    }
                }

                await _prepareEmbeddedPayment(country_code, state);
                await _prepareCards(cards_payment_methods);

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

                const initiateSessionResponse = await jsonrpc('/payment/myfatoorah/initiate-session', {});
                const sessionId = initiateSessionResponse?.response?.Data?.SessionId;

                if(is_google_pay_enabled || is_apple_pay_enabled || is_card_view_enabled){
                    //_loadGooglePay(checkout_gateways.gp.GatewayTotalAmount, country_code, checkout_gateways.gp.PaymentCurrencyIso, sessionId)
                    var countryCode = country_code;
                    var currencyCode = checkout_gateways.ap.PaymentCurrencyIso;
                    var amount = `${checkout_gateways.ap.GatewayTotalAmount}`;

                    var currentCouponCode = '';
                    var currentShippingMethodCode = '';
                    var currentShippingCountryCode = '';

                    var paymentOptions = [];

                    if(is_google_pay_enabled){
                        paymentOptions.push('Googlepay');
                    }
                    if(is_apple_pay_enabled){
                        paymentOptions.push('Applepay');
                    }
                    if(is_card_view_enabled){
                        paymentOptions.push('Card');
                    }

                    var paymentOptions = paymentOptions;

                    var mfConfig = {
                        sessionId: sessionId,
                        countryCode: countryCode,
                        currencyCode: currencyCode,
                        amount: amount,
                        callback: this._onClickPayment.bind(this),
                        paymentOptions: paymentOptions,
                        settings: {
                            applePay: {
                                containerId: "mf-ap-element",
                                style: {
                                    frameHeight: "55px",
                                    frameWidth: "95%",
                                    button: {
                                        type: "pay",
                                        borderRadius: "8px",
                                    }
                                },
                            },
                            googlePay: {
                                containerId: "mf-gp-element",
                                style: {
                                    frameHeight: "55px",
                                    frameWidth: "95%",
                                    button: {
                                        //text: "pay",
                                        type: "pay",
                                        borderRadius: "8px",
                                    }
                                },
                            },
                            card: {
                                containerId: "mf-form-element",
                                onCardBinChanged: handleCardBinChanged,
                                style: {
                                    input: {
                                        color: "black",
                                        fontSize: "13px",
                                        fontFamily: "sans-serif",
                                        inputHeight: "32px",
                                        inputMargin: "-1px",
                                        borderColor: "c7c7c7",
                                        borderWidth: "1px",
                                        borderRadius: "0px",
                                        boxShadow: "",
                                    },
                                    label: {
                                        display: false,
                                        color: "black",
                                        fontSize: "13px",
                                        fontWeight: "normal",
                                        fontFamily: "sans-serif",
                                    },
                                    error: {
                                        borderColor: "red",
                                        borderRadius: "8px",
                                        boxShadow: "0px"
                                    },
                                    button: {
                                        useCustomButton: true
                                    },
                                    separator: {
                                    },
                                },

                            }
                        },
                    };
                    myfatoorah.init(mfConfig);
                }

                is_form_prepared = true;

            } catch (error) {
                if (error instanceof RPCError) {
                    this._displayErrorDialog(_t("Payment processing failed"), "Ops! Something went wrong on initiating MyFatoorah Payment, Please contact admin");
                    this._enableButton?.(); // This method doesn't exists in Express Checkout form.
                } else {
                    return Promise.reject(error);
                }
            } finally {
                is_form_preparing = false;
                if (myFatoorahRadio) {
                    myFatoorahRadio.disabled = false;
                }
                formPreparationPromise = null;
            }
        })();

        return formPreparationPromise;
    },

    // #=== PAYMENT FLOW ===#

    /**
     * Simulate a feedback from a payment provider and redirect the customer to the status page.
     *
     * @override method from payment.payment_form
     * @private
     * @param {string} providerCode - The code of the selected payment option's provider.
     * @param {number} paymentOptionId - The id of the selected payment option.
     * @param {string} paymentMethodCode - The code of the selected payment method, if any.
     * @param {object} processingValues - The processing values of the transaction.
     * @return {void}
     */
    async _processDirectFlow(providerCode, paymentOptionId, paymentMethodCode, processingValues) {
        if (providerCode !== 'myfatoorah') {
            this._super(...arguments);
            return;
        }

        if(myFatoorahPaymentMethodId != undefined){ /* Cards */
            return this._myfatoorahExecutePayment(null, myFatoorahPaymentMethodId);
        }else if(this.myFatoorahSessionId != undefined){ /*Google and Apple pay*/
            return this._myfatoorahExecutePayment(this.myFatoorahSessionId);
        } else{ /* Card view */
            myfatoorah.submitCardPayment();
            return Promise.resolve();
        }
    },

    _onClickPayment: function(response) {
        var button = document.querySelector("button[name='o_payment_submit_button']");
        if (response.isSuccess == false){
            this._displayErrorDialog(_t("Payment processing failed"), response.error);
            this._enableButton?.();
            return Promise.reject();
        } else {
            if (button) {
                this.myFatoorahSessionId = response.sessionId;
                if (response.paymentType == 'Card'){ // Card view
                    return this._myfatoorahExecutePayment(this.myFatoorahSessionId);
                } else {   // Google pay & Apple pay
                    button.click();
                    return Promise.resolve();
                }
            } else {
                console.error('Button not found');
                return Promise.reject();
            }
        }
    },

    _myfatoorahExecutePayment: function(session_id = null, payment_method_id = null){
        if(session_id == null && payment_method_id == null){
            this._displayErrorDialog(_t("Missing Data"), "Session and payment method cannot be null");
            this._enableButton();
            return Promise.reject();
        }

        return jsonrpc('/payment/myfatoorah/execute-payment', {
            SessionId: session_id,
            PaymentMethodId: payment_method_id,
        }).then((data) => {
            if (!data.success){
                this._displayErrorDialog(_t("Validation Error"), data.message);
                this._enableButton();
                return Promise.reject();
            }
            var mf_response = JSON.parse(data.data)
            if (mf_response.IsSuccess) {
                var paymentUrl = mf_response.Data.PaymentURL;
                try {
                    window.location.href = paymentUrl;
                } catch (error) {
                    console.log(error);
                    window.location.href = paymentUrl;
                }
                return Promise.resolve();
            } else {
                var errorMessage = '';
                if (mf_response.ValidationErrors && mf_response.ValidationErrors.length > 0) {
                    mf_response.ValidationErrors.forEach((error) => {
                        errorMessage = error.Error; // Print each error message
                    });
                }
                this._displayErrorDialog(_t("Payment processing failed"), errorMessage);
                this._enableButton();
                return Promise.reject();
            }
        }).catch((error) => {
            this._displayErrorDialog(_t("Payment processing failed"), error);
            this._enableButton?.();
            return Promise.reject();
        });
    },
});
