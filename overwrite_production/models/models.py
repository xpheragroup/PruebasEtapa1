import json
import datetime
from collections import defaultdict
from itertools import groupby

from odoo import api, fields, models, _
from odoo.exceptions import AccessError, UserError
from odoo.tools import date_utils, float_compare, float_round, float_is_zero

class ReportBomStructure(models.AbstractModel):
    _inherit = 'report.mrp.report_bom_structure'

    @api.model
    def _get_report_values(self, docids, data=None):
        docs = []
        if docids is None and data.get('docids', False):
            docids = data.get('docids')
        for bom_id in docids:
            bom = self.env['mrp.bom'].browse(bom_id)
            candidates = bom.product_id or bom.product_tmpl_id.product_variant_ids
            quantity = float(data.get('quantity', 1))
            for product_variant_id in candidates:
                if data and data.get('childs'):
                    doc = self._get_pdf_line(bom_id, product_id=product_variant_id, qty=quantity, child_bom_ids=json.loads(data.get('childs')))
                else:
                    doc = self._get_pdf_line(bom_id, product_id=product_variant_id, qty=quantity, unfolded=True)
                doc['report_type'] = 'pdf'
                doc['report_structure'] = data and data.get('report_type') or 'all'
                docs.append(doc)
            if not candidates:
                if data and data.get('childs'):
                    doc = self._get_pdf_line(bom_id, qty=quantity, child_bom_ids=json.loads(data.get('childs')))
                else:
                    doc = self._get_pdf_line(bom_id, qty=quantity, unfolded=True)
                doc['report_type'] = 'pdf'
                doc['report_structure'] = data and data.get('report_type') or 'all'
                docs.append(doc)
        return {
            'doc_ids': docids,
            'doc_model': 'mrp.bom',
            'docs': docs,
        }

class MrpProduction(models.Model):
    """ Manufacturing Orders """
    _inherit = 'mrp.production'

    parent_id = fields.Many2one(comodel_name='mrp.production')
    children_ids = fields.One2many(comodel_name='mrp.production', inverse_name='parent_id')

    def action_print_bom(self):
        data = dict(quantity=self.product_qty, docids=[self.bom_id.id], no_price=True, report_type='bom_structure')
        report = self.env.ref('mrp.action_report_bom_structure').with_context(discard_logo_check=True)
        report.name = 'Estructura de materiales - {}'.format(self.name)
        return report.report_action(self.bom_id, data)
        
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
        
        production.move_raw_ids.write({
            'group_id': production.procurement_group_id.id,
            'reference': production.name,  # set reference when MO name is different than 'New'
        })
        # Trigger move_raw creation when importing a file
        if 'import_file' in self.env.context:
            production._onchange_move_raw()
        return production