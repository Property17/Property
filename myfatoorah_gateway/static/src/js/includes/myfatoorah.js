var myFatoorahPaymentMethodId = undefined;
var myFatoorahPaymentMethodCode = undefined;
var is_form_prepared = false;
var is_form_preparing = false;
let formPreparationPromise = null;

function resetMyFatoorahFormState() {
    is_form_prepared = false;
    formPreparationPromise = null;
}

function _getMfSessionScript(state, country_code, gateway){

    var subdomain = '';

    if(state == 'test'){
        subdomain = 'demo'
    }else{
        if(country_code == 'SAU'){
            subdomain = 'sa';
        }else if(country_code == 'QAT'){
            subdomain = 'qa'
        }else{
            subdomain = 'portal'
        }
    }
    var base_url = "https://" + subdomain + ".myfatoorah.com/";

    const endpoints = {
        google_pay: "googlepay/v1/googlepay.js",
        cardview: "cardview/v2/session.js",
        apple_pay: "applepay/v3/applepay.js",
        embedded: "payment/v1/session.js"
    };

    return base_url + endpoints[gateway];
}

function _loadScript(src) {
    return new Promise((resolve, reject) => {
        const script = document.createElement('script');
        script.src = src;
        script.onload = () => resolve();
        script.onerror = () => reject(new Error(`Failed to load script: ${src}`));
        document.head.appendChild(script);
    });
}

function _prepareGooglePay(country_code, state) {
    const src = _getMfSessionScript(state, country_code, "google_pay");
    return _loadScript(src);
}

function _prepareForm(country_code, state) {
    const src = _getMfSessionScript(state, country_code, "cardview");
    return _loadScript(src);
}

function _prepareApplePay(country_code, state) {
    const src = _getMfSessionScript(state, country_code, "apple_pay");
    return _loadScript(src);
}

function _prepareEmbeddedPayment(country_code, state) {
    const src = _getMfSessionScript(state, country_code, "embedded");
    return _loadScript(src);
}

async function _prepareCards(cards_payment_methods) {
    let mfRowContainer = document.getElementById('mf-cards');

    if(cards_payment_methods.length > 0){
        for (let i = 0; i < cards_payment_methods.length; i++) {
            let mfCard = cards_payment_methods[i];
            let mfCardTitle = mfCard.PaymentMethodEn;
            try {
                let cardsHtml = `
            <div class="mf-card-container mf-div-${mfCard.PaymentMethodCode}" onclick="mfCardSubmit(${mfCard.PaymentMethodId})">
                <div class="mf-row-container">
                    <img class="mf-payment-logo" src="${mfCard.ImageUrl}" alt="${mfCardTitle}">
                    <span class="mf-payment-text mf-card-title">${mfCardTitle}</span>
                </div>
                <span class="mf-payment-text">
                    ${mfCard.GatewayTotalAmount} ${mfCard.PaymentCurrencyIso}
                </span>
            </div>
          `;
                mfRowContainer.innerHTML += cardsHtml;
            } catch (error) {
                console.log(error);
            }

        }
    }else{
        document.getElementById('mf-sectionCard')?.remove();
    }
}

function mfCardSubmit(payment_method_id){
    myFatoorahPaymentMethodId = payment_method_id
    var button = document.querySelector("button[name='o_payment_submit_button']");
    if (button) {
        button.click();
    } else {
        console.error('Button not found');
    }
}

if (!window.ApplePaySession) {

    document.getElementById('mf-ap-element')?.remove();

    var mfGpElement = document.getElementById('mf-gp-element');
    if (!mfGpElement) {
        document.getElementById('mf-or-cardsDivider')?.remove();
    }

    let mfDivAps = document.querySelectorAll('.mf-div-ap');
    mfDivAps.forEach(element => {
        element.remove();
    });

    var mfCardContainer = document.querySelectorAll('.mf-card-container');
    if (!mfGpElement) {
        document.getElementById('mf-or-formDivider')?.remove();
    }
}

function handleCardBinChanged(cardBin) {
    console.log(cardBin);
}
