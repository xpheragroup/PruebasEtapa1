# -*- coding: utf-8 -*-
{
    'name': "Duplicate Change",

    'summary': """
        This module change duplicate behaivor for setting elaboraton to current logged user.""",

    'description': """
        This module change duplicate behaivor for setting elaboraton to current logged user.
    """,

    'author': "Xphera",
    'website': "http://xphera.co",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/13.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'purchase', 'purchase_requisition'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'views/views.xml',
        'views/templates.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}
