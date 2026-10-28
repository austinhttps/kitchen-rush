import json
import unittest
from unittest.mock import patch
import game
from rooms import enter
from public_state import snapshot


class RestartSetupTests(unittest.TestCase):
    def setUp(self):
        self.clock=patch('time.time',return_value=1000);self.clock.start();self.addCleanup(self.clock.stop)
        self.room=game.new_room('medium');self.host=game.join(self.room,'Host');self.guest=game.join(self.room,'Guest')
        game.action(self.room,self.host,{'action':'bots','count':2});game.start(self.room)

    def test_restart_changes_difficulty_and_removes_selected_human_and_bot_atomically(self):
        guest_id=self.room['players'][self.guest]['id']
        bot_id=next(p['id'] for p in self.room['players'].values() if p['bot'])
        old_round=self.room['round_id']
        game.action(self.room,self.host,{'action':'restart','difficulty':'easy','remove':[guest_id,bot_id]})
        self.assertEqual(self.room['difficulty'],'easy');self.assertEqual(self.room['round_id'],old_round+1)
        self.assertEqual(len(self.room['players']),2);self.assertEqual(self.room['bot_count'],1)
        self.assertEqual(self.room['target'],600);self.assertEqual(self.room['launch_at'],1004)
        self.assertFalse(any(s['kind']=='drinks' for s in self.room['stations']))
        with self.assertRaisesRegex(ValueError,'removed'):
            enter({'AAA-123':self.room},'/api/rejoin',{'room':'AAA-123','token':self.guest})
        public=json.dumps(snapshot(self.room,self.host,game.RECIPES))
        self.assertNotIn(self.guest,public);self.assertNotIn('removed_tokens',public)

    def test_invalid_config_and_guest_attempts_leave_round_unchanged(self):
        current=self.room['round_id'];players=list(self.room['players'])
        attempts=[{'difficulty':'unknown'},{'remove':[self.room['players'][self.host]['id']]},
                  {'remove':['unknown']},{'remove':'bad'},{'remove':[42]}]
        for extra in attempts:
            with self.assertRaises(ValueError):game.action(self.room,self.host,{'action':'restart',**extra})
            self.assertEqual(self.room['round_id'],current);self.assertEqual(list(self.room['players']),players)
        with self.assertRaises(ValueError):game.action(self.room,self.guest,{'action':'restart','difficulty':'easy'})

    def test_restart_can_add_drink_station_when_moving_up_from_easy(self):
        game.action(self.room,self.host,{'action':'restart','difficulty':'easy'})
        game.action(self.room,self.host,{'action':'restart','difficulty':'hard'})
        self.assertTrue(any(s['kind']=='drinks' for s in self.room['stations']))
        self.assertIn('Lemonade',snapshot(self.room,self.host,game.RECIPES)['recipes'])
