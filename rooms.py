"""Explicit lobby flows and collision-safe, mixed alphanumeric room codes."""
import re
import secrets
import time
import game
from bots import configure
from config import MAX_BOTS

LETTERS = 'ABCDEFGHJKLMNPQRSTUVWXYZ'
DIGITS = '23456789'


def normalize_code(value):
    code = str(value).strip().upper()
    if not re.fullmatch(r'[A-Z0-9]{3}-?[A-Z0-9]{3}', code):
        raise ValueError('Enter a six-character room code, like A7K-2QM.')
    raw = code.replace('-', '')
    return raw[:3]+'-'+raw[3:]


def generate_code(existing):
    while True:
        raw = ''.join(secrets.choice(LETTERS+DIGITS) for _ in range(6))
        code = raw[:3]+'-'+raw[3:]
        if any(c in LETTERS for c in raw) and any(c in DIGITS for c in raw) and code not in existing:
            return code


def enter(rooms, path, data):
    if path == '/api/rejoin':
        code = normalize_code(data.get('room',''))
        room = rooms.get(code)
        token = str(data.get('token',''))
        if room is not None and token in room['disconnected_tokens']:
            raise ValueError('Your connection was inactive for 15 seconds, so the chef slot was released. Ask the host for a new invite.')
        if room is not None and token in room['removed_tokens']:
            raise ValueError('The host removed your chef from this kitchen. Ask for a new invite to join again.')
        if room is None or token not in room['players'] or room['players'][token]['bot']:
            raise ValueError('That chef session is no longer available. Create or join a kitchen again.')
        room['players'][token]['last'] = time.time()
        return {'room':code,'token':token}
    if path == '/api/demo':
        room = game.new_room(demo=True)
        name = 'Trainee'
    else:
        name = str(data.get('name','')).strip()
        if not name:
            raise ValueError('Enter your chef nickname.')
        if path == '/api/join':
            code = normalize_code(data.get('room',''))
            if code not in rooms:
                raise ValueError('Room not found. Check the code or ask the host.')
            token = game.join(rooms[code],name)
            return {'room':code,'token':token}
        count = data.get('bots',0)
        if type(count) is not int or not 0 <= count <= MAX_BOTS:
            raise ValueError('Choose zero to three bots; kitchens hold four chefs total.')
        room = game.new_room(data.get('difficulty','medium'))
    token = game.join(room,name)
    if room['demo']:
        game.start(room)
    else:
        configure(room,data.get('bots',0),game.join)
    code = generate_code(rooms)
    rooms[code] = room
    return {'room':code,'token':token}
