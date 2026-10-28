"""Exercise real request handlers in-process, without binding a local socket."""
import io
import json
import re
from pathlib import Path
import sys
from unittest.mock import patch
from urllib.parse import urlencode

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import server


class HandlerHarness(server.Handler):
    def __init__(self, path, data=None):
        payload = b'' if data is None else json.dumps(data).encode()
        self.path = path
        self.request_version = 'HTTP/1.1'
        self._headers_buffer = []
        self.headers = {'Content-Length': str(len(payload))}
        self.rfile = io.BytesIO(payload)
        self.wfile = io.BytesIO()
        self.status = None
        self.response_headers = {}

    def send_response(self, status, message=None, explain=None):
        self.status = status

    def send_header(self, key, value):
        self.response_headers[key] = value

    def log_request(self, *args, **kwargs):
        pass


def request(method, path, data=None):
    handler = HandlerHarness(path, data)
    getattr(handler, 'do_' + method)()
    raw = handler.wfile.getvalue()
    body = json.loads(raw) if raw else None
    return handler.status, body, handler.response_headers


def post(path, data, expected=200):
    status, body, _ = request('POST', '/api/' + path, data)
    assert status == expected, (path, status, body)
    return body


def state_of(session, expected=200):
    status, body, _ = request('GET', '/api/state?' + urlencode(session))
    assert status == expected, (status, body)
    return body


def run_smoke():
    server.ROOMS.clear()
    assert server.Handler.protocol_version == 'HTTP/1.1'
    soundtrack = (ROOT / 'public/audio.js').read_bytes()
    assert b'kitchen-music' in soundtrack
    header_probe = HandlerHarness('/api/state')
    server.Handler.end_headers(header_probe)
    assert header_probe.response_headers['Cache-Control'] == 'no-store'

    host = post('create', {'name': 'Smoke host'})
    assert re.fullmatch(r'[A-Z0-9]{3}-[A-Z0-9]{3}', host['room'])
    guest = post('join', {'name': 'Smoke guest', 'room': host['room'].replace('-', '').lower()})
    assert guest['room'] == host['room']
    post('action', {**host, 'action': 'start'})
    with patch.object(server.game, 'tick', side_effect=AssertionError('state reads must not run simulation')):
        countdown = state_of(host)
    assert countdown['launch_at'] > countdown['wall_now']
    assert round(countdown['end'] - countdown['now']) == 150
    assert countdown['orders'][2]['guest'] == 'VIP'
    assert countdown['orders'][2]['bonus'] == 150 and countdown['orders'][2]['penalty'] == 100
    assert countdown['score_floor'] == -200 and countdown['fire_limit'] == 20
    assert 'Lemonade' in countdown['recipes'] and any(s['kind'] == 'drinks' for s in countdown['stations'])
    clock[0] = countdown['launch_at']
    with patch.object(server.game, 'tick', side_effect=AssertionError('movement requests must not run simulation')):
        post('action', {**guest, 'action': 'move', 'dx': 1, 'dy': 0})
    state = state_of(guest)
    assert len(state['players']) == 2 and state['players'][state['you']]['x'] > 5.5

    assert state_of(host)['players'][state_of(host)['you']]['name'] == 'Chef Smoke host'
    assert post('rejoin', host) == host
    assert host['token'] not in json.dumps(state) and guest['token'] not in json.dumps(state)
    practice = post('demo', {})
    lesson = state_of(practice)
    assert lesson['lesson']['round'] == 1 and lesson['orders'][0]['recipe'] == 'Salad'
    assert all('guest' not in order for order in lesson['orders'])
    assert post('join', {'name': 'Intruder', 'room': practice['room']}, 400)

    hard = post('create', {'name': 'Challenge', 'difficulty': 'chef-de-cuisine'})
    post('action', {**hard, 'action': 'start'})
    assert state_of(hard)['target'] == 2800
    post('action', {**host, 'action': 'pause'})
    state_of(guest)
    post('action', {**guest, 'action': 'pause'}, 400)
    clock[0] += 2
    post('action', {**host, 'action': 'pause'})
    assert not state_of(guest)['paused']
    post('action', {**guest, 'action': 'end'}, 400)
    round_id = state_of(host)['round_id']
    post('action', {**host, 'action': 'restart'})
    assert state_of(guest)['round_id'] == round_id + 1
    post('action', {**host, 'action': 'end'})
    assert state_of(guest)['finished']
    assert state_of(guest)['results']['stats']['vip_missed'] == 1

    bots = post('create', {'name': 'Bot host', 'bots': 2, 'difficulty': 'easy'})
    assert sum(p['bot'] for p in state_of(bots)['players'].values()) == 2
    post('action', {**bots, 'action': 'bots', 'count': 1})
    post('action', {**bots, 'action': 'start'})
    clock[0] += 5
    assert state_of(bots)['bot_count'] == 1
    post('leave', bots)
    assert state_of(bots, 404)['error']

    full = post('create', {'name': 'Full host', 'bots': 3})
    post('join', {'name': 'Fifth chef', 'room': full['room']}, 400)
    assert len(state_of(full)['players']) == 4
    post('leave', full)

    setup = post('create', {'name': 'Setup host', 'difficulty': 'medium', 'bots': 1})
    removed = post('join', {'name': 'Remove me', 'room': setup['room']})
    post('action', {**setup, 'action': 'start'})
    before = state_of(setup)
    removed_ids = [key for key, player in before['players'].items() if player['bot'] or player['name'] == 'Chef Remove me']
    post('action', {**setup, 'action': 'restart', 'difficulty': 'easy', 'remove': removed_ids})
    after = state_of(setup)
    assert after['difficulty'] == 'easy' and after['bot_count'] == 0 and len(after['players']) == 1
    assert removed['token'] not in json.dumps(after)
    assert state_of(removed, 410)['error']
    for session in (host, guest, practice, hard, setup):
        post('leave', session)
    server.ROOMS.clear()
    print('PASS: request-handler smoke covers rooms, rounds, permissions, bots, demo, rejoin and removal.')


clock = [1000.0]
with patch('time.time', side_effect=lambda: clock[0]):
    run_smoke()
