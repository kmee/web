# -*- coding: utf-8 -*-

from odoo import models, fields, api
from datetime import datetime

from totalvoice.cliente import Cliente
import json
import re

client = Cliente("49c31c417f21915f1ced29182c5dea56", 'api.totalvoice.com.br')
date_format = '%Y-%m-%dT%H:%M:%S.%fZ'

class TotalVoiceMessage(models.Model):
    _name = 'totalvoice.message'

    sms_id = fields.Integer(
        string='SMS ID',
        readonly=True,
        help="SMS ID provided by Total Voice's server"
    )

    coversation_id = fields.Many2one(
        comodel_name='totalvoice.base',
        string='TotalVoice Conversation',
    )

    message = fields.Text(
        string='Message',
        size=160,
    )

    message_date = fields.Datetime(
        string='Message Date',
        readonly=True,
    )


class TotalVoiceBase(models.Model):
    _name = 'totalvoice.base'
    _inherits = {'totalvoice.message': 'message_id'}
    _rec_name = 'partner_id'

    partner_id = fields.Many2one(
        comodel_name='res.partner',
        string='Contact',
        required=True,
        domain="[('mobile', '!=', False)]",
    )

    image = fields.Binary(
        string='Contact Avatar',
        related='partner_id.image',
        readonly=True,
    )

    image_medium = fields.Binary(
        related='partner_id.image_medium',
    )

    image_small = fields.Binary(
        related='partner_id.image_small',
    )

    message_id = fields.Many2one(
        comodel_name='totalvoice.message',
        string='message_id',
        readonly=True,
        invisible=True,
        required=True,
        ondelete='cascade',
    )

    answer_ids = fields.One2many(
        comodel_name='totalvoice.message',
        inverse_name='coversation_id',
        string='Contact Answers',
        readonly=True,
        invisible=True,
    )

    state = fields.Selection([
        ('draft', 'Draft'),
        ('sent', 'Sent'),
        ('waiting', 'Waiting Answer'),
        ('done', 'Done'),
        ('failed', 'Failed')],
        default='draft',
        readonly=True,
    )

    number_to = fields.Char(
        string='Phone',
        related='partner_id.mobile',
        readonly=True,
        help="Contact's number",
    )

    wait_for_answer = fields.Boolean(
        default=False,
    )

    server_message = fields.Char(
        string='Server Message',
        readonly=True,
        size=160,
    )

    @api.multi
    def send_sms(self):
        for record in self:

            mobile = re.sub('\D', '', record.number_to)
            response = client.sms.enviar(
                mobile, record.message,
                resposta_usuario=record.wait_for_answer
            )

            response = json.loads(response)

            data = response.get('dados')
            record.server_message = 'Motivo: ' + str(response.get('motivo')) + \
                                    ' - ' + response.get('mensagem')

            if not response.get('sucesso'):
                record.state = 'failed'
                return
            record.state = 'sent'

            if record.wait_for_answer:
                record.state = 'waiting'

            record.sms_id = data.get('id')

            record.message_date = fields.Datetime.now()

    @api.multi
    def get_sms_status(self):
        for record in self:
            sms = json.loads(client.sms.get_by_id(str(record.sms_id)))
            data = sms.get('dados')
            answers = data.get('respostas')

            if answers:
                record.state = 'done'
                for answer in answers:
                    if answer['id'] in record.answer_ids.mapped('sms_id'):
                        continue
                    new_answer = {
                        'message_date': datetime.strptime(
                            answer['data_resposta'], date_format),
                        'sms_id': answer['id'],
                        'message': answer['resposta'],
                        'coversation_id': record.id,
                    }
                    self.env['totalvoice.message'].create(new_answer)
