# -*- coding: utf-8 -*-
import datetime
from odoo import models

class PurchaseRequisition(models.Model):
    _inherit = 'purchase.requisition'                       # Inherit purchase requisition

    def copy(self, default=None):                           # Redefininf copy funcion
        default = dict(default or {})
        default.update({
            'user_id': self._uid,                           # Getting current user on copy action
        })
        return super(PurchaseRequisition, self).copy(default)