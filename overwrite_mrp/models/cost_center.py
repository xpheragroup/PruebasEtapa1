from odoo import api, fields, models

class CostCenter(models.Model):

    _name = 'overwrite_mrp.cost_center'
    _description = 'Cost Center'

    name = fields.Char(string='Nombre')
