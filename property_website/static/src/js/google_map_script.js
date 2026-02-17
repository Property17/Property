if ($('#MAP').length > 0) {
    try {
        var map;
        var infowindow;
        var markersArray = [];
        var pyrmont = new google.maps.LatLng(20.268455824834792, 85.84099235520011);
        var marker;
        var geocoder = new google.maps.Geocoder();
        var infowindow = new google.maps.InfoWindow();
        
        function createMarker(place,icon) {
            var marker = new google.maps.Marker({
                map: map,
                position: place.geometry.location,
                icon: icon,
                visible:true
        
            });
            markersArray.push(marker);
            google.maps.event.addListener(marker, 'click', function() {
                infowindow.setContent("<b>Name:</b>"+place.name+"<br><b>Address:</b>"+place.vicinity+"<br><b>Rating:</b>"+place.rating);
                infowindow.open(map, this);
            });
        
        }
        var source="";
        var dest='';
        
        function search_types(latLng,search_type){
            clearOverlays();
        
            if(!latLng){
                var latLng = pyrmont;
            }
        
            if (!search_type || !search_type.length){
                return false;
            }
            else
            {
                var service = new google.maps.places.PlacesService(map);
                if(jQuery.inArray("school", search_type) !== -1){
                    var type2= 'school';
                    var icon2 = "/property_website/static/images/"+type2+".png";
                    var request2 = {
                        location: latLng,
                        radius: 2000,
                        types: [type2] //e.g. school, restaurant,bank,bar,city_hall,gym,night_club,park,zoo
                    };
                    service.search(request2, function(results, status) {
                        map.setZoom(14);
                        if (status == google.maps.places.PlacesServiceStatus.OK) {
                            for (var i = 0; i < results.length; i++) {
                                results[i].html_attributions='';
                                createMarker(results[i],icon2);
                            }
                        }
                    });
                }
                if(jQuery.inArray("petrol_pump", search_type) !== -1){
                    var type13 = 'gas_station'
                    var icon13 = "/property_website/static/images/"+'fuel'+".png";
                    var request13 = {
                        location: latLng,
                        radius: 2000,
                        types: [type13] //e.g. school, restaurant,bank,bar,city_hall,gym,night_club,park,zoo
                    };
                    service.search(request13, function(results, status) {
                        map.setZoom(14);
                        if (status == google.maps.places.PlacesServiceStatus.OK) {
                            for (var i = 0; i < results.length; i++) {
                                results[i].html_attributions='';
                                createMarker(results[i],icon13);
                            }
                        }
                    });
                }
                if(jQuery.inArray("hospital", search_type) !== -1){
                    var type9 = 'hospital';
                    var icon9 = "/property_website/static/images/"+type9+".png";
                    var request9 = {
                        location: latLng,
                        radius: 2000,
                        types: [type9] //e.g. school, restaurant,bank,bar,city_hall,gym,night_club,park,zoo
                    };
                    service.search(request9, function(results, status) {
                        map.setZoom(14);
                        if (status == google.maps.places.PlacesServiceStatus.OK) {
                            for (var i = 0; i < results.length; i++) {
                                results[i].html_attributions='';
                                createMarker(results[i],icon9);
                            }
                        }
                    });
                }
                if(jQuery.inArray("bus_station", search_type) !== -1){
                    var type7 = 'bus_station';
                    var icon7 = "/property_website/static/images/"+type7+".png";
                    var request7 = {
                        location: latLng,
                        radius: 2000,
                        types: [type7] //e.g. school, restaurant,bank,bar,city_hall,gym,night_club,park,zoo
                    };
                    service.search(request7, function(results, status) {
                        map.setZoom(14);
                        if (status == google.maps.places.PlacesServiceStatus.OK) {
                            for (var i = 0; i < results.length; i++) {
                                results[i].html_attributions='';
                                createMarker(results[i],icon7);
                            }
                        }
                    });
                }
                if(jQuery.inArray("park", search_type) !== -1){
                    var type5 = 'park';
                    var icon5 = "/property_website/static/images/"+type5+".png";
                    var request5 = {
                        location: latLng,
                        radius: 2000,
                        types: [type5] //e.g. school, restaurant,bank,bar,city_hall,gym,night_club,park,zoo
                    };
                    service.search(request5, function(results, status) {
                        map.setZoom(14);
                        if (status == google.maps.places.PlacesServiceStatus.OK) {
                            for (var i = 0; i < results.length; i++) {
                                results[i].html_attributions='';
                                createMarker(results[i],icon5);
                            }
                        }
                    });
                }
                if(jQuery.inArray("bank", search_type) !== -1){
                    var type4 = 'bank';
                    var icon4 = "/property_website/static/images/"+type4+".png";
                    var request4 = {
                        location: latLng,
                        radius: 2000,
                        types: [type4] //e.g. school, restaurant,bank,bar,city_hall,gym,night_club,park,zoo
                    };
                    service.search(request4, function(results, status) {
                        map.setZoom(14);
                        if (status == google.maps.places.PlacesServiceStatus.OK) {
                            for (var i = 0; i < results.length; i++) {
                                results[i].html_attributions='';
                                createMarker(results[i],icon4);
                            }
                        }
                    });
                }
                if(jQuery.inArray("bar", search_type) !== -1){
                    var type8 = 'bar';
                    var icon8 = "/property_website/static/images/"+type8+".png";
                    var request8 = {
                        location: latLng,
                        radius: 2000,
                        types: [type8] //e.g. school, restaurant,bank,bar,city_hall,gym,night_club,park,zoo
                    };
                    service.search(request8, function(results, status) {
                        map.setZoom(14);
                        if (status == google.maps.places.PlacesServiceStatus.OK) {
                            for (var i = 0; i < results.length; i++) {
                                results[i].html_attributions='';
                                createMarker(results[i],icon8);
                            }
                        }
                    });
                }
                if(jQuery.inArray("movie_theater", search_type) !== -1){
                    var type10 = 'movie_theater';
                    var icon10 = "/property_website/static/images/"+type10+".png";
                    var request10 = {
                        location: latLng,
                        radius: 2000,
                        types: [type10] //e.g. school, restaurant,bank,bar,city_hall,gym,night_club,park,zoo
                    };
                    service.search(request10, function(results, status) {
                        map.setZoom(14);
                        if (status == google.maps.places.PlacesServiceStatus.OK) {
                            for (var i = 0; i < results.length; i++) {
                                results[i].html_attributions='';
                                createMarker(results[i],icon10);
                            }
                        }
                    });
                }
                if(jQuery.inArray("night_club", search_type) !== -1){
                    var type11 = 'night_club'
                    var icon11 = "/property_website/static/images/"+type11+".png";
                    var request11 = {
                        location: latLng,
                        radius: 2000,
                        types: [type11] //e.g. school, restaurant,bank,bar,city_hall,gym,night_club,park,zoo
                    };
                    service.search(request11, function(results, status) {
                        map.setZoom(14);
                        if (status == google.maps.places.PlacesServiceStatus.OK) {
                            for (var i = 0; i < results.length; i++) {
                                results[i].html_attributions='';
                                createMarker(results[i],icon11);
                            }
                        }
                    });
                }
                if(jQuery.inArray("zoo", search_type) !== -1){
                    var type12 = 'zoo'
                    var icon12 = "/property_website/static/images/"+type12+".png";
                    var request12 = {
                        location: latLng,
                        radius: 2000,
                        types: [type12] //e.g. school, restaurant,bank,bar,city_hall,gym,night_club,park,zoo
                    };
                    service.search(request12, function(results, status) {
                        map.setZoom(14);
                        if (status == google.maps.places.PlacesServiceStatus.OK) {
                            for (var i = 0; i < results.length; i++) {
                                results[i].html_attributions='';
                                createMarker(results[i],icon12);
                            }
                        }
                    });
                }
                if(jQuery.inArray("gym", search_type) !== -1){
                    var type3 = 'gym';
                    var icon3 = "/property_website/static/images/"+type3+".png";
                    var request3 = {
                        location: latLng,
                        radius: 2000,
                        types: [type3] //e.g. school, restaurant,bank,bar,city_hall,gym,night_club,park,zoo
                    };
                    service.search(request3, function(results, status) {
                        map.setZoom(14);
                        map.setZoom(14);
                        if (status == google.maps.places.PlacesServiceStatus.OK) {
                            for (var i = 0; i < results.length; i++) {
                                results[i].html_attributions='';
                                createMarker(results[i],icon3);
                            }
                        }
                    });
                }
                if(jQuery.inArray("atm", search_type) !== -1){
                    var type = 'atm';
                    var icon = "/property_website/static/images/"+type+".png";
                    var request = {
                        location: latLng,
                        radius: 2000,
                        types: [type] //e.g. school, restaurant,bank,bar,city_hall,gym,night_club,park,zoo
                    };
                    service.search(request, function(results, status) {
                        map.setZoom(14);
                        if (status == google.maps.places.PlacesServiceStatus.OK) {
                            for (var i = 0; i < results.length; i++) {
                                results[i].html_attributions='';
                                createMarker(results[i],icon);
                            }
                        }
                    });
                }
                if(jQuery.inArray("spa", search_type) !== -1){
                    var type6 = 'spa';
                    var icon6 = "/property_website/static/images/"+type6+".png";
                    var request6 = {
                        location: latLng,
                        radius: 2000,
                        types: [type6] //e.g. school, restaurant,bank,bar,city_hall,gym,night_club,park,zoo
                    };
                    service.search(request6, function(results, status) {
                        map.setZoom(14);
                        if (status == google.maps.places.PlacesServiceStatus.OK) {
                            for (var i = 0; i < results.length; i++) {
                                results[i].html_attributions='';
                                createMarker(results[i],icon6);
                            }
                        }
                    });
                }
            }
         }
        
        // Deletes all markers in the array by removing references to them
        function clearOverlays() {
            if (markersArray) {
                for (i in markersArray) {
                    markersArray[i].setVisible(false)
                }
                //markersArray.length = 0;
            }
        }
        //google.maps.event.addDomListener(window, 'load', initialize);
        
        function clearMarkers(){
            $('#show_btn').show();
            $('#hide_btn').hide();
            clearOverlays()
        }
        function showMarkers(){
            $('#show_btn').hide();
            $('#hide_btn').show();
            if (markersArray) {
                for (i in markersArray) {
                    markersArray[i].setVisible(true)
                }
            }
        }
        
        odoo.define('property_website.property_google_map', function(require) {
        
        $(document).ready(function(e){
            var map_div = $('#MAP')
            if (map_div.length > 0) {
                var lat = $('.lat').val();
                var lang = $('.long').val();
                map = new google.maps.Map(document.getElementById('MAP'), {
                    mapTypeId: google.maps.MapTypeId.ROADMAP,
                    center: new google.maps.LatLng(lat, lang),
                    zoom: 14,
                });
                showMap(false)
            }
        });
        
        function showMap(type){
            var imageUrl = 'http://chart.apis.google.com/chart?cht=mm&chs=24x32&chco=FFFFFF,008CFF,000000&ext=.png';
            var markerImage = new google.maps.MarkerImage(imageUrl,new google.maps.Size(24, 32));
        //    var input_addr=$("#pro_street").html() + ' ' + $("#pro_street2").html() + ' ' + $("#pro_city").html() + ' ' + $("#pro_state").html() + ' ' + $("#pro_country").html() + ' ' + $("#pro_zip").html();
            var street = $("#pro_street").data('street');
            var street2 = $("#pro_street2").data('street2');
            var city = $("#pro_city").data('city');
            var state = $("#pro_state").data('state');
            var country = $("#pro_country").data('country');
            var zip = $("#pro_zip").data('zip');
            if (street === undefined){
                var street=''
            }
            if (street2 === undefined){
                var street2=''
            }
            if (city === undefined){
                var city=''
            }
            if (state === undefined){
                var state=''
            }
            if (country === undefined){
                var country=''
            }
            if (zip === undefined){
                var zip=''
            }
            var input_addr=street + ' ' + street2 + ' ' + city + ' ' + state + ' ' + country + ' ' + zip;
        
            
            
            var geocoder = new google.maps.Geocoder();
            geocoder.geocode({address: input_addr}, function(results, status) {
                if (status == google.maps.GeocoderStatus.OK) {
        
                    var latitude = $('.lat').val();
                    var longitude = $('.long').val();
                    var latitude = latitude || results[0].geometry.location.lat();
                    var longitude = longitude || results[0].geometry.location.lng();
                    
                    var latlng = new google.maps.LatLng(latitude, longitude);
                    if (results[0]) {
                        map.setZoom(14);
                        map.setCenter(latlng);
                        marker = new google.maps.Marker({
                            position: latlng,
                            map: map,
                            icon: markerImage,
                            draggable: true
                        });
                        $('#btn').hide();
                        $('#latitude,#longitude').show();
                        $('#address').val(results[0].formatted_address);
                        $('#latitude').val(marker.getPosition().lat());
                        $('#longitude').val(marker.getPosition().lng());
                        infowindow.setContent(results[0].formatted_address);
                        infowindow.open(map, marker);
                        if (type){
                            search_types(marker.getPosition(),type);
                        }
                        google.maps.event.addListener(marker, 'click', function() {
                            infowindow.open(map,marker);
        
                        });
        
        
                        google.maps.event.addListener(marker, 'dragend', function() {
        
                            geocoder.geocode({'latLng': marker.getPosition()}, function(results, status) {
                                if (status == google.maps.GeocoderStatus.OK) {
                                    if (results[0]) {
                                        $('#btn').hide();
                                        $('#latitude,#longitude').show();
                                        $('#address').val(results[0].formatted_address);
                                        $('#latitude').val(marker.getPosition().lat());
                                        $('#longitude').val(marker.getPosition().lng());
                                    }
        
                                    infowindow.setContent(results[0].formatted_address);
                                    var centralLatLng = marker.getPosition();
        //                            search_types(centralLatLng);
                                    infowindow.open(map, marker);
                                }
                            });
                        });
                        google.maps.event.trigger(map, 'resize');
        
                    } else {
                        alert("No results found");
                    }
                } else {
                    alert("Geocoder failed due to: " + status);
                }
            });
        
        }
        
        
         $(document).on('click', 'a[data-target="#map"]', function(){
             var list_places = []
             initialize()
             $('#table-map-near-by .chkbox:checked').each(function(){
                  list_places.push(this.id);
             });
             showMap(list_places)
         });
        
          $(document).on('click', '.property_name', function(e){
             var list_places = []
             initialize()
             $('#table-map-near-by .chkbox:checked').each(function(){
                  list_places.push(this.id);
             });
             showMap(list_places)
         });
        
        $(document).on('click', '#table-map-near-by tr td input', function(){
           var list_places = []
           $('#table-map-near-by .chkbox:checked').each(function(){
        
                 list_places.push(this.id);
            });
           showMap(list_places)
        });
        
        });
    }catch(e) {
    }
}