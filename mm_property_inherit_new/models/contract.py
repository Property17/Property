from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from datetime import datetime
from dateutil.relativedelta import relativedelta
import locale


class PropertyContractTemplateNew(models.Model):
    _name = "property.contract.template"
    _description = "Property Contract Template"
    _rec_name = 'temp_id'

    tenancy_id = fields.Many2one('account.analytic.account', 'Tenancy')
    temp_id = fields.Many2one('contract.template', 'Temp id')
    temp = fields.Html(string='Temp')

    @api.onchange('temp_id', 'tenancy_id')
    def _onchange_temp_id(self):
        for rec in self:
            message_string = ""
            bedroom = ""
            bathroom = ""
            parking = ""
            property_street = ""
            property_street2 = ""
            property_city = ""
            property_country_name = ""
            tenant_id_street = ""
            tenant_id_street2 = ""
            tenant_id_city = ""
            tenant_id_country = ""

            company_street = ""
            company_street2 = ""
            company_city = ""
            company_country = ""
            if rec.temp_id:
                message_string = rec.temp_id.temp
                if rec.tenancy_id.property_id.bedroom:
                    bedroom = rec.tenancy_id.property_id.bedroom
                if rec.tenancy_id.property_id.bathroom:
                    bathroom = rec.tenancy_id.property_id.bathroom
                if rec.tenancy_id.property_id.parking:
                    parking = rec.tenancy_id.property_id.parking
                if rec.tenancy_id.property_id.street:
                    property_street = rec.tenancy_id.property_id.street
                if rec.tenancy_id.property_id.street2:
                    property_street2 = rec.tenancy_id.property_id.street2
                if rec.tenancy_id.property_id.city:
                    property_city = rec.tenancy_id.property_id.city
                if rec.tenancy_id.property_id.country_id.name:
                    property_country_name = rec.tenancy_id.property_id.country_id.name

                if rec.tenancy_id.tenant_id.street:
                    tenant_id_street = rec.tenancy_id.tenant_id.street
                if rec.tenancy_id.tenant_id.street2:
                    tenant_id_street = rec.tenancy_id.tenant_id.street2
                if rec.tenancy_id.tenant_id.city:
                    tenant_id_city = rec.tenancy_id.tenant_id.city
                if rec.tenancy_id.tenant_id.country_id.name:
                    tenant_id_country = rec.tenancy_id.tenant_id.country_id.name

                if rec.tenancy_id.company_id.street:
                    company_street = rec.tenancy_id.company_id.street
                if rec.tenancy_id.company_id.street2:
                    company_street = rec.tenancy_id.company_id.street2
                if rec.tenancy_id.company_id.city:
                    company_city = rec.tenancy_id.company_id.city
                if rec.tenancy_id.company_id.country_id.name:
                    company_country = rec.tenancy_id.company_id.country_id.name

                if rec.tenancy_id.code:
                    message_string = message_string.replace('{tenancy_number}', str(rec.tenancy_id.code))
                if rec.tenancy_id.property_id.name:
                    message_string = message_string.replace('{property_name}', str(rec.tenancy_id.property_id.name))
                if rec.tenancy_id.property_id.auto_add_no:
                    message_string = message_string.replace('{auto_add_no}', str(rec.tenancy_id.property_id.auto_add_no))
                if rec.tenancy_id.property_id.parent_id.name:
                    message_string = message_string.replace('{parent_name}', str(rec.tenancy_id.property_id.parent_id.name))
                if rec.tenancy_id.property_manager_id.name:
                    message_string = message_string.replace('{property_manager}', str(rec.tenancy_id.property_manager_id.name))
                if rec.tenancy_id.property_manager_id.phone:
                    message_string = message_string.replace('{property_manager_phone}', str(rec.tenancy_id.property_manager_id.phone))
                if rec.tenancy_id.company_id.name:
                    message_string = message_string.replace('{company_name}', str(rec.tenancy_id.company_id.name))
                message_string = message_string.replace('{company_address}', str(company_street+' - '+ company_street2 + ' - '+ company_city + ' - ' + company_country))

                if rec.tenancy_id.tenant_id.name:
                    message_string = message_string.replace('{tenant_name}', str(rec.tenancy_id.tenant_id.name))
                if rec.tenancy_id.tenant_id.email:
                    message_string = message_string.replace('{tenant_email}', str(rec.tenancy_id.tenant_id.email))
                if rec.tenancy_id.tenant_id.name2:
                    message_string = message_string.replace('{tenant_name2}', str(rec.tenancy_id.tenant_id.name2))
                if rec.tenancy_id.tenant_id.civil_number2:
                    message_string = message_string.replace('{civil_number2}', str(rec.tenancy_id.tenant_id.civil_number2))
                if rec.tenancy_id.tenant_id.country_id2.name:
                    message_string = message_string.replace('{country_id2}', str(rec.tenancy_id.tenant_id.country_id2.name))
                if rec.tenancy_id.tenant_id.notes2:
                    message_string = message_string.replace('{notes2}', str(rec.tenancy_id.tenant_id.notes2))
                if rec.tenancy_id.tenant_id.name3:
                    message_string = message_string.replace('{tenant_name3}', str(rec.tenancy_id.tenant_id.name3))
                if rec.tenancy_id.tenant_id.civil_number3:
                    message_string = message_string.replace('{civil_number3}', str(rec.tenancy_id.tenant_id.civil_number3))
                if rec.tenancy_id.tenant_id.country_id3.name:
                    message_string = message_string.replace('{country_id3}', str(rec.tenancy_id.tenant_id.country_id3.name))
                if rec.tenancy_id.tenant_id.notes3:
                    message_string = message_string.replace('{notes3}', str(rec.tenancy_id.tenant_id.notes3))
                if rec.tenancy_id.tenant_id.country_id.name:
                    message_string = message_string.replace('{national}', str(rec.tenancy_id.tenant_id.country_id.name))
                if rec.tenancy_id.tenant_id.civil_number:
                    message_string = message_string.replace('{civil_no}', str(rec.tenancy_id.tenant_id.civil_number))
                if rec.tenancy_id.tenant_id.mobile:
                    message_string = message_string.replace('{mobile}', str(rec.tenancy_id.tenant_id.mobile))
                if rec.tenancy_id.tenant_id.phone:
                    message_string = message_string.replace('{phone}', str(rec.tenancy_id.tenant_id.phone))
                if rec.tenancy_id.tenant_id.work_address:
                    message_string = message_string.replace('{work_address}', str(rec.tenancy_id.tenant_id.work_address))
                # if rec.tenancy_id.tenant_id.street
                message_string = message_string.replace('{address}', str(tenant_id_street+' - '+ tenant_id_street2 + ' - '+ tenant_id_city + ' - ' + tenant_id_country))
                if rec.tenancy_id.property_id.name:
                    message_string = message_string.replace('{unit_name}', str(rec.tenancy_id.property_id.name))
                # if property_street
                message_string = message_string.replace('{prop_no}', str(property_street+' - '+ property_street2 + ' - '+ property_city + ' - ' + property_country_name))
                if rec.tenancy_id.activity_type_lo_id.name:
                    message_string = message_string.replace('{activity_type}', str(rec.tenancy_id.activity_type_lo_id.name))
                # if bedroom
                message_string = message_string.replace('{prop_info}', str(bedroom + "Bedrooms /" + bathroom + "Bathrooms /" + parking + "Parking"))
                if rec.tenancy_id.rent:
                    message_string = message_string.replace('{rent}', str(rec.tenancy_id.rent))
                if rec.tenancy_id.rent:
                    message_string = message_string.replace('{text_amount}', str(rec.tenancy_id.amount_text_arabic(rec.tenancy_id.rent)))
                if rec.tenancy_id.total_rent:
                    message_string = message_string.replace('{total_rent}', str(rec.tenancy_id.rent * 12))
                if rec.tenancy_id.rent:
                    message_string = message_string.replace('{total_text_amount}', str(rec.tenancy_id.amount_text_arabic(rec.tenancy_id.rent * 12)))
                if rec.tenancy_id.date_start:
                    message_string = message_string.replace('{start_date}', str(rec.tenancy_id.date_start))
                if rec.tenancy_id.date:
                    message_string = message_string.replace('{end_date}', str(rec.tenancy_id.date_start + relativedelta(years=1) - relativedelta(days=1) ))
                if rec.tenancy_id.deposit:
                    message_string = message_string.replace('{deposit}', str(rec.tenancy_id.deposit))
                if rec.tenancy_id.deposit:
                    message_string = message_string.replace('{text_deposit}', str(rec.tenancy_id.amount_text_arabic(rec.tenancy_id.deposit)))
                date_today = fields.Date.today()
                date_name = date_today.strftime('%A')
                today_date_name = ''
                if date_name == 'Monday':
                    today_date_name = 'الاتنين'
                if date_name == 'Tuesday':
                    today_date_name = 'الثلاثاء'
                if date_name == 'Wednesday':
                    today_date_name = 'الاربعاء'
                if date_name == 'Thursday':
                    today_date_name = 'الخميس'
                if date_name == 'Friday':
                    today_date_name = 'الجمعة'
                if date_name == 'Saturday':
                    today_date_name = 'السبت'
                if date_name == 'Sunday':
                    today_date_name = 'الحد'

                message_string = message_string.replace('{today_date}', str(fields.Date.today()))
                message_string = message_string.replace('{today_date_name}', today_date_name)
                if rec.tenancy_id.close_date:
                    message_string = message_string.replace('{close_date}', str(rec.tenancy_id.close_date))



                rec.temp = message_string