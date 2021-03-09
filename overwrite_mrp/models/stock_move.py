from datetime import datetime
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools import float_round, float_compare

from itertools import groupby

class Override_StockMove(models.Model):
    _inherit = 'stock.move'

    fab_product = fields.Many2one('product.product', string='Preparación', readonly=True, check_company=True,
        compute='_compute_custom_values')
    std_quantity = fields.Float(string='Cantidad estándar', readonly=True, digits=(12,4), compute='_compute_custom_values')
    missing = fields.Float(string='Cantidad Faltante', readonly=True, digits=(12,4), compute='_compute_custom_values')
    deviation = fields.Float(string='Desviación', compute='_compute_custom_values', digits=(12,4))
    deviation_per = fields.Float(string='Desviación Porcentual', compute='_compute_custom_values')
    real_cost = fields.Float(string='Costo real', compute='_compute_custom_values', digits=(12,4))
    std_cost = fields.Float(string='Costo estándar', compute='_compute_custom_values', digits=(12,4))

    @api.depends('std_quantity', 'product_qty', 'product_id.standard_price', 'product_uom_qty', 'reserved_availability', 'product_id.qty_available')
    def _compute_custom_values(self):
        """ Calcula los campos añadidos al modelo cruzando información ya existente. 
        fab_product: product.product    - Producto padre del cual proviene el ingrediente
        std_quantity: float             - Cantidad de productos a fabricar x cantidad en la lista de materiales
        missing: float                  - Cantidad necesitada de producto - cantidad reservada
        deviation: float                - Cantidad en que difiere la cantidad digitada de la estándar en la receta
        deviation_per: float            - Razon de la diferencia entre las cantidades digitadas y estandar
        real_cost: float                - Valor total del producto x cantidad digitada
        std_cost: float                 - Valor total del producto x cantidad estándar

        """
        for record in self:
            record.fab_product = record.bom_line_id.bom_id.product_id
            record.std_quantity = record.raw_material_production_id.product_uom_qty * record.bom_line_id.product_qty
            record.missing = record.product_uom_qty - record.reserved_availability
            record.deviation = record.product_uom_qty - record.std_quantity
            record.deviation_per = record.deviation / record.std_quantity if record.std_quantity > 0 else 1
            record.real_cost = record.product_uom_qty * record.product_id.standard_price
            record.std_cost = record.std_quantity * record.product_id.standard_price
