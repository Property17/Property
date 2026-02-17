# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import AccessError, UserError, ValidationError
import logging
_logger = logging.getLogger(__name__)


class RequestType(models.Model):
    
    _name = 'request.type'
    _rec = "name"
    _order = "id desc"
    _description ="Request Type"
    
    name = fields.Char('Name')

    
class CaseType(models.Model):
    
    _name = 'case.type'
    _rec = "name"
    _order = "id desc"
    _description ="Case Type"
    
    name = fields.Char('Name')


class LawyerOffice(models.Model):
    
    _name = 'lawyer.office'
    _rec = "name"
    _order = "id desc"
    _description ="Lawyer Office"
    
    name = fields.Char('Name')

