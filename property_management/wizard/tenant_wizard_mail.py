# See LICENSE file for full copyright and licensing details

import datetime

from odoo import tools
from odoo import api, models
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT


class TenantWizardMail(models.TransientModel):
    _name = "tenant.wizard.mail"
    _description = "Mass Mailing"

    def mass_mail_send(self):
        """
        This method is used to sending mass mailing to tenant
        for Reminder for rent payment
        """
        partner_pool = self.env['tenancy.rent.schedule']
        active_ids = partner_pool.search(
            [('start_date', '<', datetime.date.today().strftime(
                DEFAULT_SERVER_DATE_FORMAT))])
        for partner in active_ids:
            if partner.rel_tenant_id.parent_id:
                if partner.rel_tenant_id.parent_id[0].email:
                    to = '"%s" <%s>' % (
                        partner.rel_tenant_id.name,
                        partner.rel_tenant_id.parent_id[0].email)
        # TODO(email): add some tests to check for invalid email addresses
        # CHECKME: maybe we should use res.partner/email_send
                    tools.email_send(tools.config.get('email_from', False),
                                     [to],
                                     'Reminder for rent payment',
                                     '''Hello Mr %s,\n
                                     Your rent QAR %d of %s is unpaid so \
                                     kindly pay as soon as possible.
                                     \n
                                     Regards,
                                     Administrator.
                                     Property management firm.
                                     ''' % (
                                        partner.rel_tenant_id.name,
                                        partner.amount, partner.start_date))
        return {'type': 'ir.actions.act_window_close'}
