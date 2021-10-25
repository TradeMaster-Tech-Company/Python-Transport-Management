# Copyright 2017, Jarsa Sistemas, S.A. de C.V.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).


from datetime import datetime

from odoo.tests.common import TransactionCase


class TestTmsEvent(TransactionCase):

    def setUp(self):
        super().setUp()
        self.travel_id = self.env.ref("tms.tms_travel_01")

    def create_event(self):
        return self.env['tms.event'].create({
            'name': 'Test',
            'date': datetime.now(),
            'state': 'draft',
            'travel_id': self.travel_id.id
        })

    def test_10_tms_event_action_confirm(self):
        event = self.create_event()
        event.action_confirm()
        self.assertEqual(event.state, 'confirm')

    def test_20_tms_event_action_cancel(self):
        event = self.create_event()
        event.action_cancel()
        self.assertEqual(event.state, 'cancel')

    def test_30_tms_event_set_2_draft(self):
        event = self.create_event()
        event.action_confirm()
        event.set_2_draft()
        self.assertEqual(event.state, 'draft')
