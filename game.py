import random
import time
import secrets
from modes import LESSONS, chef_name, notify, round_clock, select_difficulty, settings
from physics import move_player, pickup_floor, throw_item, tick_projectiles
from bots import configure, host_token, tick_bots
from config import MAX_CHEFS
from round_control import toggle_pause
import chaos
import vip
from service import serve
from kitchen_layout import RECIPES, STATIONS, menu, stations
import outcomes
import dining
from host_controls import handle as host_control

def ticket(room):
    patience = 180 if room['demo'] else settings(room)['patience']
    recipe = LESSONS[room['demo_round']]['recipe'] if room['demo'] else random.choice(list(menu(room)))
    return {'id': secrets.token_hex(3), 'recipe': recipe, 'expires': time.time() + patience, 'patience': patience}


def new_room(difficulty='medium', demo=False):
    return {'players': {}, 'stations': stations(difficulty,demo),
            'orders': [], 'score': 0, 'combo': 1, 'plates': 4, 'dirty': 0, 'end': 0, 'started': False,
            'notice': 'Gather your crew, then start service.', 'next_order': 0,
            'difficulty': select_difficulty(difficulty), 'demo': demo, 'demo_round': 0,
            'event_id': 0, 'events': [], 'finished': False, 'clock_alerts': [], 'round_id': 0, 'results': None,
            'floor': [], 'projectiles': [], 'bot_count':0,'paused':False,'paused_at':0,'chaos':None,'next_chaos':0,'chaos_count':0,'launch_at':0,'vip_visits':0,'next_vip':0,
            'diners':[],'fire_deadline':0,'failure_reason':None,'removed_tokens':[],'disconnected_tokens':[]}


def join(room, name):
    if room['demo'] and room['players']:
        raise ValueError('Practice kitchens are solo. Create your own demo from the homepage.')
    if len(room['players']) >= MAX_CHEFS:
        raise ValueError('This kitchen already has four chefs. Ask the host to reduce bots or join another room.')
    token = secrets.token_hex(12)
    room['players'][token] = {'id':secrets.token_hex(6),'name': chef_name(name), 'x': 5.5, 'y': 6, 'held': None, 'task': None, 'served': 0,
                            'last': time.time(), 'move_at': time.time(), 'facing':[1,0], 'stunned_until':0, 'bot':False}
    return token


def start(room, countdown=False):
    if room['paused'] or room['started'] and room['end'] > time.time():
        raise ValueError('Service is already underway.')
    config = settings(room)
    delay = 4 if countdown and not room['demo'] else 0
    launch = time.time()+delay
    room.update(score=0, combo=1, plates=4, dirty=0, end=launch+150, started=True,
                orders=[ticket(room) for _ in range(1 if room['demo'] else min(3,config['max_customers']))], next_order=time.time()+config['interval'],
                target=100 if room['demo'] else config['target'] + max(0, len(room['players'])-2)*config['extra'],
                finished=False, clock_alerts=[], demo_served=False, results=None, round_id=room['round_id']+1,
                stats={'served': 0, 'incorrect': 0, 'expired': 0, 'burned': 0, 'best_combo': 1,'vip_served':0,'vip_missed':0,'drinks':0},floor=[],projectiles=[],paused=False,paused_at=0,launch_at=launch,ended_early=False,
                stations=stations(room['difficulty'],room['demo']),diners=[],fire_deadline=0,failure_reason=None)
    room['next_order'] += delay
    for order in room['orders']: order['expires'] += delay
    chaos.reset(room,launch)
    if room['demo'] and room['demo_round'] == 2:
        room.update(plates=0, dirty=2)
    notify(room, f"Practice {room['demo_round']+1}/3 — {LESSONS[room['demo_round']]['title']}" if room['demo'] else
           f"Service! {config['label']} difficulty. Follow the recipe cards.")
    vip.reset(room,launch)
    for s in room['stations']:
        s.update(item=None,ready=0,x=s['home_x'],y=s['home_y'],motion=None)
    for p in room['players'].values():
        p.update(held=None, task=None, x=5.5, y=6, served=0, stunned_until=0, brain={}, bot_status='Ready')


def tick(room):
    now = time.time()
    if not room['started'] or room['paused'] or now < room['launch_at'] or not round_clock(room, now):
        return
    if not outcomes.check(room,now): return
    dining.tick(room,now)
    chaos.tick(room,now)
    tick_projectiles(room, now)
    expired = [o for o in room['orders'] if o['expires'] <= now]
    if expired:
        room['stats']['expired'] += len(expired)
        penalty = sum(vip.failure(room,o) for o in expired)
        room['score'] -= penalty
        room['combo'] = 1
        room['orders'] = [o for o in room['orders'] if o['expires'] > now]
        notify(room, f'Orders expired! −{penalty} points.', 'warning')
        if not outcomes.check(room,now): return
    vip.tick(room,now,ticket)
    if room['demo'] and not room['orders']:
        room['orders'].append(ticket(room))
    elif not room['demo'] and now >= room['next_order'] and len(room['orders'])+len(room['diners']) < settings(room)['max_customers']:
        room['orders'].append(ticket(room))
        room['next_order'] = now + max(5, settings(room)['interval']-len(room['players']))
    for s in room['stations']:
        if s['kind'] == 'stove' and s['item'] and s['ready']:
            if now > s['ready'] + settings(room)['burn'] and s['item'] != 'fire':
                s['item'] = 'fire'
                s.update(fire_since=s['ready']+settings(room)['burn'],fire_alerts=[])
                room['stats']['burned'] += 1
                notify(room, 'Fire on the stove! Grab the extinguisher.', 'danger', 'fire')
            elif now >= s['ready'] and not s['item'].startswith('cooked'):
                if s['item'] != 'fire':
                    s['item'] = 'cooked '+s['item']
                    notify(room, f"{s['item'].capitalize()} is ready! Collect it before it burns.", 'success', 'ready')
    for p in room['players'].values():
        task = p['task']
        if task and now >= task['end']:
            if task['kind'] == 'chop':
                p['held'] = 'chopped '+p['held']
            elif task['kind']=='mix':
                p['held'] = 'lemonade'
                notify(room,'Lemonade ready! Carry the cup to Serve.','success','ready')
            else:
                room['plates'] += 1
                notify(room, 'Clean plate ready at Plates.', 'success', 'washed')
            p['task'] = None
    if not outcomes.check(room,now): return
    tick_bots(room,now,interact,menu(room))


def nearest(room, p):
    s = min(room['stations'], key=lambda s: (s['x']-p['x'])**2+(s['y']-p['y'])**2)
    if (s['x']-p['x'])**2+(s['y']-p['y'])**2 > 2.4:
        raise ValueError('Move closer to a station.')
    return s


def interact(room, p):
    s = nearest(room, p)
    if s['motion']:
        raise ValueError('That station is moving. Wait for it to settle.')
    k, held = s['kind'], p['held']
    if k in ('tomato', 'lettuce', 'meat', 'fish', 'rice', 'bun'):
        if held is None:
            p['held'] = k
        else:
            raise ValueError('Your hands are full. Use a counter or discard.')
    elif k == 'chop':
        if held not in ('tomato', 'lettuce', 'meat', 'fish'):
            raise ValueError('Hold a raw vegetable, meat, or fish to chop.')
        p['task'] = {'kind': 'chop', 'end': time.time()+3}
    elif k == 'stove':
        if held == 'extinguisher' and s['item'] == 'fire':
            s.update(item=None, ready=0,fire_since=0,fire_alerts=[])
            notify(room, 'Fire extinguished. Stove ready for cooking.', 'success', 'washed')
        elif held is None and s['item'] and s['item'].startswith('cooked'):
            p['held'], s['item'], s['ready'] = s['item'], None, 0
        elif held is None and s['item'] and not s['ready']:
            p['held'],s['item'] = s['item'],None
        elif held is None and s['item'] == 'fire':
            raise ValueError('Fetch the extinguisher!')
        elif s['item'] is None and held in ('chopped meat', 'chopped fish', 'rice'):
            s['item'] = held.replace('chopped ', '')
            s['ready'] = time.time()+7
            p['held'] = None
        else:
            raise ValueError('Chop meat/fish first. Rice cooks directly. Cooking takes 7 seconds.')
    elif k == 'plates':
        if held is None and room['plates'] > 0:
            p['held'] = []
            room['plates'] -= 1
        else:
            raise ValueError('Empty your hands or wash more plates.')
    elif k == 'counter':
        item = s['item']
        if isinstance(item, list) and isinstance(held, str) and held != 'extinguisher':
            item.append(held)
            p['held'] = None
        elif isinstance(held, list) and isinstance(item, str) and item != 'extinguisher':
            held.append(item)
            s['item'] = None
        elif held is None or item is None:
            p['held'], s['item'] = item, held
        else:
            raise ValueError('Counter occupied. Put a plate here to assemble ingredients.')
    elif k == 'sink':
        if held is None and room['dirty'] > 0:
            room['dirty'] -= 1
            p['task'] = {'kind': 'wash', 'end': time.time()+3}
        else:
            raise ValueError('Empty your hands; dirty plates return after service.')
    elif k == 'serve':
        serve(room,p,menu(room))
    elif k == 'drinks':
        if held is not None: raise ValueError('Empty your hands before mixing a drink.')
        p.update(held='empty cup',task={'kind':'mix','end':time.time()+3})
    elif k == 'extinguisher':
        if held is None:
            p['held'] = 'extinguisher'


def action(room, token, data):
    if data.get('action') != 'move':
        tick(room)
    p = room['players'].get(token)
    if p is None:
        raise ValueError('Chef session not found. Rejoin the room.')
    p['last'] = time.time()
    kind = data['action']
    if host_control(room,token,kind,start,data):
        return
    if kind=='pause':
        if token != host_token(room):
            raise ValueError('Only the host can pause or resume the kitchen.')
        if 'paused' in data:
            if type(data['paused']) is not bool: raise ValueError('Pause state must be true or false.')
            if data['paused']==room['paused']: return
        toggle_pause(room)
        return
    if kind in ('start', 'difficulty', 'next_demo', 'bots'):
        if token != host_token(room):
            raise ValueError('Only the room host can change service settings.')
        if kind == 'bots':
            configure(room,data.get('count'),join)
            return
        if kind == 'difficulty':
            if room['demo'] or room['started'] and room['end'] > time.time():
                raise ValueError('Difficulty can only change between real rounds.')
            room['difficulty'] = select_difficulty(data.get('difficulty'))
            room['stations'] = stations(room['difficulty'],room['demo'])
            notify(room, f"Difficulty set to {settings(room)['label']}.")
            return
        if kind == 'next_demo':
            if not room['demo'] or not room['finished'] or room['demo_round'] >= len(LESSONS)-1:
                raise ValueError('Complete the current practice round first.')
            room['demo_round'] += 1
        start(room,countdown=not room['demo'])
        return
    if not room['started'] or time.time() >= room['end']:
        return
    if time.time() < room['launch_at']:
        return
    if room['paused']:
        raise ValueError('Kitchen paused. The host can resume service.')
    if p['task']:
        return
    if kind == 'move':
        elapsed = min(.2, time.time()-p['move_at'])
        p['move_at'] = time.time()
        dx, dy = float(data.get('dx', 0)), float(data.get('dy', 0))
        move_player(room,p,dx,dy,elapsed)
    elif kind == 'interact':
        if not pickup_floor(room,p):
            interact(room, p)
    elif kind == 'discard':
        if isinstance(p['held'], list):
            room['dirty'] += 1
        p['held'] = None
    elif kind == 'throw':
        throw_item(room,p,data)
    outcomes.check(room,time.time())
