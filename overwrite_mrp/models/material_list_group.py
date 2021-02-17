from odoo import api, fields, models

class BomRegister(models.Model):

    _name = 'overwrite_mrp.bom_register'
    _description = 'A register of material list'

    boms_id = fields.Many2one(
        string='Lista',
        comodel_name='mrp.bom'
        )
    
    repetitions = fields.Integer(string='Repeticiones')
    quantity = fields.Integer(string='Cantidad')
    total = fields.Integer(string='Total', compute='_calc_total')
    

    related_group = fields.Many2one(
        string='Grupo Relacionado',
        comodel_name='overwrite_mrp.bom_group'
    )

    @api.depends('repetitions', 'quantity')
    def _calc_total(self):
        for record in self:
            record.total = record.repetitions * record.quantity
    

class BomGroup(models.Model):

    _name = 'overwrite_mrp.bom_group'
    _description = 'An agrupation of Bom Reister'

    bom_list = fields.One2many(
        string='Listas Relacionadas',
        comodel_name='overwrite_mrp.bom_register',
        inverse_name='related_group'
        )