# See LICENSE file for full copyright and licensing details
import odoo
from odoo.http import request
from odoo import http, SUPERUSER_ID
from odoo.tools.translate import _
from odoo.addons.web.controllers.main import ensure_db


db_list = http.db_list
db_monodb = http.request.db


def db_info():
    version_info = odoo.service.common.exp_version()
    return {
        'server_version': version_info.get('server_version'),
        'server_version_info': version_info.get('server_version_info'),
    }


class PropertyManagementLogin(odoo.addons.web.controllers.main.Home):

    @http.route()
    def web_login(self, redirect=None, *args, **kw):
        ensure_db()
        request.params['login_success'] = False
        response = super(PropertyManagementLogin, self).web_login(*args, **kw)
        response.qcontext.update(self.get_auth_signup_config())
        
        if request.httprequest.method == 'GET' and request.session.uid and request.params.get('redirect'):
            # Redirect if already logged in and redirect param is present
            return http.redirect_with_hash(request.params.get('redirect'))

        if not request.uid:
            request.uid = odoo.SUPERUSER_ID

        values = request.params.copy()
        try:
            values['databases'] = http.db_list()
        except odoo.exceptions.AccessDenied:
            values['databases'] = None

        if request.httprequest.method == 'POST':
            old_uid = request.uid
            try:
                uid = request.session.authenticate(request.session.db, request.params['login'], request.params['password'])
                request.params['login_success'] = True
                if uid is not False:
                    # code for add from cookie property ids
                    product_ids_from_cookies = request.httprequest.cookies.get(
                        'property_id')
                    product_ids_from_cookies_str = str(product_ids_from_cookies)
                    product_ids_from_cookies_list = product_ids_from_cookies_str.split(
                        ',')
                    account_asset_cookie_ids = []
                    if product_ids_from_cookies_list[0] == 'None':
                        account_asset_cookie_ids = []
                    else:
                        for one_prod_cookie_id in product_ids_from_cookies_list:
                            if not one_prod_cookie_id:
                                continue
                            one_cookie_int_id = int(one_prod_cookie_id)
                            account_asset_cookie_ids.append(one_cookie_int_id)
                    user_obj = request.env['res.users']
                    partner_obj = request.env['res.partner']
                    user = user_obj.browse(int(uid))
                    account_asset_frvorite_property_ids = []
                    if user and user.partner_id:
                        for one_asset_id in user.partner_id.fav_assets_ids:
                                account_asset_frvorite_property_ids.append(
                                    one_asset_id.id)
                        properties_for_save = [
                        x for x in account_asset_cookie_ids if x not in account_asset_frvorite_property_ids]
                        if properties_for_save:
                            for one_property_save in properties_for_save:
                                selected_property = user.partner_id.write(
                                    {'fav_assets_ids': [(4, int(one_property_save))]})
     
                    # code for redicet homepage when
                    backend_users_ids = request.env.ref(
                        'property_website.group_property_website_backend').sudo().users.ids
                    if uid not in backend_users_ids:
                        if uid == SUPERUSER_ID:
                            pass
                        else:
                            return request.redirect('/')
                return http.redirect_with_hash(self._login_redirect(uid, redirect=redirect))
            except odoo.exceptions.AccessDenied as e:
                request.uid = old_uid
                if e.args == odoo.exceptions.AccessDenied().args:
                    values['error'] = _("Wrong login/password")
                else:
                    values['error'] = e.args[0]
        else:
            if 'error' in request.params and request.params.get('error') == 'access':
                values['error'] = _('Only employee can access this database. Please contact the administrator.')

        if 'login' not in values and request.session.get('auth_login'):
            values['login'] = request.session.get('auth_login')

        if not odoo.tools.config['list_db']:
            values['disable_database_manager'] = True

        # response = request.render('web.login', values)
        response.headers['X-Frame-Options'] = 'DENY'
        return response
