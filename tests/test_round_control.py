import unittest
from unittest.mock import patch
import game
import chaos


class PauseChaosTests(unittest.TestCase):
    def setUp(self):
        self.clock = patch('time.time',return_value=1000)
        self.now = self.clock.start()
        self.addCleanup(self.clock.stop)
        self.room = game.new_room()
        self.host = game.join(self.room,'Host')
        self.guest = game.join(self.room,'Guest')
        game.start(self.room)

    def test_pause_freezes_every_deadline_and_resume_preserves_remaining_time(self):
        room = self.room
        host, guest = room['players'][self.host],room['players'][self.guest]
        guest.update(held='tomato',task={'kind':'chop','end':1003})
        stove = next(s for s in room['stations'] if s['kind']=='stove')
        stove.update(item='meat',ready=1007)
        host.update(x=2,y=5,held='bun',facing=[1,0])
        game.action(room,self.host,{'action':'throw'})
        game.action(room,self.host,{'action':'pause'})
        self.now.return_value = 1100
        game.tick(room)
        self.assertEqual(room['end'],1150)
        self.assertEqual(guest['held'],'tomato')
        self.assertEqual(stove['item'],'meat')
        self.assertEqual(room['projectiles'][0]['travelled'],0)
        self.assertFalse(room['finished'])
        game.action(room,self.host,{'action':'pause'})
        self.assertFalse(room['paused'])
        self.assertEqual(room['end'],1250)
        self.assertEqual(guest['task']['end'],1103)
        self.assertEqual(stove['ready'],1107)
        self.assertEqual(room['orders'][0]['expires'],1160)
        self.assertEqual(room['projectiles'][0]['updated'],1100)
        self.now.return_value=1101
        game.tick(room)
        self.assertEqual(guest['held'],'tomato')

    def test_host_only_pause_blocks_gameplay_and_rematch(self):
        with self.assertRaises(ValueError): game.action(self.room,self.guest,{'action':'pause'})
        game.action(self.room,self.host,{'action':'pause'})
        for action in ({'action':'move','dx':1,'dy':0},{'action':'start'}):
            with self.assertRaises(ValueError): game.action(self.room,self.host,action)

    def test_explicit_pause_is_idempotent_for_repeated_menu_clicks(self):
        for _ in range(2):game.action(self.room,self.host,{'action':'pause','paused':True})
        self.assertTrue(self.room['paused'])
        for _ in range(2):game.action(self.room,self.host,{'action':'pause','paused':False})
        self.assertFalse(self.room['paused'])

    def test_station_shuffle_is_warned_and_preserves_items_and_collision_layout(self):
        room = self.room
        room['difficulty']='hard'
        chaos.reset(room,1000)
        occupied = {(s['x'],s['y']) for s in room['stations']}
        stoves = [s for s in room['stations'] if s['kind']=='stove']
        stoves[0].update(item='cooked meat',ready=1020)
        chaos.tick(room,1024)
        self.assertEqual(room['chaos']['phase'],'warning')
        self.assertFalse(any(s['motion'] for s in room['stations']))
        chaos.tick(room,1027)
        self.assertEqual(room['chaos']['phase'],'active')
        moving = [s for s in stoves if s['motion']]
        self.assertEqual(len(moving),2)
        original = [(s,s['x'],s['y'],s['item'],s['ready']) for s in moving]
        chaos.tick(room,1029)
        self.assertEqual(occupied,{(s['x'],s['y']) for s in room['stations']})
        for s,x,y,item,ready in original:
            self.assertNotEqual((s['x'],s['y']),(x,y))
            self.assertEqual((s['item'],s['ready']),(item,ready))
        self.now.return_value=1029
        game.action(room,self.host,{'action':'pause'})
        deadline = room['chaos']['end']
        self.now.return_value=1129
        game.action(room,self.host,{'action':'pause'})
        self.assertEqual(room['chaos']['end'],deadline+100)

    def test_difficulty_scales_surprises_and_demos_are_undisturbed(self):
        self.assertGreater(chaos.CHAOS['easy']['first'],chaos.CHAOS['chef-de-cuisine']['first'])
        self.assertGreater(chaos.CHAOS['easy']['interval'],chaos.CHAOS['chef-de-cuisine']['interval'])
        demo=game.new_room(demo=True)
        game.join(demo,'Trainee')
        game.start(demo)
        chaos.tick(demo,1100)
        self.assertIsNone(demo['chaos'])
