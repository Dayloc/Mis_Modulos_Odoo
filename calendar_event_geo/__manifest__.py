{
    "name": "Calendar Event Geolocation 1.1",
    "version": "1.0",
    "depends": [
        "calendar",
        "crm",
        "mail"],
    "data": [
        "security/ir.model.access.csv",
        "views/calendar_event_action.xml",
        "views/calendar_event_view.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "calendar_event_geo/static/src/js/calendar_user_geo.js",
        ],
    },
    "installable": True,
}
