from odoo import api, fields, models

class BomRegister(models.Model):

    _name = 'overwrite_mrp.bom_register'
    _description = 'A register of material list'

    boms_id = fields.Many2many(
            string='Lista',
            comodel_name='mrp.bom'
        )
    bom_line_ids = fields.Many2many(
            string='Lista',
            comodel_name='mrp.bom.line'
        )

class BomGroup(models.Model):

    _name = 'overwrite_mrp.bom_group'
    _description = 'An agrupation of Bom Reister'

    bom_list = fields.Many2many(
        string='Listas Relacionadas',
        comodel_name='overwrite_mrp.bom_register',
        inverse_name='related_group'
        )