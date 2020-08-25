# -*- coding: utf-8 -*-

from odoo import models, fields, api


class duplicate_change(models.Model):
    _name = 'purchase.order'
    _inherit = 'purchase.order'

    def copy(self, default=None):
        default = dict(default or {})
        default.update({
            'user_id': self._uid,
        })
        return super(duplicate_change, self).copy(default)

class duplicate_change(models.Model):
    _name = 'purchase.requisition'
    _inherit = 'purchase.requisition'

    def copy(self, default=None):
        default = dict(default or {})
        default.update({
            'user_id': self._uid,
        })
        return super(duplicate_change, self).copy(default)