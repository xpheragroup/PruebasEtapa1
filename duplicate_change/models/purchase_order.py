# -*- coding: utf-8 -*-
import datetime
from odoo import models

class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'                                             # Inherit Purchase Requisition

    def copy(self, default=None):                                           # Redefininf copy funcion
        default = dict(default or {})
        default.update({
            'user_id': self._uid,                                           # Getting current user on copy action
            'date_planned': datetime.datetime(year=2220, month=1, day=1)    # Setting planned date to far future to avoid errors
        })  
        return super(PurchaseOrder, self).copy(default)