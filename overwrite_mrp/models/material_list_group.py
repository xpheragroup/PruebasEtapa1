from odoo import api, fields, models
import json

class BomRegister(models.Model):

    _name = 'overwrite_mrp.bom_register'
    _description = 'A register of material list'

    boms_id = fields.Many2many(
            string='Lista',
            comodel_name='mrp.bom'
        )

    def add_product(data, bom, total):
        if bom.product_id.id in data:
            data[bom.product_id.id]['qty'] = bom.product_qty * total
        else:
            data[bom.product_id.id] = {
                'product': bom.product_id,
                'qty': bom.product_qty * total,
                'uom': bom.product_uom_id
            }
    

    ##TODO: Para la cantidad reservada recorrer los stock_moves de las listas (sacar asi los productos?)
    def get_all_products(self):
        boms = []
        products = {}
        for bom in self.boms_id:
            boms.append(bom)
            for child_bom in bom.bom_line_ids:
                for inner_bom in child_bom.child_line_ids:
                    BomRegister.add_product(products, inner_bom, bom.total)

                if len(child_bom.child_line_ids) == 0:
                    BomRegister.add_product(products, child_bom, bom.total)
            
        data = {'material_lists': boms, 'products': products}
        print(data)
        return data



### This model Should not exist
class BomGroup(models.Model):

    _name = 'overwrite_mrp.bom_group'
    _description = 'This model Should not exist'
