import time
import unittest
import game


class KitchenTests(unittest.TestCase):
    def setUp(self):
        self.room = game.new_room()
        self.a = game.join(self.room, 'Alice')
        self.b = game.join(self.room, 'Bob')
        game.start(self.room)

    def test_shared_salad_service_and_washing(self):
        room = self.room
        p = room['players'][self.a]
        counter = next(s for s in room['stations'] if s['kind'] == 'counter')
        p.update(x=3, y=7, held=None)
        game.interact(room, p)
        self.assertEqual(p['held'], [])
        p.update(x=counter['x'], y=counter['y']-1)
        game.interact(room, p)
        for ingredient in ('tomato', 'lettuce'):
            p.update(x=1, y=3, held=ingredient)
            game.interact(room, p)
            p['task']['end'] = time.time()-1
            game.tick(room)
            p.update(x=counter['x'], y=counter['y']-1)
            game.interact(room, p)
        other = room['players'][self.b]
        other.update(x=counter['x'], y=counter['y']-1)
        game.interact(room, other)
        room['orders'][0]['recipe'] = 'Salad'
        other.update(x=12, y=4)
        game.interact(room, other)
        self.assertGreaterEqual(room['score'], 100)
        self.assertEqual(room['combo'], 2)
        self.assertEqual(room['dirty'], 1)
        other.update(x=5, y=7)
        game.interact(room, other)
        other['task']['end'] = time.time()-1
        game.tick(room)
        self.assertEqual(room['plates'], 4)

    def test_wrong_and_expired_orders(self):
        p = self.room['players'][self.a]
        p.update(x=12, y=4, held=['bun'])
        game.interact(self.room, p)
        self.assertEqual(self.room['score'], -50)
        self.room['orders'][0]['expires'] = time.time()-1
        game.tick(self.room)
        self.assertEqual(self.room['score'], -75)

    def test_cooking_and_fire(self):
        p = self.room['players'][self.a]
        p.update(x=5, y=3, held='chopped meat')
        game.interact(self.room, p)
        stove = next(s for s in self.room['stations'] if s['kind'] == 'stove')
        stove['ready'] = time.time()-1
        game.tick(self.room)
        self.assertEqual(stove['item'], 'cooked meat')
        stove['ready'] = time.time()-16
        game.tick(self.room)
        self.assertEqual(stove['item'], 'fire')
        p['held'] = 'extinguisher'
        game.action(self.room, self.a, {'action': 'interact'})
        self.assertIsNone(stove['item'])

    def test_only_host_can_start(self):
        with self.assertRaises(ValueError):
            game.action(self.room, self.b, {'action': 'start'})

    def test_wall_window_has_a_clear_front_approach(self):
        player=self.room['players'][self.a]
        player.update(x=11.9,y=4,held=[])
        self.assertEqual(game.nearest(self.room,player)['kind'],'serve')


if __name__ == '__main__':
    unittest.main()
