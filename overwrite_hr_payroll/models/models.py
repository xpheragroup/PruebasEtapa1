
from odoo import models, fields, api


class overwrite_payroll_contract(models.Model):
    _inherit = 'hr.contract'
    tipo_de_contrato = fields.Selection(
        selection=[('1','Modalidad 1: Igual o superior a un año'),
        ('2', 'Modalidad 2: Inferior a un año'),
        ('3', 'Contrato a término indefinido'),
        ('4', 'Contrato civil por prestación de servicios'),
        ('5', 'Contrato de aprendizaje'),
        ('6', 'Contrato de Obra o labor'),
        ('7', 'Contrato temporal, ocasional o accidental'),
        ('8', 'Contrato de trabajo móvil')]
    )

    eps = fields.Char(
        string='EPS',
        help='Ingrese la EPS'
    )

    caja_compensacion = fields.Char(
        string='Caja de compensación',
        help='Aquí se debe ingresar la caja de compensación'
    )

    fondo_pension = fields.Char(
        string='Fondo de pensiones',
        help='Aquí se debe ingresar la caja de compensación'
    )

    aseguradora_riesgo = fields.Char(
        string='Nombre de aseguradora ARL',
        help='Aquí se debe diligenciar el nombre de la aseguradora'
    )

    clase_riesgo = fields.Selection(
        string='Clase de riesgo',
        selection=[('1', 'Tipo I'),
                   ('2', 'Tipo II'),
                   ('3', 'Tipo III'),
                   ('4', 'Tipo IV'),
                   ('5', 'Tipo V')]
    )

    rodamiento = fields.Monetary(
        string='Rodamiento'
    )

    porcentaje_comision = fields.Float(
        string='Porcentaje de comisión',
        help='Aquí debe ingresar el porcentaje de comisión, que será calculada en base a las ventas que ingresará en nómina.'
    )

    comision_es_prestacional = fields.Boolean(
        string='¿La comisión es prestacional?',
        help='Si la comisión es prestacional, habilite.'
    )

    bono_es_prestacional = fields.Boolean(
        string='¿El bono es prestacional?',
        help='Si el bono es prestacional, habilite.'
    )

    rodamiento_es_prestacional = fields.Boolean(
        string='¿El rodamiento es prestacional?',
        help='Si el rodamiento es prestacional, habilite.'
    )


class overwrite_payroll_employee(models.Model):
    _inherit = 'hr.employee'
#informacion personal
    ciudad_de_nacimiento = fields.Char()
    ciudad_actual = fields.Char()
    casa_propia = fields.Boolean(string='¿tiene casa propia?')
    carro_propio = fields.Boolean(string='¿tiene carro?')
    placas_carro =fields.Integer()

#informacion de documento
    tipo_de_documento = fields.Selection(
        string='Tipo de documento',
        selection=[('1', 'Cédula de ciudadanía'),
                   ('2', 'Cédula de extranjería'),
                   ('3', 'Pasaporte'),]
    )
    ciudad_de_expedicion = fields.Char()

#informacion de salud
    fuma = fields.Boolean(string='¿fuma?')
    estatura = fields.Integer(string="estatura en centimetros")
    anteojos = fields.Boolean(string='¿usa anteojos?')
    factor_rh = fields.Selection(
        string='Factor RH',
        selection=[('1', 'positivo'),
                   ('2', 'negativo'),]
    )
    grupo_sanguineo = fields.Selection(
        string='Grupo Sanguineo',
        selection=[('1', 'O'),
                   ('2', 'A'),
                   ('3', 'B'),
                   ('4', 'AB')]
    )
    embarazo = fields.Boolean(string='¿se encuentra en estado de embarazo?')

#informacion judicial
    libreta_militar = fields.Boolean(string='¿tiene libreta militar?')
    certificado_judicial = fields.Boolean()