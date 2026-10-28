import time
import unittest

import game


class RoundResultTests(unittest.TestCase):
    def setUp(self):
        self.room = game.new_room('easy')
        self.host = game.join(self.room, 'Mika')
        self.guest = game.join(self.room, 'Jo')
        game.start(self.room)
        # These tests isolate ordinary scoring; special-guest closure has its own tests.
        for order in self.room['orders']:
            for key in ('guest','bonus','penalty'): order.pop(key,None)

    def serve(self, token, ingredients):
        self.room['players'][token].update(x=12, y=4, held=ingredients)
        game.action(self.room, token, {'action': 'interact'})

    def finish(self):
        self.room['end'] = time.time()-1
        game.tick(self.room)
        return self.room['results']

    def test_win_has_team_winner_and_accurate_statistics(self):
        self.room['orders'][0]['recipe'] = 'Salad'
        self.serve(self.host, list(game.RECIPES['Salad']))
        self.serve(self.guest, ['bun'])
        self.room['orders'][0]['expires'] = time.time()-1
        game.tick(self.room)
        self.room['score'] = self.room['target']
        result = self.finish()
        self.assertTrue(result['won'])
        self.assertEqual(result['winner'], 'Kitchen crew')
        self.assertEqual(result['score'], result['target'])
        self.assertEqual(result['stats']['served'], 1)
        self.assertEqual(result['stats']['incorrect'], 1)
        self.assertEqual(result['stats']['expired'], 1)
        self.assertEqual(result['stats']['best_combo'], 1)
        self.assertEqual(result['chefs'][0], {'name': 'Chef Mika', 'served': 1})
        self.assertEqual(result['chefs'][1], {'name': 'Chef Jo', 'served': 0})

    def test_loss_does_not_invent_a_player_winner_and_freezes_result(self):
        result = self.finish()
        self.assertFalse(result['won'])
        self.assertIsNone(result['winner'])
        frozen = dict(result)
        self.serve(self.host, list(game.RECIPES['Salad']))
        game.tick(self.room)
        self.assertEqual(self.room['results'], frozen)
        self.assertEqual(self.room['score'], 0)

    def test_host_rematch_resets_results_and_stats_for_everyone(self):
        result = self.finish()
        with self.assertRaises(ValueError):
            game.action(self.room, self.guest, {'action': 'start'})
        game.action(self.room, self.host, {'action': 'start'})
        self.assertEqual(self.room['round_id'], result['round_id']+1)
        self.assertIsNone(self.room['results'])
        self.assertFalse(self.room['finished'])
        self.assertEqual(self.room['stats']['served'], 0)
        self.assertEqual(len(self.room['players']), 2)

    def test_demo_completion_has_practice_result_and_next_lesson_resets_it(self):
        room = game.new_room(demo=True)
        host = game.join(room, 'Trainee')
        game.start(room)
        room['players'][host].update(x=12, y=4, held=list(game.RECIPES['Salad']))
        game.action(room, host, {'action': 'interact'})
        self.assertTrue(room['results']['won'])
        self.assertTrue(room['results']['demo'])
        self.assertEqual(room['results']['stats']['served'], 1)
        game.action(room, host, {'action': 'next_demo'})
        self.assertIsNone(room['results'])
        self.assertEqual(room['demo_round'], 1)


if __name__ == '__main__':
    unittest.main()
