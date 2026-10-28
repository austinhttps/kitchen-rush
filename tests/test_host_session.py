import unittest
from unittest.mock import patch
import game
from rooms import enter
from public_state import snapshot
import json


class HostSessionTests(unittest.TestCase):
    def test_countdown_keeps_the_full_round_and_order_patience(self):
        with patch('time.time',return_value=1000) as now:
            room=game.new_room()
            host=game.join(room,'Host')
            game.action(room,host,{'action':'start'})
            self.assertEqual(room['launch_at'],1004)
            self.assertEqual(room['end'],1154)
            self.assertEqual(room['orders'][0]['expires'],1064)
            now.return_value=1002
            game.action(room,host,{'action':'move','dx':1,'dy':0})
            self.assertEqual(room['players'][host]['x'],5.5)
            with self.assertRaises(ValueError): game.action(room,host,{'action':'pause'})
            now.return_value=1004.1
            game.action(room,host,{'action':'move','dx':1,'dy':0})
            self.assertGreater(room['players'][host]['x'],5.5)

    def test_host_can_restart_and_end_but_guest_cannot(self):
        room=game.new_room()
        host=game.join(room,'Host');guest=game.join(room,'Guest')
        game.start(room)
        for kind in ('restart','end'):
            with self.assertRaises(ValueError): game.action(room,guest,{'action':kind})
        room['score']=123
        old_round=room['round_id']
        game.action(room,host,{'action':'restart'})
        self.assertEqual(room['round_id'],old_round+1)
        self.assertEqual(room['score'],0)
        game.action(room,host,{'action':'end'})
        self.assertTrue(room['finished'])
        self.assertIsNotNone(room['results'])

    def test_rejoin_reuses_same_chef_without_consuming_another_slot(self):
        rooms={}
        host=enter(rooms,'/api/create',{'name':'Original'})
        room=rooms[host['room']]
        player=room['players'][host['token']]
        player.update(held='bun',x=3,y=5)
        restored=enter(rooms,'/api/rejoin',host)
        self.assertEqual(restored,host)
        self.assertEqual(len(room['players']),1)
        self.assertEqual((player['held'],player['x'],player['y']),('bun',3,5))
        with self.assertRaises(ValueError): enter(rooms,'/api/rejoin',{'room':host['room'],'token':'invalid'})

    def test_public_state_hides_authentication_tokens_from_other_chefs(self):
        room=game.new_room()
        host=game.join(room,'Host');guest=game.join(room,'Guest')
        state=snapshot(room,guest,game.RECIPES)
        self.assertNotIn(host,json.dumps(state))
        self.assertNotIn(guest,json.dumps(state))
        self.assertEqual(state['you'],room['players'][guest]['id'])
        self.assertNotEqual(state['host'],host)
