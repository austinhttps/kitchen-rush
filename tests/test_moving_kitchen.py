import unittest
from unittest.mock import patch
import game
import chaos
from bots import configure


class MovingKitchenTests(unittest.TestCase):
    def test_ingredient_prep_and_carousel_moves_preserve_station_identity_contents(self):
        for kind in ('shuffle_ingredients','shuffle_prep','carousel','rush'):
            with self.subTest(kind=kind):
                room=game.new_room('chef-de-cuisine')
                game.join(room,'Host')
                game.start(room)
                room['stations'][8].update(item='cooked fish',ready=1010)
                room['stations'][14]['item']=['bun']
                before={(s['x'],s['y']) for s in room['stations']}
                contents=[(s['item'],s['ready']) for s in room['stations']]
                indices=chaos.select_stations(room,kind)
                event={'stations':indices}
                chaos.begin_motion(room,event,1000)
                self.assertTrue(all(room['stations'][i]['motion'] for i in indices))
                if kind=='carousel':self.assertEqual(len(indices),len(room['stations'])-1)
                chaos.tick(room,1002)
                self.assertEqual(before,{(s['x'],s['y']) for s in room['stations']})
                self.assertEqual(contents,[(s['item'],s['ready']) for s in room['stations']])
                self.assertTrue(all(s['motion'] is None for s in room['stations']))

    def test_special_movements_are_difficulty_gated(self):
        self.assertNotIn('shuffle_ingredients',chaos.CHAOS['easy']['kinds'])
        self.assertIn('shuffle_ingredients',chaos.CHAOS['medium']['kinds'])
        self.assertIn('shuffle_prep',chaos.CHAOS['expert']['kinds'])
        self.assertIn('carousel',chaos.CHAOS['chef-de-cuisine']['kinds'])

    def test_serve_stays_beside_customers_through_every_movement_type(self):
        room=game.new_room('chef-de-cuisine')
        game.join(room,'Host')
        game.start(room)
        serve=next(s for s in room['stations'] if s['kind']=='serve')
        for kind in chaos.LABELS:
            for _ in range(10):
                indices=chaos.select_stations(room,kind)
                self.assertNotIn(room['stations'].index(serve),indices)
                if indices:
                    chaos.begin_motion(room,{'stations':indices},1000)
                    chaos.tick(room,1002)
                self.assertEqual((serve['x'],serve['y'],serve['motion']),(13,4,None))

    def test_bot_keeps_caught_food_and_delivers_it_to_a_counter(self):
        with patch('time.time',return_value=1000) as clock:
            room=game.new_room('easy')
            host=game.join(room,'Host')
            configure(room,1,game.join)
            game.start(room)
            room['orders']=[]
            bot=next(p for p in room['players'].values() if p['bot'])
            room['players'][host].update(x=2,y=5,held='tomato',facing=[1,0])
            bot.update(x=4,y=5,held=None)
            game.action(room,host,{'action':'throw'})
            clock.return_value=1000.4
            game.tick(room)
            self.assertEqual(bot['held'],'tomato')
            self.assertEqual(bot['stunned_until'],0)
            for step in range(200):
                clock.return_value=1000.5+step*.1
                game.tick(room)
                if bot['held'] is None:break
            self.assertTrue(any(s['item']=='tomato' for s in room['stations']))
            self.assertEqual(room['floor'],[])
