# -*- coding: utf-8 -*-

from odoo import models, fields

class tracking_field_overwriter(models.Model):

    _name = 'res.partner'
    _inherit = 'res.partner'

    # Base Name
    name = fields.Char(tracking=1)
    var = fields.Char(tracking=1)
    phone = fields.Char(tracking=1)
    mobile = fields.Char(tracking=1)
    email = fields.Char(tracking=1)
    website = fields.Char(tracking=1)

    # Base Address
    street = fields.Char(tracking=1)
    street2 = fields.Char(tracking=1)
    city = fields.Char(tracking=1)
    state_id = fields.Many2one(tracking=1)
    zip = fields.Char(tracking=1)
    country_id = fields.Many2one(tracking=1)

    # Sales and purchase
    user_id = fields.Many2one(tracking=1)
    property_payment_term_id = fields.Many2one(tracking=1)
    property_supplier_payment_term_id = fields.Many2one(tracking=1)
    default_supplierinfo_discount = fields.Float(tracking=1)
    barcode = fields.Char(tracking=1)
    property_account_position_id = fields.Many2one(tracking=1)
    ref = fields.Char(tracking=1)
    company_id = fields.Many2one(tracking=1)
    website_id = fields.Many2one(tracking=1)
    industry_id = fields.Many2one(tracking=1)
    property_stock_customer = fields.Many2one(tracking=1)
    property_stock_supplier = fields.Many2one(tracking=1)

    # Accounting
    bank_ids = fields.One2many(tracking=1)
    property_account_receivable_id = fields.Many2one(tracking=1)
    property_account_payable_id = fields.Many2one(tracking=1)

    # Internal notes
    comment = fields.Text(tracking=1)

    # 2Many fields 
    def write(self, vals):
        write_result = super(tracking_field_overwriter, self).write(vals)
        if write_result:
            if vals.get('bank_ids') is not None:
                for bank_ids_change in vals['bank_ids']:
                    if bank_ids_change[2]:
                        if 'acc_number' in bank_ids_change[2]:
                            message = 'Se ha cambiado el número de la cuenta bancaria a {}.'
                            self.message_post(body=message.format(bank_ids_change[2]['acc_number']))
                        if 'bank_id' in bank_ids_change[2]:
                            message = 'Se ha cambiado la cuenta bancaria a {}.'
                            bank_name = self.env['res.bank'].search([['id','=',bank_ids_change[2]['bank_id']]]).name
                            self.message_post(body=message.format(bank_name))
            if vals.get('child_ids') is not None:
                self.message_post(body='Se ha cambiado la información de los contactos.')
            if vals.get('active') is not None:
                if vals['active']:
                    self.message_post(body='El estado del contacto ha pasado a dearchivado.')
                else:
                    self.message_post(body='El estado del contacto ha pasado a archivado.')
        return write_result


class ProductOver(models.Model):
    _inherit = 'product.template'

    name = fields.Char(tracking=1)
    sequence = fields.Integer(tracking=1)
    description = fields.Text(tracking=1)
    description_purchase = fields.Text(tracking=1)
    description_sale = fields.Text(tracking=1)
    type = fields.Selection(tracking=1)
    rental = fields.Boolean(tracking=1)
    categ_id = fields.Many2one(tracking=1)
    currency_id = fields.Many2one(tracking=1)
    cost_currency_id = fields.Many2one(tracking=1)

    # price fields
    # price: total template price, context dependent (partner, pricelist, quantity)
    price = fields.Float(tracking=1)
    # list_price: catalog price, user defined
    list_price = fields.Float(tracking=1)
    # lst_price: catalog price for template, but including extra for variants
    lst_price = fields.Float(tracking=1)
    standard_price = fields.Float(tracking=1)

    volume = fields.Float(tracking=1)
    weight = fields.Float(tracking=1)
    weight_uom_name = fields.Char(tracking=1)

    sale_ok = fields.Boolean(tracking=1)
    purchase_ok = fields.Boolean(tracking=1)
    pricelist_id = fields.Many2one(tracking=1)
    uom_id = fields.Many2one(tracking=1)
    uom_name = fields.Char(tracking=1)
    uom_po_id = fields.Many2one(tracking=1)
    company_id = fields.Many2one(tracking=1)
    packaging_ids = fields.One2many(tracking=1)
    seller_ids = fields.One2many(tracking=1)
    variant_seller_ids = fields.One2many(tracking=1)

    #active = fields.Boolean(tracking=1)
    color = fields.Integer(tracking=1)

    is_product_variant = fields.Boolean(tracking=1)
    attribute_line_ids = fields.One2many(tracking=1)

    valid_product_template_attribute_line_ids = fields.Many2many(tracking=1)

    product_variant_ids = fields.One2many(tracking=1)
    # performance: product_variant_id provides prefetching on the first product variant only
    product_variant_id = fields.Many2one(tracking=1)

    product_variant_count = fields.Integer(tracking=1)

    # related to display product product information if is_product_variant
    barcode = fields.Char(tracking=1)
    default_code = fields.Char(tracking=1)

    pricelist_item_count = fields.Integer(tracking=1)

    can_image_1024_be_zoomed = fields.Boolean(tracking=1)
    has_configurable_attributes = fields.Boolean(tracking=1)

    #Stock

    responsible_id = fields.Many2one(tracking=1)
    property_stock_production = fields.Many2one(tracking=1)
    property_stock_inventory = fields.Many2one(tracking=1)
    sale_delay = fields.Float(tracking=1)
    tracking = fields.Selection(tracking=1)
    description_picking = fields.Text(tracking=1)
    description_pickingout = fields.Text(tracking=1)
    description_pickingin = fields.Text(tracking=1)
    qty_available = fields.Float(tracking=1)
    virtual_available = fields.Float(tracking=1)
    incoming_qty = fields.Float(tracking=1)
    outgoing_qty = fields.Float(tracking=1)
    # The goal of these fields is to be able to put some keys in context from search view in order
    # to influence computed field.
    location_id = fields.Many2one(tracking=1)
    warehouse_id = fields.Many2one(tracking=1)
    route_ids = fields.Many2many(tracking=1)
    nbr_reordering_rules = fields.Integer(tracking=1)
    reordering_min_qty = fields.Float(tracking=1)
    reordering_max_qty = fields.Float(tracking=1)
    # TDE FIXME: seems only visible in a view - remove me ?
    route_from_categ_ids = fields.Many2many(tracking=1)

    # 2Many fields 
    def write(self, vals):
        write_result = super(ProductOver, self).write(vals)
        if write_result:
            if vals.get('active') is not None:
                if vals['active']:
                    self.message_post(body='El estado del producto ha pasado a dearchivado.')
                else:
                    self.message_post(body='El estado del producto ha pasado a archivado.')

class ProductionOver(models.Model):
    _inherit = 'mrp.production'

    # 2Many fields
    def write(self, vals):
        write_result = super(ProductionOver, self).write(vals)
        if write_result:
            if vals.get('move_raw_ids') is not None:
                message = '<p>Se han hecho los siguientes cambios a la receta:</p><ul>'
                mods = 0
                for component in vals['move_raw_ids']:
                    if component[2] != False:
                        mods += 1
                        if 'virtual' in str(component[1]):
                            message += '<li>Se agrega el producto {}.</li>'.format(component[2]['name'])
                        elif component[2].get('product_uom_qty') is not None:
                            move = self.env['stock.move'].search([['id', '=', component[1]]])
                            message += '<li>Se modifica la cantidad a usar del producto {}. De {} a {}.</li>'.format(move.product_tmpl_id.name, move.product_uom_qty, component[2]['product_uom_qty'])
                message += '</ul>'
                if mods > 0:
                    self.message_post(body=message)
