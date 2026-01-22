# Copyright 2025 Netkia - Carlos Sainz-Pardo
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).
{
    "name": "AEAT Modelo 180",
    "summary": "AEAT Modelo 180",
    "author": "Netkia Soluciones SLU, Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "website": "https://github.com/OCA/l10n-spain",
    "version": "1.0.0",
    "depends": [
        "l10n_es_aeat",
        "l10n_es_aeat_mod115",
        "mp_site",
        # "l10n_es_reports",
    ],
    "data": [
        "data/aeat_export_mod180_line_data.xml",
        "data/aeat_export_mod180_data.xml",
        "security/ir.model.access.csv",
        "security/l10n_es_aeat_mod180_security.xml",
        "views/recipient_record_views.xml",
        "views/account_move_line_views.xml",
        "data/mod180.xml",
        "views/mod180_view.xml",
        "views/l10n_es_aeat_real_estate_views.xml",
        "views/account_move_views.xml",
    ],
    "installable": True,
}
