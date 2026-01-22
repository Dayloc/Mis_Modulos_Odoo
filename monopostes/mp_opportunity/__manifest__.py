{
    'name': 'Oportunidades de Mantenimiento y Proyectos',
    'version': '1.0',
    'summary': 'Gestión de oportunidades para mantenimiento y proyectos.',
    'sequence': 1,
    'description': """
Gestión de Oportunidades
========================
- Registro de nuevas oportunidades.
- Seguimiento del estado de las oportunidades.
- Vínculo con propietarios y comerciales.
- Enlaces a Google Maps.
    """,
    'category': 'Sales/CRM',

    'depends': ['base', 'mail','purchase','mp_site'],
    'data': [
        'security/groups.xml',
        'security/ir.model.access.csv',
        'data/mp_opportunity_sequence.xml',
        'views/mp_opportunity_views.xml',
        'views/mp_opportunity_menu.xml',
        'views/define_emplacement_wizard_views.xml',
        'views/purchase_order_form.xml',
    ],
    'demo': [],
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'LGPL-3',
    'icon': 'mp_opportunity/static/description/icon.png',
}