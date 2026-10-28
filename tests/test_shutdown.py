import unittest
from unittest.mock import patch
import game
import outcomes


class ShutdownTests(unittest.TestCase):
    def setUp(self):
        self.clock=patch('time.time',return_value=1000)
        self.now=self.clock.start();self.addCleanup(self.clock.stop)
        self.room=game.new_room('medium');self.host=game.join(self.room,'Host');game.start(self.room)
        self.room['orders']=[{'id':'ordinary','recipe':'Salad','patience':60,'expires':1060}]
        self.player=self.room['players'][self.host]
        self.player.update(x=12,y=4)

    def test_wrong_service_hits_floor_immediately_and_freezes_further_actions(self):
        self.room['score']=-150;self.player['held']=['bun']
        game.action(self.room,self.host,{'action':'interact'})
        self.assertTrue(self.room['finished']);self.assertEqual(self.room['score'],-200)
        self.assertFalse(self.room['results']['won']);self.assertIn('−200',self.room['results']['reason'])
        frozen=dict(self.room['results']);self.player['held']=list(game.RECIPES['Salad'])
        game.action(self.room,self.host,{'action':'interact'})
        self.assertEqual(self.room['results'],frozen);self.assertEqual(self.room['score'],-200)

    def test_large_expiry_penalty_is_clamped_and_ends_before_bot_work(self):
        self.room['score']=-199;self.room['orders'][0]['expires']=1000
        game.tick(self.room)
        self.assertEqual(self.room['score'],-200);self.assertTrue(self.room['finished'])
        self.assertEqual(self.room['results']['stats']['expired'],1)

    def ignite(self):
        stove=next(s for s in self.room['stations'] if s['kind']=='stove')
        stove.update(item='fire',ready=990,fire_since=1000,fire_alerts=[])
        return stove

    def test_sustained_fire_warns_then_forces_loss_even_above_target(self):
        stove=self.ignite();self.room['score']=9999
        self.now.return_value=1010;game.tick(self.room)
        self.assertEqual(stove['fire_alerts'],[10]);self.assertFalse(self.room['finished'])
        self.now.return_value=1015;game.tick(self.room)
        self.assertEqual(stove['fire_alerts'],[10,5])
        self.now.return_value=1019.99;game.tick(self.room);self.assertFalse(self.room['finished'])
        self.now.return_value=1020;game.tick(self.room)
        self.assertTrue(self.room['finished']);self.assertFalse(self.room['results']['won'])
        self.assertIn('20 seconds',self.room['results']['reason'])

    def test_extinguishing_clears_shutdown_and_pause_preserves_fire_time(self):
        stove=self.ignite();game.tick(self.room)
        game.action(self.room,self.host,{'action':'pause'})
        self.now.return_value=1100;game.action(self.room,self.host,{'action':'pause'})
        self.assertEqual(stove['fire_since'],1100);self.assertEqual(self.room['fire_deadline'],1120)
        self.now.return_value=1119;self.player.update(x=stove['x'],y=stove['y']-1,held='extinguisher')
        game.action(self.room,self.host,{'action':'interact'})
        self.assertIsNone(stove['item']);self.assertEqual(stove['fire_since'],0)
        self.assertEqual(self.room['fire_deadline'],0)
        self.now.return_value=1121;game.tick(self.room);self.assertFalse(self.room['finished'])

    def test_demos_keep_forgiving_rules_and_restart_resets_shutdown(self):
        demo=game.new_room(demo=True);game.join(demo,'Trainee');game.start(demo)
        demo['score']=-500;self.assertTrue(outcomes.check(demo,1030));self.assertFalse(demo['finished'])
        self.room['score']=-200;game.tick(self.room)
        game.action(self.room,self.host,{'action':'restart','difficulty':'easy'})
        self.assertFalse(self.room['finished']);self.assertEqual(self.room['score'],0)
        self.assertIsNone(self.room['failure_reason']);self.assertEqual(self.room['fire_deadline'],0)
