import datetime
from collections import defaultdict
from itertools import groupby

from odoo import api, fields, models, _
from odoo.exceptions import AccessError, UserError
from odoo.tools import date_utils, float_compare, float_round, float_is_zero


class MrpProduction(models.Model):
    """ Manufacturing Orders """
    _inherit = 'mrp.production'

    parent_id = fields.Many2one(comodel_name='mrp.production')
    children_ids = fields.One2many(comodel_name='mrp.production', inverse_name='parent_id')

    @api.model
    def create(self, values):
        if values.get('origin', False):
            parent = self.env['mrp.production'].search([['name', '=', values['origin']]])
            if parent:
                prods = self.env['mrp.production'].search([['name', 'like', values['origin'] + '.']])
                if len(prods) == 0:
                    index = '0'
                else:
                    index = max(list(map(lambda prod: prod.name.split('.')[-1], prods)))
                values['name'] = parent.name + '.' + str(int(index) + 1)
                values['parent_id'] = parent.id
        
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
        production = super(MrpProduction, self).create(values)

        if values.get('origin', False):
            parent = self.env['mrp.production'].search([['name', '=', values['origin']]])
            if parent:
                parent.children_ids = production.id
        
        production.move_raw_ids.write({
            'group_id': production.procurement_group_id.id,
            'reference': production.name,  # set reference when MO name is different than 'New'
        })
        # Trigger move_raw creation when importing a file
        if 'import_file' in self.env.context:
            production._onchange_move_raw()
        return production