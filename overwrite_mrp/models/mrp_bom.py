from datetime import datetime
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools import float_round, float_compare

from itertools import groupby

class Override_Bom(models.Model):
    _inherit = 'mrp.bom'

    cost_center = fields.Many2one(
        string="Centro de Costos",
        comodel_name='account.analytic.account')

    cycle = fields.Integer(string='Ciclo')
    
    food_time = fields.Many2one(
        string='Tiempo de comida',
        comodel_name='overwrite_mrp.food_time'
        )
    
    state = fields.Selection(
        string='Estado', 
        selection=[('Borrador', 'Borrador'), ('Aprobado', 'Aprobado')],
        default='Borrador',
        tracking=True)

    approval_user = fields.Many2one(
        string='Usuario que aprueba',
        comodel_name='res.users'
        )
    
    approval_date = fields.Datetime(string='Fecha de aprobación')


    def approve_list(self):
        register = self.env['mrp.bom'].search([('id', '=', self.id)])
        if register.state != 'Aprobado':
            register.write({
                'state': 'Aprobado',
                'approval_user': self.env.user,
                'approval_date': fields.Datetime.now()
            })
