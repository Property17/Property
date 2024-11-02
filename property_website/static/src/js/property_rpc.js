odoo.define('property_website.property_website_rpc', function(require) {
        var odoo = require('web.ajax');

    $(document).ready(function(e){
        
        $('#property_type_id').select2({
            placeholder: 'Select Property Type...',
        });
        
        $('.search_property_select2').select2({
            placeholder: 'Select Property Type...',
        });
        
        $('.search_property_select2').change(function() {
            $('input[name="type_id"]').val($(this).val())
        });
        
    	if ((window.location.href.indexOf('/lease-properties') > 0) || (window.location.href.indexOf('/properties') > 0)){
            // bedroom slide js
            $("#bead_slider_range").slider({
                range: true,
                animate: true,
                step: 1,
                min: 1,
                max: 5,
                heterogeneity: ['50/50000'],
                format: {
                    format: '##.0',
                    locale: 'de'
                },
                dimension: '',
                values: [$('#min_bead_range_id').val(), $('#max_bead_range_id').val()],
                slide: function(event, ui) {
                    $("#bead_amount").val("" + ui.values[0] + "-" + ui.values[1]);
                    $('#min_bead_range_id').val(ui.values[0]);
                    $('#max_bead_range_id').val(ui.values[1]);
                }
            });
            $("#bead_amount").val("" + $("#bead_slider_range").slider("values", 0) + " - " + $("#bead_slider_range").slider("values", 1));
            var $bead_amount = $("#bead_amount").val();
            $('#bead_slider_range span').first().html('<label><span class="fa fa-chevron-left"></span></label>');
            $('#bead_slider_range span').first().next().html('<label><span class="fa fa-chevron-right"></span></label>');

            //  bathroom slide js
            $("#bath_slider_range").slider({
                range: true,
                animate: true,
                step: 1,
                min: 1,
                max: 5,
                heterogeneity: ['50/50000'],
                format: {
                    format: '##.0',
                    locale: 'de'
                },
                dimension: '',
                values: [$('#min_bath_range_id').val(), $('#max_bath_range_id').val()],
                slide: function(event, ui) {
                    $("#bath_amount").val("" + ui.values[0] + "-" + ui.values[1]);
                    $('#min_bath_range_id').val(ui.values[0]);
                    $('#max_bath_range_id').val(ui.values[1]);
                }
            });
            $("#bath_amount").val("" + $("#bath_slider_range").slider("values", 0) + " - " + $("#bath_slider_range").slider("values", 1));
            var $bath_amount = $("#bath_amount").val();
            $('#bath_slider_range span').first().html('<label><span class="fa fa-chevron-left"></span></label>');
            $('#bath_slider_range span').first().next().html('<label><span class="fa fa-chevron-right"></span></label>');

         // Price list slide js
            odoo.jsonRpc("/min_max_price", 'call', {}).then(function(data) {
                var min_p = $('#min_price_range_id').val() || data['min_value'];
                var max_p = $('#max_price_range_id').val() || data['max_value'];
                $("#price_slider_range").slider({
                    range: true,
                    animate: true,
                    step: 500,
                    min: data['min_value'],
                    max: data['max_value'],
                    heterogeneity: ['50/50000'],
                    format: {
                        format: '##.0',
                        locale: 'de'
                    },
                    dimension: '',
                    values: [min_p, max_p],
                    slide: function(event, ui) {
                        $("#price_slider").val(data['symbol'] + ui.values[0] + "- " + data['symbol'] + ui.values[1]);
                        $('#min_price_range_id').val(ui.values[0]);
                        $('#max_price_range_id').val(ui.values[1]);
                    }
                });
                $("#price_slider").val(data['symbol'] + $("#price_slider_range").slider("values", 0) + " - "+ data['symbol'] + $("#price_slider_range").slider("values", 1));
                $(".min_range_class").val(data['min_value'])
                $(".max_range_class").val(data['max_value'])
                var $price_slider = $("#price_slider").val();
                $('#price_slider_range a').first().html('<label><span class="fa fa-chevron-left"></span></label>');
                $('#price_slider_range a').first().next().html('<label><span class="fa fa-chevron-right"></span></label>');
            });
            
            
        } 
    	//====== Filter ========
    	$('#property_sort_by').on('change',function(e){
            $('#search_property').submit();
        })
        $('#property_type_select_filter').on('change',function(e){
            $('.selected_type').val($(this).val())
            $('#search_property').submit();
        })
        $('#search_property_by_bedrooms').on('change',function(e){
            $('#search_property').submit();
        })
        $('#search_property_by_bathrooms').on('change',function(e){
            $('#search_property').submit();
        })
        $('#search_property_by_furnish_type').on('change',function(e){
            $('#search_property').submit();
        })
        $('#search_property_by_publication_date').on('change',function(e){
            $('#search_property').submit();
        })
    	
    	$('.check_property').on('change',function(){
            var self = this;
            var total_selected_property_type_ids = [];
            $('.check_property:checked').each(function(){
                   var selected_id =$(this).data('property_type_id')
                   total_selected_property_type_ids.push(selected_id);
            });
            $('.selected_utilities').val(total_selected_property_type_ids)
            $('#search_property').submit();
        });
   	
   	
	    $(".heart").on("click", function() {
	    	$(this).toggleClass("is-active");
	    });
	    
	    $(document).on('click', '.listing-save,.listing-saved-data', function(e){
	        var fav_checked = false
	        var self = $(this)
	        if ($(this).hasClass('listing-save')){
	            fav_checked = true
	        }
	        odoo.jsonRpc("/update_fav_property", 'call', {
	            'fav_checked': fav_checked,
	            'fav_property': $(this).data('property_id')
	        }).then(function(data) {
	            var parent_div =self.parent()
	            if (fav_checked){
	                parent_div.find('.listing-saved-data').css('display', 'initial');
	                parent_div.find('.listing-save').css('display', 'none');
	            }else{
	                parent_div.find('.listing-save').css('display', 'initial');
	                parent_div.find('.listing-saved-data').css('display', 'none');
	            }
	            $('#view_all_asset_sale_saved').html('Saved (' + data +')')
	        });
	    });


		// Lift card and show stats on Mouseover
		$('#property-card').hover(function(){
				$(this).addClass('animate');
				$('div.carouselNext, div.carouselPrev').addClass('visible');
			 }, function(){
				$(this).removeClass('animate');
				$('div.carouselNext, div.carouselPrev').removeClass('visible');
		});
    	
        $(document).on('click', '.navbar a', function(e){
            $(this).each( function() {
                $(this).parent().removeClass('active');
            });
            $(this).parent().addClass('active');
        })


        //code for click on navbar in responsive view
        $(document).on('click', '.nav.sidebar-nav li .is-closed', function(e){
            if (this['id'] == 'user_account_logout'){
                $(document).find("ul.nav.sidebar-nav li a").addClass('is-open');
            }
            if (this['id'] != 'user_account_logout'){
                $('.hidden-md.hidden-lg.toggled ul.nav.sidebar-nav li a').removeClass('active');
                $(document).find("#wrapper").removeClass('toggled');
                $('#wrapper .overlay').css('display', 'none');
            }
        });
        $(document).on('click', '.nav.sidebar-nav li .is-open', function(e){
            if (this['id'] =='user_account_logout'){
                $(document).find("ul.nav.sidebar-nav li a").addClass('is-open');
            }
            if (this['id'] !='user_account_logout'){
                $('.hidden-md.hidden-lg.toggled ul.nav.sidebar-nav li a').removeClass('active');
                $(document).find("#wrapper").removeClass('toggled');
                $('#wrapper .overlay').css('display', 'none');
            }
        });

        $(document).on('click', '.hero-text', function(e){
            e.preventDefault();
            $('html, body').animate({
                scrollTop: $('.rest').offset().top - 50
            }, 1000);

        });

       // create lead from sales page
        $(document).on('click', '#submit_sale_form', function(e){
        	$("#display_success_msg").css('display', 'none');
            $('#saleForm').addClass('was-validated');
        	if ($('#saleForm')[0].checkValidity() === false) {
        		e.preventDefault();
        		e.stopPropagation();
            	return false;
        	}else{
        		odoo.jsonRpc("/contactus/create_lead", 'call', {
                    'contact_name' : $("input[name='first_name']").val() +' '+$("input[name='last_name']").val(),
                    'phone' : $("input[name='phone']").val(),
                    'email_from' : $("input[name='email_from']").val(),
                    'address' : $("input[name='address']").val(),
                    'city' : $("input[name='city']").val(),
                    'zip' : $("input[name='zip']").val(),
                    'country_id' : $("select[name='country_id']").val(),
                    'value_from' : "Sales page",
                }).then(function() {
                    $('#saleForm')[0].reset();
                    $('#saleForm').removeClass('was-validated');
                    $("#display_success_msg").css('display', 'block');
                });
        	}
        });

    // create lead from perticular property page
        $(document).on('click', '#send_property_id', function(e){
        	$("#display_success_msg").css('display', 'none');
        	$('#selectedpropertyForm').addClass('was-validated');
        	if ($('#selectedpropertyForm')[0].checkValidity() === false) {
        		e.preventDefault();
        		e.stopPropagation();
            	return false;
        	}else{
	        	odoo.jsonRpc("/contactus/create_lead", 'call', {
	                'contact_name' : $("input[name='first_name']").val() +' '+ $("input[name='last_name']").val(),
	                'phone' : $("input[name='phone']").val(),
	                'email_from' : $("input[name='email_from']").val(),
	                'telType' : $("select[name='telType']").val(),
	                'telTime' : $("select[name='telTime']").val(),
	                'msg' : $("textarea[name='msg']").val(),
	                'asset': $("input[name='asset']").val(),
	                'value_from' : "Property page",
	            }).then(function() {
	                $('#selectedpropertyForm')[0].reset();
	                $('#selectedpropertyForm').removeClass('was-validated');
	                $("#display_success_msg").css('display', 'block');
	            });
        	}
        });

        $(document).on('click', '.listing-save,.listing-saved-data', function(e){
            var fav_checked = false
            var self = $(this)
        	if ($(this).hasClass('listing-save')){
        		fav_checked = true
            }
            odoo.jsonRpc("/update_fav_property", 'call', {
                'fav_checked': fav_checked,
                'fav_property': $(this).data('lease_id')
            }).then(function(data) {
            	var parent_div =self.parent()
            	if (fav_checked){
            		parent_div.find('.listing-saved-data').css('display', 'block');
                	parent_div.find('.listing-save').css('display', 'none');
            	}else{
            		parent_div.find('.listing-save').css('display', 'block');
                	parent_div.find('.listing-saved-data').css('display', 'none');
            	}
                $('#view_all_asset_sale_saved').html('Saved (' + data +')')
            });
        });
        
//        if (window.location.href.indexOf('/properties/') > 0) {
//        	var list_places = []
//        	initialize()
//        	$('#table-map-near-by .chkbox:checked').each(function(){
//                 list_places.push(this.id);
//            });
//            showMap(list_places)
//        }

        if (window.location.pathname == '/' || window.location.pathname == '/page/homepage'){
        	//set price on the slider dynamically
            odoo.jsonRpc("/min_max_price", 'call', {}).then(function(data) {

                //code for rent
                $(".form_filter_rent .home_page_filter_price #amount").val("$" + data['min_value'] + " - $" + data['max_value']);
                $('.form_filter_rent .home_page_filter_price #min_property_range_id').val(data['min_value']);
                $('.form_filter_rent .home_page_filter_price #max_property_range_id').val(data['max_value']);
                $(".form_filter_rent .home_page_filter_price #slider_range").slider({
                    range: true,
                    animate: true,
                    step: 500,
                    min: data['min_value'],
                    max: data['max_value'],
                    heterogeneity: ['50/50000'],
                    format: {
                        format: '##.0',
                        locale: 'de'
                    },
                    dimension: '',
                    scale: [0, '|', 50, '|', '100', '|', 250, '|', 500],
                    values: [data['min_value'], data['max_value']],
                    slide: function(event, ui) {
                        $(".form_filter_rent .home_page_filter_price #amount").val("$" + ui.values[0] + " - $" + ui.values[1]);
                        $(".form_filter_rent .home_page_filter_price #min_property_range_id").val(ui.values[0]);
                        $(".form_filter_rent .home_page_filter_price #max_property_range_id").val(ui.values[1]);
                    }
                });

                $(".form_filter_rent .home_page_filter_price #amount").val("$" + $(".form_filter_rent .home_page_filter_price #slider_range").slider("values", 0) + " - $" + $(".form_filter_rent .home_page_filter_price #slider_range").slider("values", 1));
                var $amount = $(".form_filter_rent .home_page_filter_price #amount").val();
                $('.form_filter_rent .home_page_filter_price #slider_range a').html('<label><span class="fa fa-chevron-left"></span></label>');
                $('.form_filter_rent .home_page_filter_price #slider_range a').next().html('<label><span class="fa fa-chevron-right"></span></label>');
            });

            // bedroom slide js
            $("#bead_slider_range").slider({
                range: true,
                animate: true,
                step: 1,
                min: 1,
                max: 5,
                heterogeneity: ['50/50000'],
                format: {
                    format: '##.0',
                    locale: 'de'
                },
                dimension: '',
                values: [$('#min_bead_range_id').val(), $('#max_bead_range_id').val()],
                slide: function(event, ui) {
                    $("#bead_amount").val("" + ui.values[0] + "-" + ui.values[1]);
                    $('#min_bead_range_id').val(ui.values[0]);
                    $('#max_bead_range_id').val(ui.values[1]);
                }
            });
            $("#bead_amount").val("" + $("#bead_slider_range").slider("values", 0) + " - " + $("#bead_slider_range").slider("values", 1));
            var $bead_amount = $("#bead_amount").val();
            $('#bead_slider_range span').first().html('<label><span class="fa fa-chevron-left"></span></label>');
            $('#bead_slider_range span').first().next().html('<label><span class="fa fa-chevron-right"></span></label>');

            //  bathroom slide js
            $("#bath_slider_range").slider({
                range: true,
                animate: true,
                step: 1,
                min: 1,
                max: 5,
                heterogeneity: ['50/50000'],
                format: {
                    format: '##.0',
                    locale: 'de'
                },
                dimension: '',
                values: [$('#min_bath_range_id').val(), $('#max_bath_range_id').val()],
                slide: function(event, ui) {
                    $("#bath_amount").val("" + ui.values[0] + "-" + ui.values[1]);
                    $('#min_bath_range_id').val(ui.values[0]);
                    $('#max_bath_range_id').val(ui.values[1]);
                }
            });
            $("#bath_amount").val("" + $("#bath_slider_range").slider("values", 0) + " - " + $("#bath_slider_range").slider("values", 1));
            var $bath_amount = $("#bath_amount").val();
            $('#bath_slider_range span').first().html('<label><span class="fa fa-chevron-left"></span></label>');
            $('#bath_slider_range span').first().next().html('<label><span class="fa fa-chevron-right"></span></label>');

            // Price list slide js
            odoo.jsonRpc("/min_max_price", 'call', {}).then(function(data) {
                $("#price_slider_range").slider({
                    range: true,
                    animate: true,
                    step: 500,
                    min: 0,
                    max: data['max_value'],
                    heterogeneity: ['50/50000'],
                    format: {
                        format: '##.0',
                        locale: 'de'
                    },
                    dimension: '',
                    values: [$('#min_price_range_id').val(), $('#max_price_range_id').val()],
                    slide: function(event, ui) {
                        $("#price_slider").val("$" + ui.values[0] + "- $" + ui.values[1]);
                        $('#min_price_range_id').val(ui.values[0]);
                        $('#max_price_range_id').val(ui.values[1]);
                    }
                });
                $("#price_slider").val("$" + $("#price_slider_range").slider("values", 0) + " - $" + $("#price_slider_range").slider("values", 1));
                $(".min_range_class").val(data['min_value'])
                $(".max_range_class").val(data['max_value'])
                var $price_slider = $("#price_slider").val();
                $('#price_slider_range a').first().html('<label><span class="fa fa-chevron-left"></span></label>');
                $('#price_slider_range a').first().next().html('<label><span class="fa fa-chevron-right"></span></label>');
            });
        }

        //code for hover and click eveent in sales and rent page property type dropdown
        $(document).on('mouseover', '.dropdown-submenu', function(e){
            $(this).find(".dropdown-menu").attr('style', 'display: block;');

            $(this).find(".fa.fa-caret-left").attr('style', 'display: block;width:14px;float:left;margin-top: 3px;');
            $(this).find(".fa.fa-caret-down").attr('style', 'display: none;');
        });

        $(document).on('mouseleave', '.dropdown-submenu', function(e){
            if ($(this).find(".dropdown-menu").hasClass('active')){
                $(this).find(".fa.fa-caret-left").attr('style', 'display: block;width:14px;float:left;margin-top: 3px;');
                $(this).find(".fa.fa-caret-down").attr('style', 'display: none;');
            }
            else{
                $(this).find(".fa.fa-caret-left").attr('style', 'display: none');
                $(this).find(".fa.fa-caret-down").attr('style', 'display: block;width:14px;float:left;margin-top: 3px;');
                $(this).find(".dropdown-menu").attr('style', 'display: none;');
            }
        });

        $(document).on('click', '.dropdown-submenu', function(e){
            var dorpdown_menu = $(this).children(".dropdown-menu");
            if ($(this).children(".dropdown-menu").hasClass('active')){
                $(this).children(".dropdown-menu").attr('style', 'display: none');
                $(this).children(".dropdown-menu").removeClass('active');
                $(this).find(".fa.fa-caret-left").attr('style', 'display: none');
                $(this).find(".fa.fa-caret-down").attr('style', 'display: block;width:14px;float:left;margin-top: 3px;');
            }
            else{
                $(this).children(".dropdown-menu").attr('style', 'display: block');
                $(this).children(".dropdown-menu").addClass('active');
                $(this).find(".fa.fa-caret-down").attr('style', 'display: none;');
                $(this).find(".fa.fa-caret-left").attr('style', 'display: block;width:14px;float:left;margin-top: 3px;');
            }
        });

    //    $("#menu-toggle").click(function(e) {
        $(document).on('click', '#menu-toggle', function(e){
            e.preventDefault();
            $("#wrapper").toggleClass("active");
        });

        if ($(window).width() <= 992) {
            $('.arrow-slidebar').children().children("i").addClass('fa-chevron-right');
           }
           else{
           $('.arrow-slidebar').children().children("i").addClass('fa-chevron-left');
           }
            $(document).on('click', '.social_share_property', function(e){
        });

    //    $('#datetimepicker8').datepicker();
        $(document).bind('click', '.date_maintenance', function(e){
            $('#datetimepicker8').datepicker();
        });

        $(document).on('click', '.maintenane_type_class', function(e){
            $(this).parent('#inputTelType').find('.maintenane_type_class').removeClass('active')
            $(this).addClass('active')
        });

        // create Maintanance from perticular property page
        $(document).on('click', '#submit_maintanance', function(e){
            $('#MaintanancepropertyForm').validator('validate');
            if ($('#MaintanancepropertyForm').find('.has-error:visible').size() > 0) return;
            odoo.jsonRpc("/create_maintanance", 'call', {
                /*'type_id': $('#MaintanancepropertyForm #inputTelType .maintenane_type_class.active').data('type_id'),*/
                'type_id': $('#MaintanancepropertyForm #inputTelType .maintenane_type_class:selected').data('type_id'),
                'date': $('.date_maintenance').val(),
                'description': $('#MaintanancepropertyForm #inputMsg').val(),
                'property_id': $('#MaintanancepropertyForm').data('property_id'),
                'renters_fault': $('#renters_fault').is( ':checked' ),
            }).then(function() {
                $('#MaintanancepropertyForm')[0].reset();
                $("#MaintanancepropertyForm #display_success_msg").css('display', 'block');
            });
        });


    });
});
