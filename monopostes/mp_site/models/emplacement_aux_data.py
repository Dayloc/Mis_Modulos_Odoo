# -*- coding: utf-8 -*-
from odoo import models, fields

class MpFocusNumber(models.Model):
    _name = 'mp.emplacement.focus.number'
    _description = 'Número de Focos'

    name = fields.Char(string='Nº Focos', required=True)


class MpTowerHeight(models.Model):
    _name = 'mp.emplacement.tower.height'
    _description = 'Altura de Torretas'

    name = fields.Char(string='Altura Torretas', required=True)


class MpConcreteType(models.Model):
    _name = 'mp.emplacement.concrete'
    _description = 'Tipo de Hormigón'

    name = fields.Char(string='Tipo de Hormigón', required=True)


class MpGroundHeight(models.Model):
    _name = 'mp.emplacement.ground.height'
    _description = 'Altura desde el Suelo'

    name = fields.Char(string='Altura Suelo', required=True)
