import datetime
from collections import defaultdict
from itertools import groupby

from odoo import api, fields, models, _
from odoo.exceptions import AccessError, UserError
from odoo.tools import date_utils, float_compare, float_round, float_is_zero

class Override_Bom_Production(models.Model):
    _inherit = 'mrp.production'

    cost_center = fields.Many2one(
        string="Centro de Costos",
        comodel_name='account.analytic.account')

    cycle = fields.Integer(string='Ciclo')
    reference = fields.Char(string='Referencia')
    total_real_cost = fields.Float(string='Costo total real receta', compute='_compute_real_cost')
    total_std_cost = fields.Float(string='Costo total estándar receta', compute='_compute_std_cost')

    @api.depends('move_raw_ids.product_id')
    def _compute_std_cost(self):
        for record in self:
            std_cost = sum(product.std_quantity * product.product_id.standard_price for product in record.move_raw_ids)
            record.total_std_cost = std_cost * self.product_qty

    @api.depends('move_raw_ids.product_id')
    def _compute_real_cost(self):
        for record in self:
            real_cost = sum(product.product_qty * product.product_id.standard_price for product in record.move_raw_ids)
            record.total_real_cost = real_cost

    
    def _get_moves_raw_values(self):
        moves = []
        for production in self:
            factor = production.product_uom_id._compute_quantity(production.product_qty, production.bom_id.product_uom_id) / production.bom_id.product_qty
            boms, lines = production.bom_id.explode(production.product_id, factor, picking_type=production.bom_id.picking_type_id)
            for bom_line, line_data in lines:
                if bom_line.child_bom_id and bom_line.child_bom_id.type == 'phantom' or\
                        bom_line.product_id.type not in ['product', 'consu']:
                    continue
                #moves.append(production._get_move_raw_values(bom_line, line_data))
                for p in bom_line.child_line_ids:
                    moves.append(production._get_move_raw_values(p, {'qty': p.product_qty, 'parent_line': ''})) 
        return moves
    
    def _get_move_raw_values(self, bom_line, line_data):
        data = super()._get_move_raw_values(bom_line, line_data)
        data['std_quantity'] = bom_line.product_qty * self.product_qty
        return data
