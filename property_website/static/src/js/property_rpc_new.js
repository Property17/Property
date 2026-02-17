/** @odoo-module **/

import publicWidget from '@web/legacy/js/public/public_widget';

publicWidget.registry.PropertyWebsiteRPC = publicWidget.Widget.extend({
    selector: '#property_website',

    events: {
        'change .search_property_select2': '_onChangeSearchPropertySelect2',
        'change #property_sort_by': '_onChangePropertySort',
        'change #property_type_select_filter': '_onChangeTypeFilter',
        'change #search_property_by_bedrooms': '_onChangeBedroomsFilter',
        'change #search_property_by_bathrooms': '_onChangeBathroomsFilter',
        'change #search_property_by_furnish_type': '_onChangeFurnishType',
        'change #search_property_by_publication_date': '_onChangePublicationDate',
        'click .listing-save, .listing-saved-data': '_onClickToggleFavorite',
        'click #menu-toggle': '_onToggleMenu',
        'mouseover .dropdown-submenu': '_onMouseOverDropdown',
        'mouseleave .dropdown-submenu': '_onMouseLeaveDropdown',
    },

    /**
     * @constructor
     */

    init: function () {
        this._super.apply(this, arguments);
        this.rpc = this.bindService("rpc");
        this._initializeSelect2();
        this._initializeSliders();

    },

    /**
     * Initialize Select2 elements.
     */
    _initializeSelect2() {
        $('#property_type_id, .search_property_select2').select2({
            placeholder: 'Select Property Type...',
        });
    },

    /**
     * Initialize jQuery UI sliders.
     */
    _initializeSliders() {
        this._initSlider('#bead_slider_range', '#min_bead_range_id', '#max_bead_range_id', '#bead_amount');
        this._initSlider('#bath_slider_range', '#min_bath_range_id', '#max_bath_range_id', '#bath_amount');
        this._initializePriceSlider();
    },

    /**
     * Generic slider initialization function.
     */
    _initSlider(selector, minInput, maxInput, display) {
        $(selector).slider({
            range: true,
            step: 1,
            min: 1,
            max: 5,
            values: [$(minInput).val(), $(maxInput).val()],
            slide: (event, ui) => {
                $(display).val(`${ui.values[0]} - ${ui.values[1]}`);
                $(minInput).val(ui.values[0]);
                $(maxInput).val(ui.values[1]);
            },
        });
        $(display).val(`${$(selector).slider('values', 0)} - ${$(selector).slider('values', 1)}`);
    },

    /**
     * Initialize the price slider with backend data using RPC.
     */
    _initializePriceSlider() {
        this.rpc('/min_max_price', {}).then(data => {
            $('#price_slider_range').slider({
                range: true,
                step: 500,
                min: data.min_value,
                max: data.max_value,
                values: [$('#min_price_range_id').val(), $('#max_price_range_id').val()],
                slide: (event, ui) => {
                    $('#price_slider').val(`$${ui.values[0]} - $${ui.values[1]}`);
                    $('#min_price_range_id').val(ui.values[0]);
                    $('#max_price_range_id').val(ui.values[1]);
                },
            });
        });
    },



    /**
     * Event handler for property type change.
     */
    _onChangeSearchPropertySelect2(ev) {
        $('input[name="type_id"]').val($(ev.currentTarget).val());
    },

    _onChangePropertySort() {
        $('#search_property').submit();
    },

    _onChangeTypeFilter(ev) {
        $('.selected_type').val($(ev.currentTarget).val());
        $('#search_property').submit();
    },

    _onChangeBedroomsFilter() {
        $('#search_property').submit();
    },

    _onChangeBathroomsFilter() {
        $('#search_property').submit();
    },

    _onChangeFurnishType() {
        $('#search_property').submit();
    },

    _onChangePublicationDate() {
        $('#search_property').submit();
    },

    /**
     * Toggle favorite property.
     */
    _onClickToggleFavorite(ev) {
        const isFavorite = $(ev.currentTarget).hasClass('listing-save');
        this.rpc('/update_fav_property', {
            fav_checked: isFavorite,
            fav_property: $(ev.currentTarget).data('property_id'),
        }).then(data => {
            const parent = $(ev.currentTarget).parent();
            parent.find('.listing-save, .listing-saved-data').toggle();
            $('#view_all_asset_sale_saved').text(`Saved (${data})`);
        });
    },


    /**
     * Submit the property form using RPC.
     */


    /**
     * Toggle the menu.
     */
    _onToggleMenu(ev) {
        ev.preventDefault();
        $('#wrapper').toggleClass('active');
    },

    /**
     * Handle mouseover on dropdown submenu.
     */
    _onMouseOverDropdown(ev) {
        $(ev.currentTarget).find('.dropdown-menu').show();
    },

    /**
     * Handle mouseleave on dropdown submenu.
     */
    _onMouseLeaveDropdown(ev) {
        $(ev.currentTarget).find('.dropdown-menu').hide();
    },
});

publicWidget.registry.PropertySubmitForm = publicWidget.Widget.extend({
    selector: '.sider_feedback_div',


    events: {

        'click #send_property_id': '_onSubmitPropertyForm',

    },

     /**
 * @constructor
 */

     init: function () {
        this._super.apply(this, arguments);
        this.rpc = this.bindService("rpc");


    },

    _onSubmitPropertyForm: function (ev) {
        ev.preventDefault();
        console.log($('#selectedpropertyForm')[0].checkValidity())
        if ($('#selectedpropertyForm')[0].checkValidity()) {
            this.rpc('/contactus/create_lead', {

                'contact_name': $("input[name='first_name']").val() + ' ' + $("input[name='last_name']").val(),
                'phone': $("input[name='phone']").val(),
                'email_from': $("input[name='email_from']").val(),
                'telType': $("select[name='telType']").val(),
                'telTime': $("select[name='telTime']").val(),
                'msg': $("textarea[name='msg']").val(),
                'asset': $("input[name='asset']").val(),
                'value_from': "Property page",
            }).then(() => {
                $('#selectedpropertyForm')[0].reset();
                $('#selectedpropertyForm').removeClass('was-validated');
                $('#display_success_msg').show();
            });
        }
    },
});

publicWidget.registry.PropertySubmitSaleForm = publicWidget.Widget.extend({
    selector: '.saleform_div',

    events: {

        'click #submit_sale_form': '_onSubmitSaleForm',

    },

    /**
 * @constructor
 */

    init: function () {
        this._super.apply(this, arguments);
        this.rpc = this.bindService("rpc");


    },

    /**
 * Submit the sale form using RPC.
 */
    _onSubmitSaleForm: function (ev) {
        ev.preventDefault();
        console.log($('#saleForm')[0].checkValidity())
        if ($('#saleForm')[0].checkValidity()) {
            this.rpc('/contactus/create_lead', {

                'contact_name': $("input[name='first_name']").val() + ' ' + $("input[name='last_name']").val(),
                'phone': $("input[name='phone']").val(),
                'email_from': $("input[name='email_from']").val(),
                'address': $("input[name='address']").val(),
                'city': $("input[name='city']").val(),
                'zip': $("input[name='zip']").val(),
                'country_id': $("select[name='country_id']").val(),
                'value_from': "Sales page",
            }).then(() => {
                $('#saleForm')[0].reset();
                $('#saleForm').removeClass('was-validated');
                $('#display_success_msg').show();
            });
        }
        else {
            ev.preventDefault();
            ev.stopPropagation();
            return false;
        }
    },

});

