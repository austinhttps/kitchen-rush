import unittest
from unittest.mock import patch
import game
import dining


class DrinksDiningTests(unittest.TestCase):
    def test_drinks_only_exist_on_medium_plus_and_demo_stays_food_only(self):
        for difficulty in ('easy','medium','hard','expert','chef','chef-de-cuisine'):
            room=game.new_room(difficulty)
            self.assertEqual('Lemonade' in game.menu(room),difficulty!='easy')
            self.assertEqual(any(s['kind']=='drinks' for s in room['stations']),difficulty!='easy')
        self.assertNotIn('Lemonade',game.menu(game.new_room(demo=True)))

    def test_human_mixes_serves_cup_and_seats_customer_without_using_a_plate(self):
        with patch('time.time',return_value=1000) as now:
            room=game.new_room('medium');host=game.join(room,'Host');game.start(room)
            room['orders']=[{'id':'drink','recipe':'Lemonade','patience':60,'expires':1060}]
            room['next_order']=1200
            player=room['players'][host];player.update(x=10,y=6)
            game.action(room,host,{'action':'interact'})
            self.assertEqual(player['held'],'empty cup');self.assertEqual(player['task']['kind'],'mix')
            now.return_value=1002.99;game.tick(room);self.assertEqual(player['held'],'empty cup')
            now.return_value=1003;game.tick(room);self.assertEqual(player['held'],'lemonade')
            with self.assertRaises(ValueError):game.action(room,host,{'action':'throw'})
            player.update(x=12,y=4);game.action(room,host,{'action':'interact'})
            self.assertEqual(room['stats']['drinks'],1);self.assertIsNone(player['held'])
            self.assertEqual((room['plates'],room['dirty']),(4,0));self.assertGreater(room['score'],100)
            self.assertEqual(len(room['diners']),1);self.assertEqual(room['diners'][0]['recipe'],'Lemonade')
            game.action(room,host,{'action':'pause'});now.return_value=1103;game.action(room,host,{'action':'pause'})
            self.assertEqual(room['diners'][0]['leave_at'],1115)
            dining.tick(room,1115);self.assertEqual(room['diners'],[])

    def test_four_seats_never_overlap_and_customers_leave_after_twelve_seconds(self):
        room=game.new_room()
        for i in range(5):dining.seat(room,{'id':str(i),'recipe':'Salad'},1000)
        self.assertEqual(len(room['diners']),4);self.assertEqual(len({d['seat'] for d in room['diners']}),4)
        dining.tick(room,1012);self.assertEqual(room['diners'],[])
        dining.seat(room,{'id':'next','recipe':'Burger','guest':'VIP'},1012)
        self.assertEqual(room['diners'][0]['guest'],'VIP')
