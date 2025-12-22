/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import { Activity } from "@mail/components/activity/activity";
import { rpc } from "@web/core/network/rpc";

patch(Activity.prototype, "activity_geo_patch", {
    async onClickDone(ev) {
        ev.preventDefault();
        ev.stopPropagation();

        const activityId = this.props.activity.id;
        const resModel = this.props.activity.res_model;
        const resId = this.props.activity.res_id;

        // Si no es una reunión → comportamiento normal
        if (resModel !== "calendar.event") {
            return await this._super(ev);
        }

        if (!navigator.geolocation) {
            alert("Tu navegador no soporta geolocalización");
            return;
        }

        navigator.geolocation.getCurrentPosition(
            async (position) => {
                const lat = position.coords.latitude;
                const lon = position.coords.longitude;

                console.log("📍 Geo obtenida:", lat, lon);

                //  Guardar GEO EN EL EVENTO
                await rpc("/web/dataset/call_kw", {
                    model: "calendar.event",
                    method: "write",
                    args: [[resId], {
                        done_latitude: lat,
                        done_longitude: lon,
                    }],
                });

                //  Llamar al método REAL de Odoo
                await rpc("/web/dataset/call_kw", {
                    model: "mail.activity",
                    method: "action_mark_done",
                    args: [[activityId]],
                });
            },
            () => {
                alert("No se pudo obtener tu ubicación");
            },
            { enableHighAccuracy: true }
        );
    },
});
