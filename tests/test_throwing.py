import time
import unittest
from unittest.mock import patch

import game


class ThrowingTests(unittest.TestCase):
    def setUp(self):
        self.room = game.new_room()
        self.host = game.join(self.room, 'Thrower')
        self.other = game.join(self.room, 'Receiver')
        game.start(self.room)

    def test_throw_in_open_space_does_not_require_an_empty_counter(self):
        p = self.room['players'][self.host]
        p.update(x=1, y=2, held='tomato', facing=[1, 0])
        game.action(self.room, self.host, {'action': 'throw'})
        self.assertIsNone(p['held'])
        self.assertEqual(self.room['projectiles'][0]['item'], 'tomato')

    def test_thrown_ingredient_stuns_another_player_then_lands_on_floor(self):
        p, other = self.room['players'][self.host], self.room['players'][self.other]
        p.update(x=2, y=5, held='tomato', facing=[1, 0])
        other.update(x=4, y=5, held=[])
        now = time.time()
        with patch('time.time', return_value=now):
            game.action(self.room, self.host, {'action': 'throw'})
        with patch('time.time', return_value=now+.4):
            game.tick(self.room)
            self.assertGreater(other['stunned_until'], now+.4)
            game.action(self.room, self.other, {'action': 'move', 'dx': 1, 'dy': 0})
            self.assertEqual(other['x'], 4)
        self.assertEqual(len(self.room['floor']), 1)
        self.assertEqual(self.room['floor'][0]['item'], 'tomato')
        with patch('time.time', return_value=now+2):
            game.action(self.room,self.other,{'action':'move','dx':1,'dy':0})
            self.assertGreater(other['x'],4)

    def test_floor_food_can_be_picked_up(self):
        p = self.room['players'][self.host]
        self.room['floor'] = [{'id':'floor-test','x':2,'y':5,'item':'chopped lettuce'}]
        p.update(x=2.2, y=5, held=None)
        game.action(self.room, self.host, {'action':'interact'})
        self.assertEqual(p['held'], 'chopped lettuce')
        self.assertEqual(self.room['floor'], [])

    def test_empty_handed_chef_catches_without_stun_or_duplicate_floor_food(self):
        p,other=self.room['players'][self.host],self.room['players'][self.other]
        p.update(x=2,y=5,held='tomato',facing=[1,0])
        other.update(x=4,y=5,held=None)
        now=time.time()
        with patch('time.time',return_value=now):game.action(self.room,self.host,{'action':'throw'})
        with patch('time.time',return_value=now+.4):game.tick(self.room)
        self.assertEqual(other['held'],'tomato')
        self.assertEqual(other['stunned_until'],0)
        self.assertEqual(self.room['floor'],[])
        self.assertEqual(self.room['projectiles'],[])

    def test_plates_cannot_be_thrown_and_round_reset_clears_floor(self):
        p=self.room['players'][self.host]
        p['held']=[]
        with self.assertRaises(ValueError): game.action(self.room,self.host,{'action':'throw'})
        self.room['floor']=[{'id':'leftover','x':2,'y':5,'item':'bun'}]
        self.room['end']=time.time()-1
        game.start(self.room)
        self.assertEqual(self.room['floor'],[])

    def test_centered_counter_catches_a_throw_in_flight(self):
        p=self.room['players'][self.host]
        p.update(x=3,y=8,held='bun',facing=[1,0])
        now=time.time()
        with patch('time.time',return_value=now):game.action(self.room,self.host,{'action':'throw'})
        with patch('time.time',return_value=now+.6):game.tick(self.room)
        counter=next(s for s in self.room['stations'] if s['kind']=='counter' and s['x']==7)
        self.assertEqual(counter['item'],'bun')
        self.assertEqual(self.room['floor'],[])

    def test_centered_stove_catches_compatible_food_and_starts_cooking(self):
        p=self.room['players'][self.host]
        p.update(x=2,y=4,held='chopped meat',facing=[1,0])
        now=time.time()
        with patch('time.time',return_value=now):game.action(self.room,self.host,{'action':'throw'})
        with patch('time.time',return_value=now+.45):game.tick(self.room)
        stove=next(s for s in self.room['stations'] if s['kind']=='stove' and s['x']==5)
        self.assertEqual(stove['item'],'meat')
        self.assertAlmostEqual(stove['ready'],now+.45+7)

    def test_near_miss_does_not_snap_onto_counter(self):
        p=self.room['players'][self.host]
        p.update(x=3,y=7.65,held='bun',facing=[1,0])
        now=time.time()
        with patch('time.time',return_value=now):game.action(self.room,self.host,{'action':'throw'})
        with patch('time.time',return_value=now+.7):game.tick(self.room)
        self.assertTrue(all(s['item'] is None for s in self.room['stations'] if s['kind']=='counter'))
        self.assertEqual(len(self.room['floor']),1)

    def test_uncookable_ingredient_can_land_on_stove_and_be_retrieved(self):
        p=self.room['players'][self.host]
        p.update(x=2,y=4,held='tomato',facing=[1,0])
        now=time.time()
        with patch('time.time',return_value=now):game.action(self.room,self.host,{'action':'throw'})
        with patch('time.time',return_value=now+.45):game.tick(self.room)
        stove=next(s for s in self.room['stations'] if s['kind']=='stove' and s['x']==5)
        self.assertEqual((stove['item'],stove['ready']),('tomato',0))
        p.update(x=5,y=3)
        game.interact(self.room,p)
        self.assertEqual(p['held'],'tomato')


if __name__ == '__main__':
    unittest.main()
