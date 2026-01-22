/** @odoo-module **/



import { patch } from "@web/core/utils/patch";
import { Activity } from "@mail/components/activity/activity";
import { rpc } from "@web/core/network/rpc";

patch(Activity.prototype, "activity_geo_patch", {
    async markDone(ev) {
        ev.preventDefault();
        ev.stopPropagation();

        const activity = this.props.activity;
        const activityId = activity.id;

        // Solo reuniones
        if (activity.activity_type_id.name !== "Reunión") {
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

                console.log("📍 GEO obtenida:", lat, lon);

                //  Buscar el evento real
                const events = await rpc("/web/dataset/call_kw", {
                    model: "calendar.event",
                    method: "search_read",
                    args: [[["activity_ids", "in", activityId]]],
                    kwargs: { limit: 1, fields: ["id"] },
                });

                if (!events.length) {
                    alert("No se encontró la reunión asociada.");
                    return;
                }

                const eventId = events[0].id;

                // Guardar GEO en el evento
                await rpc("/web/dataset/call_kw", {
                    model: "calendar.event",
                    method: "write",
                    args: [[eventId], {
                        done_latitude: lat,
                        done_longitude: lon,
                    }],
                });

                //  Llamar al método ORIGINAL
                return await this._super(ev);
            },
            () => {
                alert("No se pudo obtener tu ubicación");
            },
            { enableHighAccuracy: true }
        );
    },
});
