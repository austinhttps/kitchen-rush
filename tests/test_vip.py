import unittest
from unittest.mock import patch
import game
import vip
from public_state import snapshot


class GuestTests(unittest.TestCase):
    def setUp(self):
        self.clock=patch('time.time',return_value=1000)
        self.now=self.clock.start()
        self.addCleanup(self.clock.stop)
        self.room=game.new_room('medium')
        self.host=game.join(self.room,'Host')
        game.start(self.room,countdown=True)
        self.now.return_value=1004

    def special_only(self):
        order=next(o for o in self.room['orders'] if 'guest' in o)
        self.room['orders']=[order]
        self.room['players'][self.host].update(x=12,y=4)
        return order,self.room['players'][self.host]

    def test_correct_service_adds_labelled_bonus_to_standard_score(self):
        order,player=self.special_only()
        player['held']=list(game.RECIPES[order['recipe']])
        game.action(self.room,self.host,{'action':'interact'})
        self.assertEqual(self.room['score'],100+30+order['bonus'])
        self.assertEqual(self.room['stats']['vip_served'],1)
        self.assertEqual(self.room['stats']['vip_missed'],0)

    def test_wrong_dish_for_front_special_guest_removes_it_and_charges_once(self):
        order,player=self.special_only()
        player['held']=['bun']
        game.action(self.room,self.host,{'action':'interact'})
        self.assertEqual(self.room['score'],-order['penalty'])
        self.assertEqual(self.room['orders'],[])
        self.assertEqual(self.room['stats']['vip_missed'],1)
        self.room['end']=1004
        game.tick(self.room)
        self.assertEqual(self.room['score'],-order['penalty'])

    def test_expiry_uses_guest_penalty_and_resets_combo(self):
        order,_=self.special_only()
        order['expires']=1004
        self.room['combo']=4
        game.tick(self.room)
        self.assertEqual(self.room['score'],-order['penalty'])
        self.assertEqual(self.room['stats']['expired'],1)
        self.assertEqual(self.room['stats']['vip_missed'],1)
        self.assertEqual(self.room['combo'],1)

    def test_buzzer_penalty_precedes_win_calculation_and_frozen_result(self):
        order,_=self.special_only()
        self.room.update(score=self.room['target'],end=1004)
        game.tick(self.room)
        result=self.room['results']
        self.assertFalse(result['won'])
        self.assertEqual(result['score'],self.room['target']-order['penalty'])
        self.assertEqual(result['stats']['vip_missed'],1)
        game.tick(self.room)
        self.assertEqual(self.room['score'],result['score'])

    def test_counts_rewards_and_critics_scale_without_exceeding_queue_cap(self):
        for difficulty,(count,bonus,penalty) in vip.VISITS.items():
            room=game.new_room(difficulty)
            token=game.join(room,'Host')
            game.start(room)
            self.assertEqual(room['vip_visits'],1)
            self.assertEqual(room['orders'][-1]['bonus'],bonus)
            self.assertEqual(room['orders'][-1]['penalty'],penalty)
            first_vip_at=room['next_vip']
            capacity=game.settings(room)['max_customers']
            self.now.return_value=first_vip_at
            room['orders']=[game.ticket(room) for _ in range(capacity-1)]
            for order in room['orders']:
                order['expires']=self.now.return_value+100
            room['next_order']=self.now.return_value
            game.tick(room)
            self.assertEqual(len(room['orders'])+len(room['diners']),capacity)
            room['vip_visits']=1
            room['next_vip']=first_vip_at
            for visit in range(1,count):
                room['orders']=[]
                self.now.return_value=room['next_vip']
                vip.tick(room,self.now.return_value,game.ticket)
                special=room['orders'][0]
                self.assertEqual(special['guest'],'Critic' if visit%2 else 'VIP')
                self.assertEqual(special['bonus'],bonus*3//2 if visit%2 else bonus)
                self.assertEqual(special['penalty'],penalty*2 if visit%2 else penalty)
            room['orders']=[]
            vip.tick(room,room['next_vip']+100,game.ticket)
            self.assertEqual(room['orders'],[])
            self.assertEqual(room['vip_visits'],count)
            self.assertEqual(snapshot(room,token,game.RECIPES)['vip_visits'],count)

    def test_pause_shifts_visits_and_demo_has_no_special_guests(self):
        next_visit=self.room['next_vip']
        game.action(self.room,self.host,{'action':'pause'})
        self.now.return_value+=100
        game.action(self.room,self.host,{'action':'pause'})
        self.assertEqual(self.room['next_vip'],next_visit+100)
        demo=game.new_room(demo=True)
        game.join(demo,'Trainee')
        game.start(demo)
        vip.tick(demo,9999,game.ticket)
        self.assertTrue(all('guest' not in o for o in demo['orders']))
