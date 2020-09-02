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
    property_account_position_id = fields.Char(tracking=1)
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
            if vals.get('bank_ids'):
                for bank_ids_change in vals['bank_ids']:
                    if bank_ids_change[2]:
                        if 'acc_number' in bank_ids_change[2]:
                            message = 'Se ha cambiado el número de la cuenta bancaria a {}.'
                            self.message_post(body=message.format(bank_ids_change[2]['acc_number']))
                        if 'bank_id' in bank_ids_change[2]:
                            message = 'Se ha cambiado la cuenta bancaria a {}.'
                            bank_name = self.env['res.bank'].search([['id','=',bank_ids_change[2]['bank_id']]]).name
                            self.message_post(body=message.format(bank_name))
            if vals.get('child_ids'):
                self.message_post(body='Se ha cambiado la información de los contactos.')
            if vals.get('active'):
                if vals['active']:
                    self.message_post(body='El estado del contacto ha pasado a dearchivado.')
                else:
                    self.message_post(body='El estado del contacto ha pasado a archivado.')
        return write_result

