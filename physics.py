"""Authoritative movement, thrown ingredients, floor pickup, and chef stuns."""
import math
import secrets
import time
from modes import notify


def walkable(room, x, y):
    return .3 <= x <= 12.7 and .3 <= y <= 9.4 and all(
        (s['x']-x)**2+(s['y']-y)**2 > .5 for s in room['stations'])


def move_player(room, player, dx, dy, elapsed):
    if not math.isfinite(dx) or not math.isfinite(dy):
        raise ValueError('Movement direction must be finite.')
    length = max(1, math.hypot(dx, dy))
    if dx or dy:
        player['facing'] = [dx/length, dy/length]
    if player['stunned_until'] > time.time():
        return
    x = player['x']+dx/length*elapsed*4
    y = player['y']+dy/length*elapsed*4
    x, y = max(.3, min(12.7, x)), max(.3, min(9.4, y))
    if walkable(room, x, y):
        player.update(x=x, y=y)


def pickup_floor(room, player):
    if player['held'] is not None:
        return False
    nearby = [item for item in room['floor'] if math.hypot(item['x']-player['x'], item['y']-player['y']) < .85]
    if not nearby:
        return False
    item = min(nearby, key=lambda item: math.hypot(item['x']-player['x'], item['y']-player['y']))
    player['held'] = item['item']
    room['floor'].remove(item)
    return True


def throw_item(room, player, data):
    if not isinstance(player['held'], str) or player['held'] in ('extinguisher','lemonade','empty cup'):
        raise ValueError('Only ingredients can be thrown. Pick up food first.')
    if len(room['floor'])+len(room['projectiles']) >= 200:
        raise ValueError('The floor is full. Pick up some ingredients first.')
    dx, dy = data.get('dx', player['facing'][0]), data.get('dy', player['facing'][1])
    length = math.hypot(dx, dy)
    if not math.isfinite(length) or length < .01:
        raise ValueError('Aim away from your chef before throwing.')
    room['projectiles'].append({'id':secrets.token_hex(4), 'owner':next(k for k,v in room['players'].items() if v is player),
        'item':player['held'], 'x':player['x'], 'y':player['y'], 'dx':dx/length, 'dy':dy/length,
        'travelled':0, 'updated':time.time()})
    player['held'] = None
    notify(room, 'Ingredient away! Aim with the mouse or face your target.', sound='throw')


def land(room, shot):
    x, y = shot['x'], shot['y']
    if not walkable(room, x, y):
        candidates = [(x+dx*.8, y+dy*.8) for dx,dy in [(0,1),(0,-1),(1,0),(-1,0),(1,1),(-1,-1)]]
        candidates = [(a,b) for a,b in candidates if walkable(room,a,b)]
        if candidates:
            x,y = candidates[0]
    room['floor'].append({'id':shot['id'], 'x':x, 'y':y, 'item':shot['item']})


def catch_station(room, shot, now):
    for station in room['stations']:
        if station['item'] is not None or station['motion']:
            continue
        if abs(station['x']-shot['x']) > .2 or abs(station['y']-shot['y']) > .2:
            continue
        if station['kind']=='counter':
            station['item'] = shot['item']
            return True
        if station['kind']=='stove':
            if shot['item'] in ('chopped meat','chopped fish','rice'):
                station.update(item=shot['item'].replace('chopped ',''),ready=now+7)
                notify(room,'Perfect toss — cooking started!','success','ready')
            else:
                station.update(item=shot['item'],ready=0)
            return True
    return False


def tick_projectiles(room, now):
    for shot in list(room['projectiles']):
        distance = min(5-shot['travelled'], max(0, now-shot['updated'])*9)
        steps = max(1, math.ceil(distance/.15))
        done, caught = False, False
        for _ in range(steps):
            shot['x'] += shot['dx']*distance/steps
            shot['y'] += shot['dy']*distance/steps
            shot['travelled'] += distance/steps
            if catch_station(room,shot,now):
                caught = True
                break
            for token, player in room['players'].items():
                if token != shot['owner'] and math.hypot(player['x']-shot['x'],player['y']-shot['y']) < .5:
                    if player['held'] is None:
                        player['held'] = shot['item']
                        if player['bot']: player['brain']['caught'] = True
                        notify(room, player['name']+' caught the ingredient!', 'success', 'ready')
                        caught = True
                        break
                    player['stunned_until'] = now+1.25
                    notify(room, player['name']+' was bonked! Movement stunned for 1.25s.', 'warning', 'bonk')
                    done = True
                    break
            if caught:
                break
            if done or not (.3 <= shot['x'] <= 12.7 and .3 <= shot['y'] <= 9.4):
                shot['x'],shot['y'] = max(.3,min(12.7,shot['x'])),max(.3,min(9.4,shot['y']))
                done = True
                break
        shot['updated'] = now
        if caught or done or shot['travelled'] >= 4.999:
            if not caught: land(room, shot)
            room['projectiles'].remove(shot)
