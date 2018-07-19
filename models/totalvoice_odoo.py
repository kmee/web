# -*- coding: utf-8 -*-

from odoo import models, fields, api

from totalvoice.cliente import Cliente
import json

client = Cliente("49c31c417f21915f1ced29182c5dea56", 'api.totalvoice.com.br')

class TotalVoiceBase(models.Model):
    _name = 'totalvoice.base'

    # number_from = fields.Char(
    #     string="Your Number",
    #     required=True,
    #     help="Provide your TotalVoice's number",
    # )

    number_to = fields.Char(
        string="Contact Number",
        required=True,
        help="Provide your contact's number",
    )

    message = fields.Char(
        string="Message",
        required=True,
        size=160,
    )

    response = fields.Text(
        string="Sender,Receiver,Message",
        readonly=True,
    )

    @api.multi
    def send_sms(self):
        for record in self:
            response = client.sms.enviar(record.number_to, record.message, resposta_usuario=True)

            record.response = response

    @api.multi
    def get_sms_status(self):
        for record in self:
            response = json.loads(record.response)
            sms = json.loads(client.sms.get_by_id(str(response['dados']['id'])))
            print(sms)
