import datetime
from collections import defaultdict
from itertools import groupby

from odoo import api, fields, models, _
from odoo.exceptions import AccessError, UserError
from odoo.tools import date_utils, float_compare, float_round, float_is_zero

class Override_Bom_Production(models.Model):
    _inherit = 'mrp.production'

    # TODO: Crear nuevo modelo y relacion 1-M (account.analytic.account)
    cost_center = fields.Char(string='Centro de Costos')
    cycle = fields.Integer(string='Ciclo')
    reference = fields.Char(string='Reference')
    #TODO: computed
    total_real_cost = fields.Float(string='Costo total real receta')
    #TODO: computed
    total_std_cost = fields.Float(string='Costo total estándar receta')

    #TODO: esto va en mrp.bom?
    std_quantity = fields.Float(string='Cantidad Estándar')
    #TODO: 1-M
    und_std = fields.Char(string='Unidad de Medida')
    real_quantity = fields.Float(string='Cantidad Estándar')
    
    #TODO: calculated
    deviation = fields.Float(string='Desviación')
    deviation_per = fields.Float(string='Desviación %')
