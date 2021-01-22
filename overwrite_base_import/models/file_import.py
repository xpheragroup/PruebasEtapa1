from odoo import api, fields, models

class file_import(models.Model):

    _name = 'overwrite_base_import.file_import'

    file_name = fields.Char(string='Nombre del archivo', index=True, readonly=True)
    file_hash = fields.Char(
        string='Valor hash del archivo', 
        help='Valor hash asignado para el contenido del archivo',
        index=True,
        readonly=True)
