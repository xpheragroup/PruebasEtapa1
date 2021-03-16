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

    add_product_id = fields.Many2many(
        'product.product', string='Productos Adicionales',
        domain="[('bom_ids', '!=', False), ('bom_ids.active', '=', True), ('bom_ids.type', '=', 'normal'), ('type', 'in', ['product', 'consu']), '|', ('company_id', '=', False), ('company_id', '=', company_id)]",
        readonly=True, check_company=True,
        states={'draft': [('readonly', False)]})
    add_bom_id = fields.Many2many(
        'mrp.bom', string='Lista de materiales de productos adicionales',
        readonly=True, states={'draft': [('readonly', False)]},
        domain="""[
        '&',
            '|',
                ('company_id', '=', False),
                ('company_id', '=', company_id),
            '&',
                '|',
                    ('product_id','=',add_product_id),
                    '&',
                        ('product_tmpl_id.product_variant_ids','=',add_product_id),
                        ('product_id','=',False),
        ('type', '=', 'normal')]""",
        check_company=True,
        help="Permite agregar las listas de materiales de los productos adicionales a la orden de producción.")

    @api.depends('move_raw_ids.std_quantity', 'move_raw_ids.product_id.standard_price')
    def _compute_std_cost(self):
        """ Calcula el costo estándar a partir de los productos presentes en 'move_raw_ids'. """
        for record in self:
            std_cost = sum(product.std_quantity * product.product_id.standard_price for product in record.move_raw_ids)
            record.total_std_cost = std_cost
            

    @api.depends('move_raw_ids.product_id', 'move_raw_ids.product_id.standard_price')
    def _compute_real_cost(self):
        """ Calcula el costo real a partir de los productos presentes en 'move_raw_ids' y las cantidades digitadas por el usuario. """
        for record in self:
            real_cost = sum(product.product_uom_qty * product.product_id.standard_price for product in record.move_raw_ids)
            record.total_real_cost = real_cost

    
    def _get_moves_raw_values(self):
        """ @Overwrite: Obtiene los ingredietes de un producto una vez es selccionado.
        En lugar de extraer los productos en la lista de materiales se dirige a sus listas hijas
        'child_line_ids' para poblar la lista de productos

        returns:
        list<stock.move> -- Lista de productos asociados a la orden de producción

        """
        moves = []
        for production in self:
            factor = production.product_uom_id._compute_quantity(production.product_qty, production.bom_id.product_uom_id) / production.bom_id.product_qty
            boms, lines = production.bom_id.explode(production.product_id, factor, picking_type=production.bom_id.picking_type_id)
            if production.add_bom_id:
                for add_pro in production.add_bom_id:
                    factor2 = production.product_uom_id._compute_quantity(production.product_qty, add_pro.product_uom_id) / add_pro.product_qty
                    boms2, lines2 = add_pro.explode(production.product_id, factor2, picking_type=add_pro.picking_type_id)
                    boms += boms2
                    lines += lines2
            
            for bom_line, line_data in lines:
                if bom_line.child_bom_id and bom_line.child_bom_id.type == 'phantom' or\
                        bom_line.product_id.type not in ['product', 'consu']:
                    continue
                
                for p in bom_line.child_line_ids:
                    moves.append(production._get_move_raw_values(p, {'qty': p.product_qty * self.product_uom_qty, 'parent_line': ''})) 
                
                if len(bom_line.child_line_ids) == 0:
                    moves.append(production._get_move_raw_values(bom_line, line_data))

        return moves