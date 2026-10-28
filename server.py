import json
import os
import threading
import time
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from pathlib import Path
import game
from bots import host_token
from rooms import enter
from public_state import snapshot
from presence import expire_disconnected

ROOMS = {}
LOCK = threading.Lock()
ROOT = Path(__file__).parent / 'public'


def simulate():
    while True:
        with LOCK:
            now=time.time()
            for code,room in list(ROOMS.items()):
                if not expire_disconnected(room,now):
                    del ROOMS[code]
                    continue
                game.tick(room)
        time.sleep(.05)


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT), **kwargs)

    def log_message(self, *args):
        pass

    def end_headers(self):
        # Local development must not mix a new server state with cached old clients.
        self.send_header('Cache-Control','no-store')
        super().end_headers()

    def reply(self, status, data):
        body = json.dumps(data).encode()
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        url = urlparse(self.path)
        if url.path == '/health':
            return self.reply(200, {'ok': True})
        if url.path != '/api/state':
            return super().do_GET()
        args = parse_qs(url.query)
        with LOCK:
            room = ROOMS.get(args.get('room', [''])[0])
            token = args.get('token', [''])[0]
            if room is not None and token in room['disconnected_tokens']:
                return self.reply(410,{'error':'Your connection was inactive for 15 seconds, so the chef slot was released. Ask the host for a new invite.'})
            if room is not None and token in room['removed_tokens']:
                return self.reply(410,{'error':'The host removed your chef from this kitchen. Ask for a new invite to join again.'})
            if room is None or token not in room['players']:
                return self.reply(404, {'error': 'Room/session not found. Create or join a kitchen.'})
            game.tick(room)
            room['players'][token]['last'] = time.time()
            self.reply(200,snapshot(room,token,game.RECIPES))

    def do_POST(self):
        try:
            size = int(self.headers.get('Content-Length', 0))
            if size > 4096:
                raise ValueError('Request too large.')
            data = json.loads(self.rfile.read(size))
            with LOCK:
                if self.path in ('/api/create','/api/join','/api/demo','/api/rejoin'):
                    return self.reply(200,enter(ROOMS,self.path,data))
                if self.path == '/api/leave':
                    code, token = data.get('room'), data.get('token')
                    room = ROOMS.get(code)
                    if room is None or token not in room['players']:
                        raise ValueError('Room/session not found.')
                    player = room['players'].pop(token)
                    if isinstance(player['held'], list):
                        room['dirty'] += 1
                    if player['task'] and player['task']['kind'] == 'wash':
                        room['dirty'] += 1
                    if host_token(room) is None:
                        del ROOMS[code]
                    return self.reply(200, {'ok': True})
                if self.path == '/api/action':
                    room = ROOMS.get(data.get('room'))
                    if room is None:
                        raise ValueError('Room not found.')
                    game.action(room, data.get('token'), data)
                    return self.reply(200, {'ok': True})
                self.reply(404, {'error': 'Unknown endpoint.'})
        except (ValueError, KeyError, TypeError) as exc:
            self.reply(400, {'error': str(exc)})


if __name__ == '__main__':
    threading.Thread(target=simulate,daemon=True,name='kitchen-simulation').start()
    port = int(os.environ.get('PORT', '8000'))
    print(f'Kitchen Rush running on port {port}', flush=True)
    ThreadingHTTPServer(('0.0.0.0', port), Handler).serve_forever()
