import re
from odoo import api, models, _
from odoo.exceptions import UserError

EMAIL_REGEX = '^[a-z0-9]+[\._]?[a-z0-9]+[@]\w+[.]\w{2,3}$'
PHONE_REGEX = '^[+]*[(]{0,1}[0-9]{1,4}[)]{0,1}[-\s\./0-9]*$'


def regex_validation_message(field, regex, message):
    if field:
        if not re.search(regex, field):
            raise UserError(message)
    return True


def validation_email(email):
    message = _(
        'El correo "{}" no tiene el formato requerido: correo@dominio.dominio')
    return regex_validation_message(email, EMAIL_REGEX, message.format(email))


def validation_phone(phone):
    message = _(
        'El teléfono {} no cumple con el formato. Por favor, escriba los dígitos del ' +
        'teléfono (entre 7 y 13 dígitos). El sistema automáticamente escribirá el ind' +
        'icativo del país, +57 en caso de Colombia.')
    return regex_validation_message(phone, PHONE_REGEX, message.format(phone))


def validation_mobile(mobile):
    message = _(
        'El teléfono celular {} no cumple con el formato. Por favor, escriba los dígi' +
        'tos del léfono (entre 7 y 13 dígitos). El sistema automáticamente escribirá ' +
        'el indicativo del país, +57 en caso de Colombia.')
    return regex_validation_message(mobile, PHONE_REGEX, message.format(mobile))


class Partner(models.Model):
    _inherit = 'res.partner'

    def check_name(self, vals):
        if not vals.get('company_id', False):
            vals['company_id'] = self.company_id.id
        existing_query = [
            ('name', '=', vals['name']),
            ('id', '!=', self.id),
            ('company_id', '=', vals['company_id'])
        ]
        partner_model = self.env['res.partner']
        exists = partner_model.search(existing_query)
        if exists:
            message = _(
                'El proveedor con nombre "{}" ya esta creado en la empresa, modifique' +
                ' el nombre')
            raise UserError(message.format(vals['name']))

    def check_vat(self, vals):
        if not vals.get('company_id', False):
            vals['company_id'] = self.company_id.id
        existing_query = [
            ('vat', '=', vals[vat]),
            ('id', '!=', self.id),
            ('company_id', '=', vals['company_id'])
        ]
        partner_model = self.env['res.partner']
        exists = partner_model.search(existing_query)
        if exists:
            message = _(
                'El proveedor con identificación "' + record.vat +
                '" ya esta creado en la empresa, modifique la identificación.')
            raise UserError(message.format(vals['vat']))

    def do_validations(self, vals):
        validation_email(vals.get('email', False))
        validation_phone(vals.get('phone', False))
        validation_mobile(vals.get('mobile', False))

    @ api.model
    def write(self, vals):
        if vals.get('name', False):
            self.check_name(vals)
            vals['name'] = vals['name'].title()
        if vals.get('vat', False):
            self.check_vat(vals)
        self.do_validations(vals)
        return super(Partner, self).write(vals)
