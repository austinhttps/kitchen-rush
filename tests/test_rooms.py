import unittest
from unittest.mock import patch
import game
from bots import configure
from rooms import enter, generate_code, normalize_code


class RoomTests(unittest.TestCase):
    def test_codes_are_six_mixed_characters_and_avoid_collisions(self):
        seen = {}
        for _ in range(100):
            code = generate_code(seen)
            self.assertRegex(code,r'^[A-Z0-9]{3}-[A-Z0-9]{3}$')
            self.assertTrue(any(c.isdigit() for c in code))
            self.assertTrue(any(c.isalpha() for c in code))
            self.assertNotIn(code,seen)
            seen[code]=True
        with patch('rooms.secrets.choice',side_effect=list('A2BC3DE4FG5H')):
            self.assertEqual(generate_code({'A2B-C3D':True}),'E4F-G5H')

    def test_join_normalizes_raw_or_formatted_codes(self):
        self.assertEqual(normalize_code(' a7k2qm '),'A7K-2QM')
        self.assertEqual(normalize_code('a7k-2qm'),'A7K-2QM')
        for invalid in ('abc','1234567','A--1234','ABC-12!'):
            with self.assertRaises(ValueError): normalize_code(invalid)

    def test_three_explicit_flows_and_name_free_demo(self):
        rooms = {}
        demo = enter(rooms,'/api/demo',{})
        self.assertTrue(rooms[demo['room']]['started'])
        self.assertEqual(rooms[demo['room']]['players'][demo['token']]['name'],'Chef Trainee')
        host = enter(rooms,'/api/create',{'name':'Host','difficulty':'easy','bots':1})
        guest = enter(rooms,'/api/join',{'name':'Guest','room':host['room'].lower().replace('-',''),'difficulty':'chef','bots':3})
        self.assertEqual(guest['room'],host['room'])
        self.assertEqual(rooms[host['room']]['difficulty'],'easy')
        self.assertEqual(rooms[host['room']]['bot_count'],1)
        with self.assertRaises(ValueError): enter(rooms,'/api/join',{'name':'No code'})
        with self.assertRaises(ValueError): enter(rooms,'/api/create',{'name':''})

    def test_four_total_chefs_including_bots_and_failed_setup_is_atomic(self):
        room = game.new_room()
        game.join(room,'Host')
        configure(room,3,game.join)
        self.assertEqual(len(room['players']),4)
        with self.assertRaises(ValueError): game.join(room,'Fifth chef')
        with self.assertRaises(ValueError): configure(room,4,game.join)
        rooms = {}
        with self.assertRaises(ValueError): enter(rooms,'/api/create',{'name':'Host','bots':4})
        self.assertEqual(rooms,{})
