from odoo import fields, models, api

class L10nEsAeatRealEstate(models.Model):
    _name = "l10n.es.aeat.real.estate"
    _description = "Inmueble AEAT"
    _rec_name = "reference"

    # Campos requeridos por el Modelo 180 (basado en tu CSV de exportación)
    partner_id = fields.Many2one('res.partner', string="Titular")
    
    # [15] Situación del inmueble
    real_estate_situation = fields.Selection(
        selection=[
            ('1', '1 - Inmueble con referencia catastral situado en España'),
            ('2', '2 - Inmueble con referencia catastral en País Vasco o Navarra'),
            ('3', '3 - Inmueble sin referencia catastral'),
            ('4', '4 - Inmueble situado en el extranjero'),
        ],
        string="Situación Inmueble",
        default='1',
        required=True
    )

    # [16] Referencia Catastral
    reference = fields.Char(string="Ref. Catastral", size=20, required=True)

    # Dirección del inmueble
    address_type = fields.Char(string="Tipo Vía (Siglas)", size=5, help="Ej: CL, AV, PZ...")
    address = fields.Char(string="Nombre Vía Pública", size=50, required=True)
    number_type = fields.Char(string="Tipo Numeración", size=3, default="NUM", help="NUM, KM, S/N...")
    number = fields.Integer(string="Número Casa")
    number_calification = fields.Char(string="Calificador Núm.", size=3)
    block = fields.Char(string="Bloque", size=3)
    portal = fields.Char(string="Portal", size=3)
    stairway = fields.Char(string="Escalera", size=3)
    floor = fields.Char(string="Piso/Planta", size=3)
    door = fields.Char(string="Puerta", size=3)
    complement = fields.Char(string="Complemento", size=40)
    
    city = fields.Char(string="Localidad/Población", size=30)
    state_id = fields.Many2one('res.country.state', string="Provincia")
    zip = fields.Char(string="Código Postal", size=5)

    # Helper para mostrar nombre amigable
    def name_get(self):
        result = []
        for record in self:
            name = f"[{record.reference}] {record.address or ''}"
            result.append((record.id, name))
        return result

    def action_import_mp_emplacements(self):
        """
        Importa emplazamientos desde mp.site.emplacement a l10n.es.aeat.real.estate
        """
        MpEmplacement = self.env['mp.site.emplacement']
        
        # Buscar emplazamientos con datos mínimos (Ref. Catastral y Propietario)
        emplacements = MpEmplacement.search([
            ('ref_catastral', '!=', False),
            ('owner_id', '!=', False)
        ])

        created_count = 0
        skipped_count = 0

        for emp in emplacements:
            # Evitar duplicados por referencia catastral
            existing = self.search([('reference', '=', emp.ref_catastral)], limit=1)
            
            if existing:
                skipped_count += 1
                continue

            # Mapeo de datos
            vals = {
                # 'partner_id': emp.owner_id.id,
                'reference': emp.ref_catastral,
                'real_estate_situation': '1',  # 1 - Inmueble en España con Ref. Catastral
                'address': emp.ubication or emp.name,
                'city': emp.city,
                'state_id': emp.state_id.id,
                # 'number_type': 'NUM',
                'address_type': 'CTRA',
                'zip': getattr(emp, 'zip', False), # Usamos getattr por seguridad si no existe en source
            }
            
            self.create(vals)
            created_count += 1

        # Notificación al usuario
        return 
        