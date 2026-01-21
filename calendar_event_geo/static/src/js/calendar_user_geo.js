/** @odoo-module **/

console.log("🔥 calendar_user_geo LOADED");

import { registry } from "@web/core/registry";
import { rpc } from "@web/core/network/rpc";

registry.category("actions").add("calendar_user_geo", async (env, action) => {
    const ctx = action.context || {};
    const model = ctx.active_model;
    const id = ctx.active_id;

    if (!model || !id) {
        env.services.notification.add(
            "No se pudo determinar el registro activo.",
            { type: "danger" }
        );
        return;
    }

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
                model: model,
                method: "write",
                args: [[id], {
                    done_latitude: pos.coords.latitude,
                    done_longitude: pos.coords.longitude,
                }],
                 kwargs: {},
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
