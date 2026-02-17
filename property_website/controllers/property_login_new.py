# See LICENSE file for full copyright and licensing details
import odoo
from odoo import http, SUPERUSER_ID, _
from odoo.http import request
from odoo.addons.web.controllers.main import ensure_db


def get_db_info():
    """Retrieve Odoo server version information."""
    version_info = odoo.service.common.exp_version()
    return {
        'server_version': version_info.get('server_version'),
        'server_version_info': version_info.get('server_version_info'),
    }


class PropertyManagementLogin(odoo.addons.web.controllers.main.Home):
    """Custom login controller for property management."""

    @http.route()
    def web_login(self, redirect=None, **kw):
        ensure_db()
        request.params['login_success'] = False

        # Call the original web_login method from the parent class
        response = super(PropertyManagementLogin, self).web_login(redirect=redirect, **kw)
        response.qcontext.update(self.get_auth_signup_config())

        # Handle redirect if already logged in and a redirect parameter exists
        if request.httprequest.method == 'GET' and request.session.uid and request.params.get('redirect'):
            return http.redirect_with_hash(request.params['redirect'])

        if not request.uid:
            request.uid = SUPERUSER_ID

        values = request.params.copy()
        try:
            # Access the database list only within the request context
            values['databases'] = http.db_list()
        except odoo.exceptions.AccessDenied:
            values['databases'] = None

        if request.httprequest.method == 'POST':
            old_uid = request.uid
            try:
                uid = request.session.authenticate(
                    request.session.db, request.params['login'], request.params['password']
                )
                request.params['login_success'] = True

                if uid:
                    self._handle_property_cookies(uid)
                    backend_user_ids = request.env.ref(
                        'property_website.group_property_website_backend'
                    ).sudo().users.ids

                    if uid not in backend_user_ids and uid != SUPERUSER_ID:
                        return request.redirect('/')

                    return http.redirect_with_hash(self._login_redirect(uid, redirect=redirect))
            except odoo.exceptions.AccessDenied as e:
                request.uid = old_uid
                values['error'] = _("Wrong login/password") if e.args == odoo.exceptions.AccessDenied().args else e.args[0]
        else:
            if request.params.get('error') == 'access':
                values['error'] = _('Only employees can access this database. Please contact the administrator.')

        if not odoo.tools.config['list_db']:
            values['disable_database_manager'] = True

        if 'login' not in values and request.session.get('auth_login'):
            values['login'] = request.session.get('auth_login')

        response.headers['X-Frame-Options'] = 'DENY'
        return response

    def _handle_property_cookies(self, uid):
        """Handle favorite properties from cookies."""
        product_ids_from_cookies = request.httprequest.cookies.get('property_id', '')
        cookie_property_ids = [
            int(pid) for pid in product_ids_from_cookies.split(',') if pid and pid != 'None'
        ]

        user = request.env['res.users'].browse(uid)

        if user.partner_id:
            existing_property_ids = user.partner_id.fav_assets_ids.ids
            new_properties = [
                prop_id for prop_id in cookie_property_ids if prop_id not in existing_property_ids
            ]

            if new_properties:
                user.partner_id.write({'fav_assets_ids': [(4, pid) for pid in new_properties]})
