/** @odoo-module **/

import {patch} from "@web/core/utils/patch";
import {Activity} from "@mail/components/activity/activity";
import {rpc} from "@web/core/network/rpc";

patch(Activity.prototype, "activity_geo_patch", {
    async onClickDone(ev) {
        ev.preventDefault();
        ev.stopPropagation();

        console.log("📍 Interceptando Hecho (Odoo 18)");

        const activity = this.props.activity;

        // Solo reuniones
        if (activity.activity_type_id.name !== "Reunión") {
            return await this._super(ev);
        }

        // Buscar evento asociado
        const events = await rpc("/web/dataset/call_kw", {
            model: "calendar.event",
            method: "search_read",
            args: [[["activity_ids", "in", activity.id]]],
            kwargs: {
                limit: 1,
                fields: ["id", "done_latitude", "done_longitude"],
            },
        });

        if (!events.length) {
            return await this._super(ev);
        }

        const event = events[0];


        if (!event.done_latitude || !event.done_longitude) {
            if (!navigator.geolocation) {
                this.env.services.notification.add(
                    "El navegador no soporta geolocalización.",
                    {type: "danger"}
                );
                return;
            }

            navigator.geolocation.getCurrentPosition(
                async (pos) => {
                    await rpc("/web/dataset/call_kw", {
                        model: active_model,
                        method: "write",
                        args: [[active_id], {
                            done_latitude: pos.coords.latitude,
                            done_longitude: pos.coords.longitude,
                            done_accuracy: pos.coords.accuracy, // 👈 NUEVO
                            done_geo_at: new Date().toISOString(), // 👈 NUEVO
                        }],
                        kwargs: {},
                    });


                    this.env.services.notification.add(
                        "Ubicación guardada. Pulsa de nuevo «Hecho».",
                        {type: "success"}
                    );
                },
                () => {
                    this.env.services.notification.add(
                        "No se pudo obtener la ubicación.",
                        {type: "danger"}
                    );
                },
                {enableHighAccuracy: true}
            );
            return;
        }

        // 🟢 Ya hay geo → dejar continuar
        return await this._super(ev);
    },
});
