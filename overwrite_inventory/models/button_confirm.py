from odoo import models


class button_confirm(models.TransientModel):
    _name = "overwrite_inventory.button.confirm"

    def button_confirm(self):
        query = [['id', '=', self._context['srap']]]
        stock_scrap = self.env['stock.scrap'].search(query)
        stock_scrap.action_validate_second_confirm()
        return {
            'type': 'ir.actions.act_window_close'
        }
