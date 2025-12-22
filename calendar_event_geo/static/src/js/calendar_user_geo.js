/** @odoo-module **/

import { registry } from "@web/core/registry";
import { rpc } from "@web/core/network/rpc";

registry.category("actions").add(
    "calendar_user_geo",
    async (env, action) => {

        const ctx = action.context || {};
        const resModel = ctx.res_model;
        const resId = ctx.res_id;

        if (!resModel || !resId) {
            env.services.notification.add(
                "No se pudo determinar el registro.",
                { type: "danger" }
            );
            return;
        }

        if (resModel !== "crm.lead") {
            env.services.notification.add(
                "La actividad no está vinculada a un lead.",
                { type: "danger" }
            );
            return;
        }

        if (!navigator.geolocation) {
            env.services.notification.add(
                "Tu navegador no soporta geolocalización.",
                { type: "danger" }
            );
            return;
        }

        navigator.geolocation.getCurrentPosition(
            async (pos) => {
                await rpc("/web/dataset/call_kw", {
                    model: "crm.lead",
                    method: "write",
                    args: [[resId], {
                        geo_latitude: pos.coords.latitude,
                        geo_longitude: pos.coords.longitude,
                    }],
                    kwargs: {},
                });

                env.services.notification.add(
                    "Ubicación guardada correctamente. Ya puedes marcar la actividad como hecha.",
                    { type: "success" }
                );
            },
            () => {
                env.services.notification.add(
                    "No se pudo obtener tu ubicación.",
                    { type: "danger" }
                );
            },
            { enableHighAccuracy: true }
        );
    }
);
