import time
import unittest
from unittest.mock import patch

import game
from modes import DIFFICULTIES, demo_data


class FeatureTests(unittest.TestCase):
    def test_chef_prefix_is_added_once_and_nickname_is_bounded(self):
        room = game.new_room()
        for nickname, expected in [('Mika', 'Chef Mika'), (' Chef Mika ', 'Chef Mika'),
                                   ('Chef chef Jo', 'Chef Jo'), ('', 'Chef Rookie')]:
            token = game.join(room, nickname)
            self.assertEqual(room['players'][token]['name'], expected)

    def test_difficulty_changes_gameplay_for_every_level(self):
        for difficulty, config in DIFFICULTIES.items():
            with self.subTest(difficulty=difficulty), patch('time.time', return_value=1000):
                room = game.new_room(difficulty)
                for name in ('A', 'B', 'C'):
                    game.join(room, name)
                game.start(room)
                self.assertEqual(room['target'], config['target']+config['extra'])
                self.assertEqual(room['orders'][0]['expires'], 1000+config['patience'])
                self.assertEqual(room['next_order'], 1000+config['interval'])
                stove = next(s for s in room['stations'] if s['kind'] == 'stove')
                stove.update(item='cooked meat', ready=1000-config['burn']-1)
                game.tick(room)
                self.assertEqual(stove['item'], 'fire')

    def test_difficulty_is_host_only_and_locked_during_round(self):
        room = game.new_room()
        host, guest = game.join(room, 'A'), game.join(room, 'B')
        with self.assertRaises(ValueError):
            game.action(room, guest, {'action': 'difficulty', 'difficulty': 'easy'})
        game.action(room, host, {'action': 'difficulty', 'difficulty': 'expert'})
        game.start(room)
        with self.assertRaises(ValueError):
            game.action(room, host, {'action': 'difficulty', 'difficulty': 'easy'})
        self.assertEqual(room['difficulty'], 'expert')
        with self.assertRaises(ValueError):
            game.new_room('unknown')

    def test_food_burns_after_shortened_difficulty_window_not_before(self):
        expected=[15,10,8,6,5,4]
        for (difficulty,config),seconds in zip(DIFFICULTIES.items(),expected):
            with self.subTest(difficulty=difficulty),patch('time.time',return_value=1000) as clock:
                self.assertEqual(config['burn'],seconds)
                room=game.new_room(difficulty)
                game.join(room,'Host')
                game.start(room)
                stove=next(s for s in room['stations'] if s['kind']=='stove')
                stove.update(item='cooked fish',ready=1000)
                clock.return_value=1000+seconds
                game.tick(room)
                self.assertEqual(stove['item'],'cooked fish')
                clock.return_value+=.05
                game.tick(room)
                self.assertEqual(stove['item'],'fire')

    def test_three_demo_rounds_are_isolated_and_end_on_correct_service(self):
        room = game.new_room(demo=True)
        token = game.join(room, 'Student')
        real_room = game.new_room()
        game.start(room)
        with self.assertRaises(ValueError):
            game.join(room, 'Guest')
        with self.assertRaises(ValueError):
            game.action(room, token, {'action': 'next_demo'})
        for index, recipe in enumerate(game.menu(room)):
            lesson = demo_data(room)
            self.assertEqual(lesson['round'], index+1)
            self.assertEqual(room['orders'][0]['recipe'], recipe)
            self.assertEqual(len(room['orders']), 1)
            if index == 2:
                self.assertEqual(room['plates'], 0)
                self.assertEqual(room['dirty'], 2)
            player = room['players'][token]
            player.update(x=12, y=4, held=list(game.RECIPES[recipe]))
            game.action(room, token, {'action': 'interact'})
            self.assertTrue(room['finished'])
            self.assertGreaterEqual(room['score'], room['target'])
            if index < 2:
                game.action(room, token, {'action': 'next_demo'})
        with self.assertRaises(ValueError):
            game.action(room, token, {'action': 'next_demo'})
        self.assertEqual(real_room['score'], 0)
        self.assertFalse(real_room['started'])

    def test_demo_timeout_can_retry_or_continue(self):
        room = game.new_room(demo=True)
        host = game.join(room, 'A')
        game.start(room)
        room['end'] = time.time()-1
        game.tick(room)
        self.assertTrue(room['finished'])
        game.action(room, host, {'action': 'start'})
        self.assertEqual(room['demo_round'], 0)
        self.assertFalse(room['finished'])
        room['end'] = time.time()-1
        game.action(room, host, {'action': 'next_demo'})
        self.assertEqual(room['demo_round'], 1)

    def test_demo_success_allows_learning_from_mistakes(self):
        room = game.new_room(demo=True)
        host = game.join(room, 'A')
        game.start(room)
        player = room['players'][host]
        player.update(x=12, y=4, held=['bun'])
        game.action(room, host, {'action': 'interact'})
        player['held'] = list(game.RECIPES['Salad'])
        game.action(room, host, {'action': 'interact'})
        self.assertTrue(room['demo_served'])
        self.assertEqual(room['events'][-1]['message'], 'Practice dish complete!')

    def test_alerts_are_emitted_once_for_cook_fire_and_round_end(self):
        room = game.new_room()
        game.join(room, 'A')
        game.start(room)
        stove = next(s for s in room['stations'] if s['kind'] == 'stove')
        stove.update(item='meat', ready=time.time()-1)
        game.tick(room)
        self.assertIn('ready', room['events'][-1]['message'])
        count = room['event_id']
        game.tick(room)
        self.assertEqual(room['event_id'], count)
        stove['ready'] = time.time()-11
        game.tick(room)
        self.assertIn('Fire', room['events'][-1]['message'])
        count = room['event_id']
        game.tick(room)
        self.assertEqual(room['event_id'], count)
        room['end'] = time.time()-1
        game.tick(room)
        count = room['event_id']
        game.tick(room)
        self.assertEqual(room['event_id'], count)


if __name__ == '__main__':
    unittest.main()
