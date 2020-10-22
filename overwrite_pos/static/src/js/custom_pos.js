odoo.define('custom_pos.models', function (require) {
    "use strict";
    console.log('dashboard #3');
    var posModels = require('point_of_sale.models');
    posModels.Orderline = posModels.Orderline.extend({
        get_taxes_names: function() {
            var taxes_ids = this.get_product().taxes_id
            var product_taxes = [];
            var taxes =  this.pos.taxes;
            _(taxes_ids).each(function(el){
                var tax = _.detect(taxes, function(t){
                    return t.id === el;
                });
                product_taxes.push(tax.name);
            });
            return product_taxes;
        },
        export_for_printing: function(){
            return {
                quantity:           this.get_quantity(),
                unit_name:          this.get_unit().name,
                price:              this.get_unit_display_price(),
                discount:           this.get_discount(),
                product_name:       this.get_product().display_name,
                product_name_wrapped: this.generate_wrapped_product_name(),
                price_lst:          this.get_lst_price(),
                display_discount_policy:    this.display_discount_policy(),
                price_display_one:  this.get_display_price_one(),
                price_display :     this.get_display_price(),
                price_with_tax :    this.get_price_with_tax(),
                price_without_tax:  this.get_price_without_tax(),
                price_with_tax_before_discount:  this.get_price_with_tax_before_discount(),
                tax:                this.get_tax(),
                product_description:      this.get_product().description,
                product_description_sale: this.get_product().description_sale,
                taxes: this.get_taxes_names()
            };
        },
    });
 });