import unittest
from unittest.mock import patch
import game
import random
from bots import configure, host_token


class BotTests(unittest.TestCase):
    def test_optional_bot_slots_and_host_permissions(self):
        room = game.new_room()
        human = game.join(room,'Human')
        game.action(room,human,{'action':'bots','count':2})
        self.assertEqual(len(room['players']),3)
        self.assertEqual(host_token(room),human)
        bot = next(k for k,p in room['players'].items() if p['bot'])
        with self.assertRaises(ValueError): game.action(room,bot,{'action':'start'})
        game.start(room)
        with self.assertRaises(ValueError): configure(room,0,game.join)

    def test_bot_completes_each_recipe_through_real_station_actions(self):
        for recipe in game.RECIPES:
            with self.subTest(recipe=recipe),patch('time.time',return_value=1000) as clock:
                room = game.new_room('medium' if recipe=='Lemonade' else 'easy')
                human = game.join(room,'Human')
                configure(room,1,game.join)
                game.start(room)
                room['orders'] = [{'id':'lesson','recipe':recipe,'expires':1230,'patience':230}]
                room['next_order'] = 1230
                for step in range(2300):
                    clock.return_value = 1000+step*.1
                    game.tick(room)
                    if room['stats']['served']:
                        break
                bot = next(p for p in room['players'].values() if p['bot'])
                self.assertGreater(room['stats']['served'],0,repr(bot))
                self.assertEqual(room['stats']['incorrect'],0)
                self.assertEqual(room['players'][human]['served'],0)
                self.assertEqual(bot['served'],1)

    def test_three_bots_share_workstations_without_serving_wrong_orders(self):
        random.seed(7)
        with patch('time.time',return_value=1000) as clock:
            room = game.new_room('easy')
            game.join(room,'Host')
            configure(room,3,game.join)
            game.start(room)
            for step in range(2300):
                clock.return_value = 1000+step*.1
                game.tick(room)
            self.assertEqual(len(room['players']),4)
            self.assertGreaterEqual(room['stats']['served'],3)
            self.assertEqual(room['stats']['incorrect'],0)

    def test_bot_replans_after_counter_shuffle_with_recipe_in_progress(self):
        random.seed(9)
        with patch('time.time',return_value=1000) as clock:
            room=game.new_room('medium')
            game.join(room,'Host')
            configure(room,1,game.join)
            game.start(room)
            room['next_chaos']=1002
            room['orders']=[{'id':'moving-recipe','recipe':'Fish & rice','expires':1220,'patience':220}]
            room['next_order']=1220
            for step in range(1800):
                clock.return_value=1000+step*.1
                game.tick(room)
                if room['stats']['served']:break
            self.assertGreater(room['stats']['served'],0)
            self.assertEqual(room['stats']['incorrect'],0)


if __name__=='__main__': unittest.main()
