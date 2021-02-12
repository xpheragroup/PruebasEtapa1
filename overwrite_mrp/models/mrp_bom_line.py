from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools import float_round, float_compare

from itertools import groupby

class Override_Bom_Line(models.Model):
    _inherit = 'mrp.bom.line'

    # TODO: Crear nuevo modelo y relacion 1-M
    food_group = fields.Char(string='Grupo de Alimentos')


