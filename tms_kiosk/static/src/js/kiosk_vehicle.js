odoo.define('tms_kiosk.kiosk_vehicle', function (require) {
"use strict";

var core = require('web.core');
var Model = require('web.Model');
var Widget = require('web.Widget');
var Session = require('web.session');
var BarcodeHandlerMixin = require('barcodes.BarcodeHandlerMixin');
var mobile = require('web_mobile.rpc');

var QWeb = core.qweb;
var _t = core._t;


var KioskVehicle = Widget.extend(BarcodeHandlerMixin, {
    events: {
        "click .o_tms_kiosk_mobile_barcode": 'open_mobile_scanner',
        "click .o_tms_kiosk_button_vehicle_finish": function(){
            this.do_action('tms_kiosk.tms_kiosk_action');
        },
    },

    init: function (parent, action) {
        // Note: BarcodeHandlerMixin.init calls this._super.init, so there's no need to do it here.
        // Yet, "_super" must be present in a function for the class mechanism to replace it with the actual parent method.
        this._super;
        BarcodeHandlerMixin.init.apply(this, arguments);
        var self = this;
        self.params = action.params;
    },

    start: function () {
        var self = this;
        self.$el.html(QWeb.render("TmsKioskVehicle", {widget: self.params}));
        if(!mobile.methods.scanBarcode){
            self.$el.find(".o_tms_kiosk_mobile_barcode").remove();
        }
        self.start_clock();
        return self._super.apply(this, arguments);
    },

    open_mobile_scanner: function(){
        var self = this;
        mobile.methods.scanBarcode().then(function(response){
            var barcode = response.data;
            if(barcode){
                self.on_barcode_scanned(barcode);
                mobile.methods.vibrate({'duration': 100});
            }else{
                mobile.methods.showToast({'message':'Please, Scan again !!'});
            }
        });
    },

    on_barcode_scanned: function(barcode) {
        var self = this;
        var extradata = new Model('tms.extradata');
        extradata.call('data_scan', [barcode, self.params.id])
            .then(function (result) {
                if (result.data) {
                    $('i[data-id=' + result.data.id + ']').show().addClass('checked');
                    if ($('.fa-check-circle').length === $('.checked').length){
                       $('.o_tms_kiosk_button_vehicle_finish').removeClass('hidden');
                       $('.o_tms_kiosk_mobile_barcode').hide();
                    }
                } else if (result.warning) {
                    self.do_warn(result.warning);
                }
            });
    },

    start_clock: function() {
        this.clock_start = setInterval(function() {this.$(".o_tms_kiosk_clock").text(new Date().toLocaleTimeString(navigator.language, {hour: '2-digit', minute:'2-digit'}));}, 500);
        // First clock refresh before interval to avoid delay
        this.$(".o_tms_kiosk_clock").text(new Date().toLocaleTimeString(navigator.language, {hour: '2-digit', minute:'2-digit'}));
    },

    destroy: function () {
        clearInterval(this.clock_start);
        this._super.apply(this, arguments);
    },
});

core.action_registry.add('tms_kiosk_vehicle', KioskVehicle);

return KioskVehicle;

});
