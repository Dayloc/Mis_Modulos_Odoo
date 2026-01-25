/** @odoo-module **/

import { registry } from "@web/core/registry";
import { rpc } from "@web/core/network/rpc";

registry.category("actions").add("calendar_user_geo", async (env, action) => {
    const { active_model, active_id } = action.context || {};

    if (!navigator.geolocation) {
        env.services.notification.add(
            "El navegador no soporta geolocalización.",
            { type: "danger" }
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
                }],
                kwargs: {}
            });

            env.services.notification.add(
                "Ubicación guardada. Pulsa de nuevo «Hecho».",
                { type: "success" }
            );
        },
        () => {
            env.services.notification.add(
                "No se pudo obtener la ubicación.",
                { type: "danger" }
            );
        },
        { enableHighAccuracy: true }
    );
});
