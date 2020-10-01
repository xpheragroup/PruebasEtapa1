from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from odoo.osv import expression
from odoo.tools import float_compare, float_is_zero
from odoo.addons.base.models.ir_model import MODULE_UNINSTALL_FLAG


class Inventory(models.Model):
    _inherit = "stock.inventory"

    AJUSTES = [('conteo', 'Por conteo'), ('diferencia','Por diferencia'), ('baja','Baja de inventario')]
    ajuste = fields.Selection(AJUSTES, 
        string='Tipo de ajuste',
        readonly=True,
        states={'draft': [('readonly', False)]},
        help="Tipo de ajuste del inventario.")

    def action_open_inventory_lines(self):
        self.ensure_one()
        if self.ajuste == 'conteo':
            action = {
                'type': 'ir.actions.act_window',
                'views': [(self.env.ref('overwrite_inventory.stock_inventory_line_tree3').id, 'tree')],
                'view_mode': 'tree',
                'name': _('Inventory Lines'),
                'res_model': 'stock.inventory.line',
            }
        elif self.ajuste == 'baja':
            action = {
                'type': 'ir.actions.act_window',
                'views': [(self.env.ref('overwrite_inventory.stock_inventory_line_tree5').id, 'tree')],
                'view_mode': 'tree',
                'name': _('Inventory Lines'),
                'res_model': 'stock.inventory.line',
            }
        else:
            action = {
                'type': 'ir.actions.act_window',
                'views': [(self.env.ref('overwrite_inventory.stock_inventory_line_tree4').id, 'tree')],
                'view_mode': 'tree',
                'name': _('Inventory Lines'),
                'res_model': 'stock.inventory.line',
            }
        context = {
            'default_is_editable': True,
            'default_inventory_id': self.id,
            'default_company_id': self.company_id.id,
        }
        # Define domains and context
        domain = [
            ('inventory_id', '=', self.id),
            ('location_id.usage', 'in', ['internal', 'transit'])
        ]
        if self.location_ids:
            context['default_location_id'] = self.location_ids[0].id
            if len(self.location_ids) == 1:
                if not self.location_ids[0].child_ids:
                    context['readonly_location_id'] = True

        if self.product_ids:
            if len(self.product_ids) == 1:
                context['default_product_id'] = self.product_ids[0].id

        action['context'] = context
        action['domain'] = domain
        return action

    def _get_inventory_lines_values(self):
        # TDE CLEANME: is sql really necessary ? I don't think so
        locations = self.env['stock.location']
        if self.location_ids:
            locations = self.env['stock.location'].search([('id', 'child_of', self.location_ids.ids)])
        else:
            locations = self.env['stock.location'].search([('company_id', '=', self.company_id.id), ('usage', 'in', ['internal', 'transit'])])
        domain = ' sq.location_id in %s AND pp.active'
        args = (tuple(locations.ids),)

        vals = []
        Product = self.env['product.product']
        # Empty recordset of products available in stock_quants
        quant_products = self.env['product.product']

        # If inventory by company
        if self.company_id:
            domain += ' AND sq.company_id = %s'
            args += (self.company_id.id,)
        if self.product_ids:
            domain += ' AND sq.product_id in %s'
            args += (tuple(self.product_ids.ids),)

        self.env['stock.quant'].flush(['company_id', 'product_id', 'quantity', 'location_id', 'lot_id', 'package_id', 'owner_id'])
        self.env['product.product'].flush(['active'])
        self.env.cr.execute("""SELECT sq.product_id, sum(sq.quantity) as product_qty, sq.location_id, sq.lot_id as prod_lot_id, sq.package_id, sq.owner_id as partner_id
            FROM stock_quant sq
            LEFT JOIN product_product pp
            ON pp.id = sq.product_id
            WHERE %s
            GROUP BY sq.product_id, sq.location_id, sq.lot_id, sq.package_id, sq.owner_id """ % domain, args)

        for product_data in self.env.cr.dictfetchall():
            product_data['company_id'] = self.company_id.id
            product_data['inventory_id'] = self.id
            # replace the None the dictionary by False, because falsy values are tested later on
            for void_field in [item[0] for item in product_data.items() if item[1] is None]:
                product_data[void_field] = False
            product_data['theoretical_qty'] = product_data['product_qty']
            if self.prefill_counted_quantity == 'zero':
                if 'difference_qty_2' in product_data.keys():
                    product_data['product_qty'] = 0 + product_data['difference_qty_2']
                else:
                    product_data['product_qty'] = 0
            if product_data['product_id']:
                product_data['product_uom_id'] = Product.browse(product_data['product_id']).uom_id.id
                quant_products |= Product.browse(product_data['product_id'])
            vals.append(product_data)
        return vals

    def _action_done(self):
        negative = next((line for line in self.mapped('line_ids') if line.product_qty < 0 and line.product_qty != line.theoretical_qty), False)
        not_checked = next((line for line in self.mapped('line_ids') if not line.revisado), False)
        negative_lost = next((line for line in self.mapped('line_ids') if line.perdida < 0), False)
        print(not_checked)
        if negative:
            raise UserError(_('You cannot set a negative product quantity in an inventory line:\n\t%s - qty: %s') % (negative.product_id.name, negative.product_qty))
        if not_checked:
            raise UserError(_('No se ha revisado algún producto.'))
        if negative_lost:
            raise UserError(_('Algún producto tiene pérdida negativa.'))
        self.action_check()
        self.write({'state': 'done'})
        self.post_inventory()
        return True

class InventoryLine(models.Model):
    _inherit = "stock.inventory.line"

    revisado = fields.Boolean('Revisado', required=True)
    motivo_de_baja = fields.Selection([
        ('obs', 'Obsolecencia de Bien'),
        ('da', 'Daño'),
        ('fec', 'Fecha de Vencimiento'),
        ('hur',	'Hurto')],
        string='Motivo de Baja')

    showed_qty = fields.Float('Contado',
        help="Campo que muestra la cantidad contada.",
        compute="update_showed_quantity",
        digits='Product Unit of Measure', default=0)
    
    difference_qty_2 = fields.Float('Diferencia',
        help="Diferencia ingresada para el cálculo de la cantidad contada.",
        digits='Product Unit of Measure', default=0)

    perdida = fields.Float('Pérdida',
        help="Productos perdidos.",
        digits='Product Unit of Measure', default=0)

    prueba = fields.Image('Prueba')
    costo = fields.Float(related='product_id.standard_price')
    total_perdida = fields.Float(compute='_compute_lost')

    @api.depends('costo', 'perdida')
    def _compute_lost(self):
        for line in self:
            line.total_perdida = line.costo * line.perdida

    @api.onchange('perdida')
    def update_quantity_by_perdida(self):
        for line in self:
            line.product_qty = line.theoretical_qty - line.perdida

    @api.onchange('difference_qty_2')
    def update_quantity_by_difference(self):
        for line in self:
            line.product_qty = line.theoretical_qty + line.difference_qty_2

    @api.onchange('product_qty')
    def update_showed_quantity(self):
        for line in self:
            line.showed_qty = line.product_qty
    
    @api.onchange('product_id', 'location_id', 'product_uom_id', 'prod_lot_id', 'partner_id', 'package_id')
    def _onchange_quantity_context(self):
        product_qty = False
        if self.product_id:
            self.product_uom_id = self.product_id.uom_id
        if self.product_id and self.location_id and self.product_id.uom_id.category_id == self.product_uom_id.category_id:  # TDE FIXME: last part added because crash
            theoretical_qty = self.product_id.get_theoretical_quantity(
                self.product_id.id,
                self.location_id.id,
                lot_id=self.prod_lot_id.id,
                package_id=self.package_id.id,
                owner_id=self.partner_id.id,
                to_uom=self.product_uom_id.id,
            )
        else:
            theoretical_qty = 0
        # Sanity check on the lot.
        if self.prod_lot_id:
            if self.product_id.tracking == 'none' or self.product_id != self.prod_lot_id.product_id:
                self.prod_lot_id = False

        if self.prod_lot_id and self.product_id.tracking == 'serial':
            # We force `product_qty` to 1 for SN tracked product because it's
            # the only relevant value aside 0 for this kind of product.
            self.product_qty = 1
        elif self.product_id and float_compare(self.product_qty, self.theoretical_qty, precision_rounding=self.product_uom_id.rounding) == 0:
            # We update `product_qty` only if it equals to `theoretical_qty` to
            # avoid to reset quantity when user manually set it.
            self.product_qty = theoretical_qty + self.difference_qty_2
        self.theoretical_qty = theoretical_qty

class StockScrap(models.Model):
    _inherit = 'stock.scrap'

    state = fields.Selection([
        ('draft', 'Elaboración'),
        ('review', 'Revisión'),
        ('auth', 'Autorización'),
        ('approv', 'Aprobación'),
        ('done', 'Done')],
        string='Status', default="draft", readonly=True, tracking=True)

    rule = {
        'review': [('readonly', True)],
        'auth': [('readonly', True)],
        'approv': [('readonly', True)],
        'done': [('readonly', True)],
        }

    company_id = fields.Many2one(states=rule, tracking=1)
    product_id = fields.Many2one(states=rule, tracking=1)
    origin = fields.Char(states=rule)
    product_uom_id = fields.Many2one(states=rule, tracking=1)
    lot_id = fields.Many2one(states=rule, tracking=1)
    package_id = fields.Many2one(states=rule, tracking=1)
    owner_id = fields.Many2one(states=rule, tracking=1)
    picking_id = fields.Many2one(states=rule, tracking=1)
    location_id = fields.Many2one(states=rule, tracking=1)
    scrap_location_id = fields.Many2one(states=rule, tracking=1)
    scrap_qty = fields.Float(states=rule, tracking=1)

    motivo_de_baja = fields.Selection([
        ('obs', 'Obsolecencia de Bien'),
        ('da', 'Daño'),
        ('fec', 'Fecha de Vencimiento'),
        ('hur',	'Hurto')],
        string='Motivo de Baja', states=rule, tracking=1)
    
    def to_review(self):
        self._check_company()
        for scrap in self:
            scrap.name = self.env['ir.sequence'].next_by_code('stock.scrap') or _('New')
            scrap.date_done = fields.Datetime.now()
            scrap.write({'state': 'review'})
        if self.product_id.type != 'product':
            return True
        precision = self.env['decimal.precision'].precision_get('Product Unit of Measure')
        location_id = self.location_id
        if self.picking_id and self.picking_id.picking_type_code == 'incoming':
            location_id = self.picking_id.location_dest_id
        available_qty = sum(self.env['stock.quant']._gather(self.product_id,
                                                            location_id,
                                                            self.lot_id,
                                                            self.package_id,
                                                            self.owner_id,
                                                            strict=True).mapped('quantity'))
        scrap_qty = self.product_uom_id._compute_quantity(self.scrap_qty, self.product_id.uom_id)
        if float_compare(available_qty, scrap_qty, precision_digits=precision) >= 0:
            return True
        else:
            ctx = dict(self.env.context)
            ctx.update({
                'default_product_id': self.product_id.id,
                'default_location_id': self.location_id.id,
                'default_scrap_id': self.id
            })
            return {
                'name': _('Insufficient Quantity'),
                'view_mode': 'form',
                'res_model': 'stock.warn.insufficient.qty.scrap',
                'view_id': self.env.ref('stock.stock_warn_insufficient_qty_scrap_form_view').id,
                'type': 'ir.actions.act_window',
                'context': ctx,
                'target': 'new'
            }

    def to_auth(self):
        self._check_company()
        for scrap in self:
            scrap.write({'state': 'auth'})
        return True
    
    def to_approv(self):
        self._check_company()
        for scrap in self:
            scrap.write({'state': 'approv'})
        return True
    
    def to_draft(self):
        self._check_company()
        for scrap in self:
            scrap.write({'state': 'draft'})
        return True

    def do_scrap(self):
        self._check_company()
        for scrap in self:
            move = self.env['stock.move'].create(scrap._prepare_move_values())
            # master: replace context by cancel_backorder
            move.with_context(is_scrap=True)._action_done()
            scrap.write({'move_id': move.id, 'state': 'done'})
        return True
    

    def _prepare_move_values(self):
        self.ensure_one()
        location_id = self.location_id.id
        if self.picking_id and self.picking_id.picking_type_code == 'incoming':
            location_id = self.picking_id.location_dest_id.id
        return {
            'name': self.name,
            'origin': self.origin or self.picking_id.name or self.name,
            'company_id': self.company_id.id,
            'product_id': self.product_id.id,
            'product_uom': self.product_uom_id.id,
            'state': 'draft',
            'product_uom_qty': self.scrap_qty,
            'location_id': location_id,
            'scrapped': True,
            'location_dest_id': self.scrap_location_id.id,
            'move_line_ids': [(0, 0, {'product_id': self.product_id.id,
                                           'product_uom_id': self.product_uom_id.id, 
                                           'qty_done': self.scrap_qty,
                                           'location_id': location_id,
                                           'location_dest_id': self.scrap_location_id.id,
                                           'package_id': self.package_id.id, 
                                           'owner_id': self.owner_id.id,
                                           'lot_id': self.lot_id.id, })],
#             'restrict_partner_id': self.owner_id.id,
            'picking_id': self.picking_id.id
        }

    def action_validate(self):
        self.ensure_one()
        return self.do_scrap()

class StockWarnInsufficientQtyScrapOver(models.TransientModel):
    _inherit = 'stock.warn.insufficient.qty.scrap'

    def action_done(self):
        return True

    def action_cancel(self):
        return self.scrap_id.to_draft()