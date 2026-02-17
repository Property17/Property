/** @odoo-module **/

import { Component, onMounted } from "@odoo/owl";
import { registry } from "@web/core/registry";

export class PropertyGoogleMap extends Component {
    markersArray = [];
    pyrmont = new google.maps.LatLng(20.268455824834792, 85.84099235520011);

    setup() {
        onMounted(() => {
            if ($('#MAP').length > 0) {
                this._initializeMap();
            }
        });

        this._bindEvents();
    }

    /**
     * Initialize the Google Map.
     */
    _initializeMap() {
        const lat = $('.lat').val() || this.pyrmont.lat();
        const lng = $('.long').val() || this.pyrmont.lng();

        this.map = new google.maps.Map(document.getElementById('MAP'), {
            mapTypeId: google.maps.MapTypeId.ROADMAP,
            center: new google.maps.LatLng(lat, lng),
            zoom: 14,
        });

        this.infowindow = new google.maps.InfoWindow();
        this._showMap(false);
    }

    /**
     * Create and display a marker on the map.
     */
    _createMarker(place, icon) {
        const marker = new google.maps.Marker({
            map: this.map,
            position: place.geometry.location,
            icon,
            visible: true,
        });

        this.markersArray.push(marker);

        google.maps.event.addListener(marker, 'click', () => {
            this.infowindow.setContent(
                `<b>Name:</b> ${place.name}<br><b>Address:</b> ${place.vicinity}<br><b>Rating:</b> ${place.rating}`
            );
            this.infowindow.open(this.map, marker);
        });
    }

    /**
     * Search and display places of specific types.
     */
    _searchTypes(latLng = this.pyrmont, searchTypes = []) {
        this._clearOverlays();

        if (!searchTypes.length) return;

        const service = new google.maps.places.PlacesService(this.map);
        searchTypes.forEach((type) => {
            const icon = `/property_website/static/images/${type}.png`;
            const request = {
                location: latLng,
                radius: 2000,
                types: [type],
            };

            service.nearbySearch(request, (results, status) => {
                if (status === google.maps.places.PlacesServiceStatus.OK) {
                    results.forEach((result) => {
                        result.html_attributions = '';
                        this._createMarker(result, icon);
                    });
                }
            });
        });
    }

    /**
     * Show the map centered on the specified address or coordinates.
     */
    _showMap(searchTypes = []) {
        const address = this._getFormattedAddress();
        const geocoder = new google.maps.Geocoder();

        geocoder.geocode({ address }, (results, status) => {
            if (status === google.maps.GeocoderStatus.OK) {
                const location = results[0].geometry.location;
                this.map.setCenter(location);
                this.map.setZoom(14);

                const marker = new google.maps.Marker({
                    map: this.map,
                    position: location,
                    icon: this._getDefaultMarkerIcon(),
                    draggable: true,
                });

                this._addMarkerListeners(marker, geocoder);

                if (searchTypes.length) {
                    this._searchTypes(location, searchTypes);
                }
            } else {
                alert(`Geocode failed: ${status}`);
            }
        });
    }

    /**
     * Clear all markers from the map.
     */
    _clearOverlays() {
        this.markersArray.forEach((marker) => marker.setVisible(false));
    }

    /**
     * Add listeners to the marker for interactions.
     */
    _addMarkerListeners(marker, geocoder) {
        google.maps.event.addListener(marker, 'click', () => {
            this.infowindow.open(this.map, marker);
        });

        google.maps.event.addListener(marker, 'dragend', () => {
            const position = marker.getPosition();
            geocoder.geocode({ location: position }, (results, status) => {
                if (status === google.maps.GeocoderStatus.OK) {
                    const address = results[0].formatted_address;
                    $('#address').val(address);
                    $('#latitude').val(position.lat());
                    $('#longitude').val(position.lng());
                    this.infowindow.setContent(address);
                    this.infowindow.open(this.map, marker);
                }
            });
        });
    }

    /**
     * Get the formatted address from input fields.
     */
    _getFormattedAddress() {
        const fields = ['#pro_street', '#pro_street2', '#pro_city', '#pro_state', '#pro_country', '#pro_zip'];
        return fields
            .map((selector) => $(selector).data() || '')
            .join(' ')
            .trim();
    }

    /**
     * Get the default marker icon.
     */
    _getDefaultMarkerIcon() {
        const imageUrl = 'http://chart.apis.google.com/chart?cht=mm&chs=24x32&chco=FFFFFF,008CFF,000000&ext=.png';
        return new google.maps.MarkerImage(imageUrl, new google.maps.Size(24, 32));
    }

    /**
     * Bind event listeners to handle user interactions.
     */
    _bindEvents() {
        $(document).on('click', 'a[data-target="#map"], .property_name, #table-map-near-by tr td input', () => {
            const selectedPlaces = this._getSelectedPlaces();
            this._showMap(selectedPlaces);
        });

        $('#show_btn').on('click', () => this._showMarkers());
        $('#hide_btn').on('click', () => this._clearOverlays());
    }

    /**
     * Get selected places from the table checkboxes.
     */
    _getSelectedPlaces() {
        return $('#table-map-near-by .chkbox:checked')
            .map((_, checkbox) => $(checkbox).attr('id'))
            .get();
    }

    /**
     * Show all markers on the map.
     */
    _showMarkers() {
        $('#show_btn').hide();
        $('#hide_btn').show();

        this.markersArray.forEach((marker) => marker.setVisible(true));
    }
}

// Register the component in the Odoo registry.
registry.category('public_widgets').add('PropertyGoogleMap', PropertyGoogleMap);
