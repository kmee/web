# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError
from totalvoice.cliente import Cliente

import json

class ApiConfig(models.TransientModel):
    _name = 'totalvoice.api.config'
    _inherit = 'res.config.settings'

    api_key = fields.Char(
        string='API-KEY',
    )
    api_url = fields.Char(
        string='API-URL',
    )

    api_registered_partner_ids = fields.Many2many(
        comodel_name='res.partner',
        string='Registered Contacts (Partners)',
        readonly=True,
    )

    api_balance = fields.Float(
        string='Balance',
        readonly=True,
    )

    @api.model
    def default_get(self, fields):
        res = super(ApiConfig, self).default_get(fields)

        # api_balance
        try:
            res['api_balance'] = json.loads(
                self.get_client().minha_conta
                    .get_saldo()).get('dados', _raise=False).get('saldo')
        except Exception:
            res['api_balance'] = 0

        self.env['ir.config_parameter'].\
            set_param('api_balance', str(res['api_balance']))

        return res

    @api.model
    def get_default_values(self, fields):
        conf = self.env['ir.config_parameter']
        return {
            'api_key': conf.get_param('api_key'),
            'api_url': conf.get_param('api_url'),
            'api_balance': float(conf.get_param('api_balance')),
            'api_registered_partner_ids': json.loads(
                conf.get_param('api_registered_partner_ids') or '[]')
        }

    @api.one
    def set_values(self):
        conf = self.env['ir.config_parameter']
        conf.set_param('api_key', str(self.api_key))
        conf.set_param('api_url', str(self.api_url))
        conf.set_param('api_balance', str(self.api_balance))
        conf.set_param('api_registered_partner_ids',
                       str(self.api_registered_partner_ids.ids))

    def get_client(self, _raise=True):
        """
        :return: The Totalvoice Client Object
        """
        try:
            client = \
                Cliente(self.env['ir.config_parameter'].get_param('api_key'),
                        self.env['ir.config_parameter'].get_param('api_url'),)
        except Exception:
            if _raise:
                raise UserError(_('API-KEY and API-URL not configured'))

        return client


    def verify_registered_number(self, number):
        """
        Verifies if the specified number is already registered in
        TotalVoice for the configured account
        :param number: number to be verified
        :return: True if the number is already registered. Else if it's not
        """

        bina_report = json.loads(self.get_client().bina.get_relatorio())

        already_registered = \
            any(number == bina.get('numero_telefone')
                for bina in bina_report.get('dados').get('relatorio'))

        return True if already_registered else False

    def register_partner(self, partner, number):
        """
        Register a new partner in the totalvoice_odoo module configuration
        :param partner: partner to be registered
        """

        already_registered = \
            self.verify_registered_number(number)

        registered_partners = self.env['res.partner'].\
            browse(self.get_default_values(None).
                   get('api_registered_partner_ids'))

        if already_registered:
            if partner.totalvoice_number != number:
                partner.totalvoice_number = number

            if partner not in registered_partners:
                registered_partners += partner
                self.env['ir.config_parameter'].set_param(
                    'api_registered_partner_ids', registered_partners.ids)

    def remove_partner(self, partner):
        """
        Remove res_partner from the api_registered_partner_ids list
        """
        partner.totalvoice_number = False

        registered_partners = self.env['res.partner']. \
            browse(self.get_default_values(None).
                   get('api_registered_partner_ids'))
        registered_partners -= partner
        self.env['ir.config_parameter'].set_param(
            'api_registered_partner_ids', registered_partners.ids)
