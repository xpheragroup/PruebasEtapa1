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
            record.total_std_cost = std_cost
            

    @api.depends('move_raw_ids.product_id')
    def _compute_real_cost(self):
        for record in self:
            real_cost = sum(product.product_uom_qty * product.product_id.standard_price for product in record.move_raw_ids)
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
                
                for p in bom_line.child_line_ids:
                    moves.append(production._get_move_raw_values(p, {'qty': p.product_qty * self.product_uom_qty, 'parent_line': ''})) 
                
                if len(bom_line.child_line_ids) == 0:
                    moves.append(production._get_move_raw_values(bom_line, line_data))
        return moves
    
    def _get_move_raw_values(self, bom_line, line_data):
        data = super()._get_move_raw_values(bom_line, line_data)
        data['std_quantity'] = bom_line.product_qty * self.product_uom_qty
        return data

    @api.model
    def create(self, values):
        if not values.get('name', False) or values['name'] == _('New'):
            picking_type_id = values.get('picking_type_id') or self._get_default_picking_type()
            picking_type_id = self.env['stock.picking.type'].browse(picking_type_id)
            if picking_type_id:
                values['name'] = picking_type_id.sequence_id.next_by_id()
            else:
                values['name'] = self.env['ir.sequence'].next_by_code('mrp.production') or _('New')
        if not values.get('procurement_group_id'):
            procurement_group_vals = self._prepare_procurement_group_vals(values)
            values['procurement_group_id'] = self.env["procurement.group"].create(procurement_group_vals).id
        production = super().create(values)
        for e in production.move_raw_ids:
            e.write({
                'group_id': production.procurement_group_id.id,
                'reference': production.name,  # set reference when MO name is different than 'New'
                'std_quantity': e.bom_line_id.product_qty * production.product_uom_qty
            })
        # Trigger move_raw creation when importing a file
        if 'import_file' in self.env.context:
            production._onchange_move_raw()
        return production

    
    def _update_raw_move(self, bom_line, line_data):
        """ :returns update_move, old_quantity, new_quantity """
        quantity = line_data['qty']
        self.ensure_one()
        move = self.move_raw_ids.filtered(lambda x: x.bom_line_id.id == bom_line.id and x.state not in ('done', 'cancel'))
        if move:
            old_qty = move[0].product_uom_qty
            remaining_qty = move[0].raw_material_production_id.product_qty - move[0].raw_material_production_id.qty_produced
            if quantity > 0:
                move[0].write({'product_uom_qty': quantity, 'std_quantity': quantity * move.bom_line_id.product_qty})
                move[0]._recompute_state()
                move[0]._action_assign()
                move[0].unit_factor = remaining_qty and (quantity - move[0].quantity_done) / remaining_qty or 1.0
                return move[0], old_qty, quantity
            else:
                if move[0].quantity_done > 0:
                    raise UserError(_('Lines need to be deleted, but can not as you still have some quantities to consume in them. '))
                move[0]._action_cancel()
                move[0].unlink()
                return self.env['stock.move'], old_qty, quantity
        else:
            move_values = self._get_move_raw_values(bom_line, line_data)
            move_values['state'] = 'confirmed'
            move = self.env['stock.move'].create(move_values)
            return move, 0, quantity
