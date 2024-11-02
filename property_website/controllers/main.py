# See LICENSE file for full copyright and licensing details

import ast
from datetime import datetime, date
from odoo import http
from odoo.http import request
from dateutil.relativedelta import relativedelta
from odoo.addons.payment_paypal.controllers.main import PaypalController
from odoo.addons.website.controllers.main import Website
import json, logging
_logger = logging.getLogger(__name__)


def get_cookie_list():
    account_asset_cookie_ids = []
    if request.uid == request.website.user_id.id:
        product_ids_from_cookies = request.httprequest.cookies.get(
            'property_id')
        product_ids_from_cookies_str = str(product_ids_from_cookies)
        product_ids_from_cookies_list = product_ids_from_cookies_str.split(',')

        if product_ids_from_cookies_list[0] == 'None':
            account_asset_cookie_ids = []
        else:
            for one_prod_cookie_id in product_ids_from_cookies_list:
                if not one_prod_cookie_id:
                    continue
                one_cookie_int_id = int(one_prod_cookie_id)
                account_asset_cookie_ids.append(one_cookie_int_id)
        return account_asset_cookie_ids
    else:
        user = request.env['res.users'].browse(request.uid)
        account_asset_cookie_ids = user.partner_id.sudo().fav_assets_ids.ids
    return account_asset_cookie_ids

class WebsiteHomepage(Website):

    @http.route()
    def index(self, **kw):
        partner = request.env.user.partner_id
        saved_assets = partner.sudo().fav_assets_ids
        lease_properties = request.env[
            'account.asset'].sudo().search([('state', '=', 'draft'),
                                            ('property_sale_rent', '=', 'rent')],
                                           order='id desc', limit=4)
        sale_properties = request.env[
            'account.asset'].sudo().search([('state', '=', 'close'),
                                            ('property_sale_rent', '=', 'sale')],
                                           order='id desc', limit=4)
        property_types = request.env['property.type'].sudo().search([])
        return request.render('website.homepage', {
            'product_ids_from_cookies_list': saved_assets.ids,
            'property_types': property_types,
            'lease_properties': lease_properties,
            'sale_properties': sale_properties,
        })


class PaypalController(PaypalController):

    def _get_return_url(self, **post):
        """ Extract the return URL from the data coming from paypal. """
        return_url = post.pop('return_url', '')
        if not return_url:
            custom = json.loads(post.pop('custom', False) or '{}')
            if post.get('item_name'):
                return_url = custom.get(
                    'return_url', '/selected_property_page?id=' + str(post.get('custom_values')['property_id']))
            else:
                return_url = custom.get('return_url', '/')
        return return_url

    def paypal_validate_data(self, **post):
        """ Paypal IPN: three steps validation to ensure data correctness
         - step 1: return an empty HTTP 200 response -> will be done at the end
           by returning ''
         - step 2: POST the complete, unaltered message back to Paypal (preceded
           by cmd=_notify-validate), with same encoding
         - step 3: paypal send either VERIFIED or INVALID (single word)

        Once data is validated, process it. """
        res = False
        new_post = dict(post, cmd='_notify-validate')
        reference = post.get('new_transaction_name')
        tx = None
        if reference:
            tx = request.registry['payment.transaction'].search(
                [('reference', '=', reference)])
        paypal_urls = request.registry['payment.acquirer']._get_paypal_urls(
            tx and tx.acquirer_id and tx.acquirer_id.environment or 'prod')
        validate_url = paypal_urls['paypal_form_url']
        resp = requests.post(validate_url, data=werkzeug.url_encode(new_post))
        resp = resp.content
        if resp == 'VERIFIED':
            _logger.info('Paypal: validated data')
            res = request.registry['payment.transaction'].sudo(
            ).form_feedback(post, 'paypal')
            # change state in transaction
            change_state = request.registry['payment.transaction'].sudo().write(int(
                post.get('new_transaction_id')), {'state': 'done'})
            # Create new Move
            create_new_move = request.registry['tenancy.rent.schedule'].sudo(
            ).create_move([int(post.get('custom_values')['payment_id'])])

        elif resp == 'INVALID':
            _logger.warning('Paypal: answered INVALID on data verification')
        else:
            _logger.warning(
                'Paypal: unrecognized paypal answer, received %s instead of VERIFIED or INVALID' % resp.text)
        return res

    @http.route('/payment/paypal/dpn', type='http', auth="none", methods=['POST'])
    def paypal_dpn(self, **post):
        custom_values = ast.literal_eval(post.get('invoice'))
        reference = str(post.get('item_number')) + '_' + \
            str(datetime.now().strftime("%Y-%m-%d_%H:%M:%S"))
        # Create new transaction in odoo
        new_transaction_id = request.env['payment.transaction'].create({
            'acquirer_id': request.env['payment.acquirer'].search([('name', '=', 'Paypal')])[0],
            'type': 'form',
            'amount': float(post.get('mc_gross')),
            'currency_id': request.env['res.currency'].search([('name', '=', str(post.get('mc_currency')))])[0],
            'partner_id': int(custom_values['partner_id']),
            'reference': reference,
        })
        post.update({'new_transaction_id': new_transaction_id,
                     'new_transaction_name': reference, 'custom_values': custom_values})
        return super(PaypalController, self).paypal_dpn(**post)


class PropertyWebsite(http.Controller):

    @http.route(['/properties'], type='http', auth="public", website=True, csrf=False)
    def search_property(self, **post):
        asset_obj = request.env["account.asset"].sudo()
        property_types = request.env['property.type'].sudo().search([])
        utilities = request.env['utility'].sudo().search([])
        selected_utilities = []
        order = None
        if post.get('sort_by') == 'most_recent':
            order = 'id DESC'
        if post.get('sort_by') == 'lowest_price':
            order = 'total_price'
        if post.get('sort_by') == 'highest_price':
            order = 'total_price DESC'
        domain = []
        vals = {}
        if 'rent_sale_type' in post:
            domain += [('property_sale_rent', '=', post.get('rent_sale_type'))]
            if post.get('rent_sale_type') == 'sale':
                domain += [('state', '=', 'close')]
            else:
                domain += [('state', '=', 'draft')]
            domain += [('state', '=', 'draft')]
        property_type_list = []
        if post.get('type_id'):
            property_type_list = ast.literal_eval(post.get('type_id'))
            if isinstance(property_type_list, int):
                property_type_list = [property_type_list]
            else:
                property_type_list = list(property_type_list)
            domain += [('type_id', 'in', property_type_list)]
        if post.get('min_range') and post.get('max_range'):
            domain += [('ground_rent', '>=', post.get('min_range')),
                       ('ground_rent', '<=', post.get('max_range'))]
            vals.update(
                {'min_range': post.get('min_range'),
                 'max_range': post.get('max_range')})
        if post.get('min_size') and post.get('max_size'):
            domain += [('gfa_meter', '>=', post.get('min_size')),
                       ('gfa_meter', '<=', post.get('max_size'))]
        if post.get('search_bedrooms'):
            domain += [('bedroom', '=', post.get('search_bedrooms'))]
        if post.get('search_bathrooms'):
            domain += [('bathroom', '=', post.get('search_bathrooms'))]
        if post.get('search_furnish_type'):
            domain += [('furnished', '=', post.get('search_furnish_type'))]
        if post.get('min_build_year') and post.get('max_build_year'):
            min_built_year_st_dt = date(int(post.get('min_build_year')), 1, 1)
            max_built_year_st_dt = date(int(post.get('max_build_year')), 12, 31)
            domain += [('built_year', '>=', min_built_year_st_dt),
                       ('built_year', '<=', max_built_year_st_dt)]
        if post.get('search_publication_date'):
            if post.get('search_publication_date') == '24_hour':
                curr_date = datetime.now().date()
                compare_date = curr_date - relativedelta(days=1)
                domain += [('create_date', '>=', compare_date),
                           ('create_date', '<=', curr_date)]
            if post.get('search_publication_date') == 'last_week':
                curr_date = datetime.now().date()
                compare_date = curr_date - relativedelta(days=7)
                domain += [('create_date', '>=', compare_date),
                           ('create_date', '<=', curr_date)]
            if post.get('search_publication_date') == 'last_month':
                curr_date = datetime.now().date()
                compare_date = curr_date - relativedelta(months=1)
                domain += [('create_date', '>=', compare_date),
                           ('create_date', '<=', curr_date)]
        if post.get('selected_utilities'):
            utility_list = ast.literal_eval(post.get('selected_utilities'))
            if isinstance(utility_list, int):
                utility_list = [utility_list]
            else:
                utility_list = list(utility_list)
            selected_utilities.extend(utility_list)
            domain += [('utility_ids.utility_id', 'in', utility_list)]
        vals.update({
            'selected_utilities': selected_utilities
        })
        if post.get('search_by_address'):
            domain += [
                '|', ('street', 'ilike', (post.get('search_by_address'))),
                '|', ('city', 'ilike', (post.get('search_by_address'))),
                '|', ('zip', '=', (post.get('search_by_address'))),
                '|', ('state_id.name', 'ilike', (post.get('search_by_address'))),
                ('country_id.name', 'ilike', (post.get('search_by_address')))
            ]
        property_rec = asset_obj.search(
            domain, order=order)
        request.cr.execute(
            "SELECT MIN(ground_rent) as min_rent, MAX(ground_rent) as max_rent FROM account_asset")
        value = request.cr.dictfetchall()[0]
        vals.update({
            'post': post,
            'my_properties': property_rec,
            'property_types': property_types,
            'utilities': utilities,
            'property_type_list': property_type_list,
            'min_value': value.get('min_rent') if value.get('min_rent') else 0,
            'max_value': value.get('max_rent') if value.get('max_rent') else 0,
#             'min_gf_mtr': value.get('min_gf_mtr') if value.get('min_gf_mtr') else 0,
#             'max_gf_mtr': value.get('max_gf_mtr') if value.get('max_gf_mtr') else 0,
#             'min_built_year': value.get('min_built_year').year if value.get('min_built_year') else 1950,
#             'max_built_year': value.get('max_built_year').year if value.get('max_built_year') else datetime.now().year
        })
        if request.env.user.partner_id:
            partner = request.env.user.partner_id
            saved_assets = partner.sudo().fav_assets_ids
            vals.update({
                'product_ids_from_cookies_list': saved_assets.ids,
            })
        return request.render('property_website.search_property_template', vals)

    @http.route(['/properties/<model("account.asset"):property>'],
                type='http', auth="public", website=True)
    def property_detail(self, property, **post):
        selected_property_id = property.id
        account_asset_obj = request.env['account.asset'].sudo().search([])
        account_asset_property_rec = account_asset_obj.browse(
            selected_property_id)

        suggested_properties_ids = \
            account_asset_property_rec.suggested_property_ids
        suggested_properties_ids_list = [
            one_id.other_property_id.id for one_id in suggested_properties_ids]
        # for one_id in suggested_properties_ids:
        #     suggested_properties_ids_list.append(one_id.other_property_id.id)
        # set_value = set(suggested_properties_ids_list)
        suggested_properties_ids_list = \
            list(set(suggested_properties_ids_list))

        suggeste_properties_obj = account_asset_obj.browse(
            suggested_properties_ids_list)

        google_maps_api_key = request.website.google_maps_api_key
        values = {
            'account_asset_property_obj': account_asset_property_rec,
            'suggeste_properties_obj': suggeste_properties_obj,
            'google_maps_api_key': google_maps_api_key,
        }

        return request.render('property_website.selected_property_onload', values)
    
    @http.route(['/favorite-properties',
                 '/favorite-properties/page/<int:page>'], type='http', auth="public", website=True)
    def all_favorite_properties(self, page=0, **post):
        PPP = 6 #property per page
        partner = request.env.user.partner_id
        saved_assets = partner.sudo().fav_assets_ids
        values = {
            'account_asset_all_sale_cookie_obj': saved_assets,
            'product_ids_from_cookies_list': saved_assets.ids,
            'page_of_saved': 'saved page',
            'facebook_share': request.env['ir.config_parameter'].get_param('property_share_kay_facebook'),
            'twitter_share': request.env['ir.config_parameter'].get_param('property_share_kay_twitter'),
        }
        return request.render('property_website.allsavedsales_onload', values)
    
    @http.route(['/update_fav_property'], type='json', auth="public", website=True)
    def update_fav_property(self, fav_property ,fav_checked=True, **kw):
        partner = request.env.user.partner_id
        saved_assets = partner.sudo().fav_assets_ids.ids
        if fav_property:
            if fav_property not in saved_assets and fav_checked:
                partner.sudo().write({'fav_assets_ids': [(4, int(fav_property))]})
            if fav_property in saved_assets and not fav_checked:
                partner.sudo().write({'fav_assets_ids': [(3, int(fav_property))]})
        return len(partner.sudo().fav_assets_ids)
    
    @http.route(['/lease-properties',
                 '/lease-properties/page/<int:page>'], type='http', auth="public", website=True)
    def all_lease_properties(self, page=0, **post):
        PPP = 9 #property per page
        partner = request.env.user.partner_id
        saved_assets = partner.sudo().fav_assets_ids
        domain = [('state', '=', 'draft')]
        values = {}
        asset_obj = request.env['account.asset']
        lease_count = asset_obj.sudo().search_count(domain)
        pager = request.website.pager(
            url='/lease-properties',
            total=lease_count,
            page=page,
            step=PPP,
            url_args=post
        )
        
        if post.get('min_range') and post.get('min_range'):
            domain += [('sale_price', '>=', post.get('min_range')),
                       ('sale_price', '<=', post.get('max_range'))]
            values.update(
                {'min_range': post.get('min_range'), 'max_range': post.get('max_range')})

        # bedroom slider domain
        values.update({'min_bead': 1, 'max_bead': 5})
        if post.get('min_bead') and post.get('max_bead'):
            values.update(
                {'min_bead': post.get('min_bead'), 'max_bead': post.get('max_bead')})
            domain += [('bedroom', '>=', post.get('min_bead')),
                       ('bedroom', '<=', post.get('max_bead'))]

        # bathroom slider domain
        values.update({'min_bath': 1, 'max_bath': 5})
        if post.get('min_bath') and post.get('max_bath'):
            values.update(
                {'min_bath': post.get('min_bath'), 'max_bath': post.get('max_bath')})
            domain += [('bathroom', '>=', post.get('min_bath')),
                       ('bathroom', '<=', post.get('max_bath'))]
        
        account_asset_lease = asset_obj.search(domain, limit=PPP,
                                               order='id desc',
                                               offset=pager['offset'])
        property_types = request.env['property.type'].sudo().search([])
        values.update({
            'pager': pager,
            'product_ids_from_cookies_list': saved_assets.ids,
            'property_types': property_types,
            'selected_property_types': [],
            'all_property_objs': account_asset_lease,
        })
        return request.render('property_website.lease_properties', values)

    _post_per_page = 8

    def common_content_lease_sale(self, post):
        if post.get('page'):
            page = post.get('page')
        else:
            page = 0
        domain = []
        values = {}
        dropdown_furnished = post.get('dropdown_furnish')
        if dropdown_furnished == 'full_furnished':
            domain += [('furnished', '=', 'full_furnished')]
            values.update({'dropdown_furnish': 'full_furnished'})
        elif dropdown_furnished == 'semi_furnished':
            domain += [('furnished', '=', 'semi_furnished')]
            values.update({'dropdown_furnish': 'semi_furnished'})
        elif dropdown_furnished == 'none':
            domain += [('furnished', '=', 'none')]
            values.update({'dropdown_furnish': 'none'})
        else:
            values.update({'dropdown_furnish': 'all'})
        

        dropdown_facing = post.get('dropdown_facing')
        if dropdown_facing == 'east':
            domain += [('facing', '=', 'east')]
            values.update({'dropdown_facing': 'east'})
        elif dropdown_facing == 'west':
            domain += [('facing', '=', 'west')]
            values.update({'dropdown_facing': 'west'})
        elif dropdown_facing == 'north':
            domain += [('facing', '=', 'north')]
            values.update({'dropdown_facing': 'north'})
        elif dropdown_facing == 'south':
            domain += [('facing', '=', 'south')]
            values.update({'dropdown_facing': 'south'})
        elif dropdown_facing == 'all':
            values.update({'dropdown_facing': 'all'})

        country_state_ids = request.env['res.country.state'].search(
            ['|',('code', 'ilike', post.get('city')),
                  ('name', 'ilike', post.get('city'))])
        country_ids = res_country = request.env['res.country'].search(
            [('name', 'ilike', post.get('city'))])

        domain += ['|','|','|','|','|','|', ('zip', 'ilike', post.get('city')),
                   ('city', 'ilike', post.get('city')),
                   ('name', 'ilike', post.get('city')),
                   ('street', 'ilike', post.get('city')),
                   ('street2', 'ilike', post.get('city')),
                   ('state_id', 'in', country_state_ids.ids),
                   ('country_id', 'in', country_ids.ids)]
        if post.get('city'):
            values.update({'city': post.get('city')})
        if post.get('state'):
            values.update({'state': post.get('state')})
            country_state_ids = request.env['res.country.state'].search(
                ['|',('code', 'ilike', post.get('state')),
                      ('name', 'ilike', post.get('state'))])
            domain += [('state_id', 'in', country_state_ids.ids)]
        if post.get('country'):
            values.update({'country': post.get('country')})
            country_ids = request.env['res.country'].search(
                [('name', 'ilike', post.get('country'))])
            domain += [('country_id', 'in', country_ids.ids)]
        if post.get('postcode'):
            domain += [('zip', 'ilike', post.get('postcode'))]
            values.update({'postcode': post.get('postcode')})

        if post.get('min_range') and post.get('max_range'):
            domain += [('ground_rent', '>=', post.get('min_range')),
                       ('ground_rent', '<=', post.get('max_range'))]
            values.update(
                {'min_range': post.get('min_range'), 'max_range': post.get('max_range')})

        # bedroom slider domain
        values.update({'min_bead': 1, 'max_bead': 5})
        if post.get('min_bead') and post.get('max_bead'):
            values.update(
                {'min_bead': post.get('min_bead'), 'max_bead': post.get('max_bead')})
            domain += [('bedroom', '>=', post.get('min_bead')),
                       ('bedroom', '<=', post.get('max_bead'))]

        # bathroom slider domain
        values.update({'min_bath': 1, 'max_bath': 5})
        if post.get('min_bath') and post.get('max_bath'):
            values.update(
                {'min_bath': post.get('min_bath'), 'max_bath': post.get('max_bath')})
            domain += [('bathroom', '>=', post.get('min_bath')),
                       ('bathroom', '<=', post.get('max_bath'))]

        property_list = []
        if post.get('selected_property_types'):
            property_list = ast.literal_eval(post.get('selected_property_types'))
            if isinstance(property_list, int):
                property_list = [property_list]
            else:
                property_list = list(property_list)
            domain += [('type_id', 'in', property_list)]

        values.update({'selected_property_types': property_list,
            'facebook_share': request.env['ir.config_parameter'].get_param('property_share_kay_facebook'),
                       'twitter_share': request.env['ir.config_parameter'].get_param('property_share_kay_twitter')})
        return {'domain': domain, 'values': values}

    @http.route(['/min_max_price'], type='json', auth='public', website=True)
    def min_max_price(self):
        asset_obj = request.env["account.asset"].sudo()
        request.cr.execute(
            "SELECT MIN(ground_rent) as min_rent, MAX(ground_rent) as max_rent FROM account_asset")
        value = request.cr.dictfetchall()[0]
        price = {
            'min_value': value.get('min_rent'),
            'max_value': value.get('max_rent'),
            'symbol': request.env.company.currency_id.symbol
        }
        return price
    
    @http.route(['/sale'], type='http', auth="public", website=True)
    def sell_properties_onload(self, **kwargs):
        account_asset_sold = request.env['account.asset'].search([(
        'state', '=', 'sold')], limit=6, order='write_date desc')
        countries = request.env['res.country'].search([])
        partner = request.env.user.partner_id
        saved_assets = partner.sudo().fav_assets_ids
        
        vals= {
            'countries': countries,
            'all_property_objs': account_asset_sold,
            'product_ids_from_cookies_list': saved_assets.ids,
            'facebook_share': request.env['ir.config_parameter'].get_param('property_share_kay_facebook'),
            'twitter_share': request.env['ir.config_parameter'].get_param('property_share_kay_twitter'),
        }
        return request.render("property_website.sell_properties", vals)

    @http.route(['/post-property'], type='http', auth="public", website=True)
    def post_property(self, **post):
        property_types = request.env['property.type'].sudo().search([])
        vals = {'property_types': property_types,
                'submited': False}
        if post:
            post.update({'name': 'Request for post property',
                         'type_id': int(post.get('type_id'))})
            lead = request.env['crm.lead'].create(post)
            if lead:
                vals.update({'submited': True})
        return request.render("property_website.post_properties", vals)

    @http.route(['/contactus/create_lead'], type='json', auth="public", website=True)
    def crmcontactus(self, **kwargs):
#         if kwargs.get('value_from') == 'Sales page':
#             return request.env['crm.lead'].sudo().create({
#                 'name': 'Request for property sale',
#                 'contact_name': kwargs.get('contact_name'),
#                 'phone': kwargs.get('phone'),
#                 'email_from': kwargs.get('email_from'),
#                 'street': kwargs.get('address'),
#                 'city': kwargs.get('city'),
#                 'zip': kwargs.get('zip'),
#                 'country_id': int(kwargs.get('country_id')),
#                 'user_id': False,
#             }).id

        if kwargs.get('value_from') == 'Property page':
            property = request.env['account.asset'].browse(
                int(kwargs.get('asset')))
            inquiry = ' '
            if kwargs.get('asset'):
                if property.property_sale_rent == 'sale':
                    val = 'Sale'
                else:
                    val = 'Rent'
                inquiry = 'Inquiry of ' + str(property.name) + ' for ' + val
            user = request.env['res.users'].sudo().search(
                [('partner_id', '=', property.property_manager.id)])
            return request.env['crm.lead'].create({
                'name': inquiry or ' ',
                'contact_name': kwargs.get('contact_name'),
                'email_from': kwargs.get('email_from'),
                'phone': kwargs.get('phone'),
                'phone_type': kwargs.get('telType'),
                'when_to_call': kwargs.get('telTime'),
                'description': kwargs.get('msg'),
                'property_id': kwargs.get('asset'),
                'user_id': user and user.id or False,
            })
    
    @http.route(['/my_properties'], type='http', auth="user", website=True)
    def my_properties_http(self, **post):
        res_user_browse = request.env['res.users'].browse(request.uid)
        vals = {}
        if res_user_browse.tenant_id:
            date_today = datetime.now().date()
            date_today = datetime.strftime(date_today, '%m/%d/%Y')
            tenant_browse = request.env['account.analytic.account'].sudo().search(
                [('tenant_id', '=', res_user_browse.tenant_id.id), ('date_start', '<=', date_today),
                 ('date', '>=', date_today)])

            my_property_list = []
            for one_tenant in tenant_browse:
                my_property_list.append(one_tenant.property_id.id)
            all_property_objs = request.env[
                'account.asset'].sudo().browse(my_property_list)
            vals.update({
                'all_property_objs': all_property_objs,
                'product_ids_from_cookies_list': get_cookie_list(),
                'facebook_share': request.env['ir.config_parameter'].get_param('property_share_kay_facebook'),
                'twitter_share': request.env['ir.config_parameter'].get_param('property_share_kay_twitter'),
            })

        return request.render("property_website.my_properties_onload", vals)

    @http.route(['/create_maintanance'], type='json', auth="public", website=True)
    def create_maintanance(self, **post):

        return request.env['maintenance.request'].create({
            'name': post.get('maint_req'),
            'property_id': post.get('property_id'),
            'maintenance_team_id': int(post.get('type_id')),
            'description': post.get('description'),
            'renters_fault': post.get('renters_fault'),

        })

