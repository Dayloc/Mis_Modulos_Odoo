/** @odoo-module **/

import { registry } from "@web/core/registry";
import { rpc } from "@web/core/network/rpc";

/**
 * Client Action: calendar_event_geo
 * - Llama al backend para geo codificar la dirección
 * - Guarda lat/lon en calendar.event
 * - Recarga el formulario para mostrar los datos
 */
registry.category("actions").add(
    "calendar_event_geo",
    async (env, action) => {
        console.log(" calendar_event_geo ejecutado");

        // Obtener ID del evento (forma correcta en Odoo 18)
        const eventId = action?.context?.active_id;
        console.log(" Event ID:", eventId);

        if (!eventId) {
            alert("Guarda la reunión primero");
            return;
        }

        try {
            //  Llamar al backend
            const result = await rpc("/web/dataset/call_kw", {
                model: "calendar.event",
                method: "action_geocode_address",
                args: [[eventId]],
                kwargs: {},
            });

            if (!result) {
                alert("No se pudieron obtener coordenadas");
                return;
            }

            //  Recargar la vista para mostrar lat/lon
            await env.services.action.doAction({
                type: "ir.actions.client",
                tag: "reload",
            });

            alert("Coordenadas guardadas correctamente");
        } catch (error) {
            console.error("Error RPC:", error);
            alert("Error al obtener coordenadas");
        }
    }
);
