/** @odoo-module **/

import { Component, onMounted } from "@odoo/owl";
import { registry } from "@web/core/registry";

export class HomePageAutocomplete extends Component {
    setup() {
        this.autocomplete = {};
        this.autocompletesWraps = ['test', 'test2'];

        // Initialize the autocomplete functionality when the component is mounted.
        onMounted(() => {
            this._initializeMapAutocomplete();
        });

        // Event listener for input focus to reinitialize autocomplete.
        $(document).on('focus', '.location_input_auto', (ev) => {
            const formFilterClass = $(ev.currentTarget).parents('form');
            this._initializeMapAutocomplete(formFilterClass);
        });
    }

    /**
     * Initialize Google Maps Autocomplete for the given form.
     * @param {HTMLElement} formFilterClass - Optional form element to initialize autocomplete for.
     */
    _initializeMapAutocomplete(formFilterClass = null) {
        this.autocompletesWraps.forEach((name) => {
            const element = $(`#${name} .autocomplete`);
            if (element.length === 0) return;

            // Initialize Google Maps autocomplete for the input field.
            this.autocomplete[name] = new google.maps.places.Autocomplete(element[0]);

            // Add event listener for 'place_changed' on the autocomplete instance.
            google.maps.event.addListener(this.autocomplete[name], 'place_changed', () => {
                const place = this.autocomplete[name].getPlace();
                const form = this._getFormByName(name);

                // Set the place name into the input field.
                $('.form_filter_rent').find('#street_name').val(place.name);

                // Reset form fields.
                Object.keys(form).forEach((component) => {
                    $(`#${name} .${component}`).val('');
                    $(`#${name} .${component}`).attr('disabled', false);
                });

                // Populate form fields with address components from the place.
                place.address_components.forEach((component) => {
                    const addressType = component.types[0];
                    if (form[addressType]) {
                        const val = component[form[addressType]];
                        $(`#${name} .${addressType}`).val(val);
                    }
                });
            });
        });
    }

    /**
     * Get the form object by the given name.
     * @param {string} name - The name of the form.
     * @returns {Object} The corresponding form object.
     */
    _getFormByName(name) {
        const forms = {
            test: { street_number: 'short_name', route: 'long_name', locality: 'long_name', administrative_area_level_1: 'short_name', country: 'long_name', postal_code: 'short_name' },
            test2: { street_number: 'short_name', route: 'long_name', locality: 'long_name', administrative_area_level_1: 'short_name', country: 'long_name', postal_code: 'short_name' }
        };
        return forms[name];
    }
}

// Register the component to the Odoo registry.
registry.category("public_widgets").add("HomePageAutocomplete", HomePageAutocomplete);
