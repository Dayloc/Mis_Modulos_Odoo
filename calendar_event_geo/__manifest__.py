{
    "name": "Calendar Event Geolocation",
    "version": "1.0",
    "depends": ["calendar", "crm", "mail","web"],
    "data": [
        "security/ir.model.access.csv",

        # Acción client para RedirectWarning
        "views/action_get_geo.xml",

        # Vistas (si las usas)
        "views/calendar_event_view.xml",
    ],
    "assets": {
        "web.assets_backend": [
            # JS que registra: registry.category("actions").add("calendar_user_geo", ...)
            "calendar_event_geo/static/src/js/calendar_user_geo.js",
        ],
    },
    "installable": True,
}
