// //odoo.define('pmsh.home_page', function (require) {
var autocomplete = {};
var autocompletesWraps = ['test', 'test2'];

var test_form = { street_number: 'short_name', route: 'long_name', locality: 'long_name', administrative_area_level_1: 'short_name', country: 'long_name', postal_code: 'short_name' };
var test2_form = { street_number: 'short_name', route: 'long_name', locality: 'long_name', administrative_area_level_1: 'short_name', country: 'long_name', postal_code: 'short_name' };


function initialize_map_autocomplete(form_filter_class) {

    $.each(autocompletesWraps, function(index, name) {

        if($('#'+name).length == 0) {
            return;
        }

        // autocomplete[name] = new google.maps.places.Autocomplete($('#'+name+' .autocomplete')[0], { types: ['geocode'] });
        autocomplete[name] = new google.maps.places.Autocomplete($('#'+name+' .autocomplete')[0]);

        google.maps.event.addListener(autocomplete[name], 'place_changed', function() {
        	
            var place = autocomplete[name].getPlace();
            var form = eval(name+'_form');

            var place_name = place.name
            $('.form_filter_rent').find('#street_name').val(place_name)

            for (var component in form) {
                $('#'+name+' .'+component).val('');
                $('#'+name+' .'+component).attr('disabled', false);
            }

            for (var i = 0; i < place.address_components.length; i++) {
                var addressType = place.address_components[i].types[0];
                if (typeof form[addressType] !== 'undefined') {
                  var val = place.address_components[i][form[addressType]];
                  $('#'+name+' .'+addressType).val(val);
                }
            }
        });
    });
}

$(document).on('focus', '.location_input_auto', function(e){
var form_filter_class = $(this).parents('form');
    initialize_map_autocomplete(form_filter_class)
});

initialize_map_autocomplete()
google.maps.event.addDomListener(window, 'load', initialize_map_autocomplete)
