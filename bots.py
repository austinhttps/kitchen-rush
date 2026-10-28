"""Cooperative recipe-driven chefs using the normal stations, timers, and inventory."""
from modes import notify
from navigation import approach, approaches
from config import MAX_CHEFS, MAX_BOTS

NAMES = ['Basil','Pepper','Sage','Miso','Olive','Ginger','Clove']


def host_token(room):
    return next((token for token,p in room['players'].items() if not p['bot']), None)


def configure(room, count, join):
    if type(count) is not int or not 0 <= count <= MAX_BOTS:
        raise ValueError('Choose between zero and three bot teammates.')
    if room['demo'] and count:
        raise ValueError('Guided demos are solo. Add bots in a real kitchen.')
    if room['started'] and not room['finished']:
        raise ValueError('Change bot teammates between rounds.')
    humans = [p for p in room['players'].values() if not p['bot']]
    if len(humans)+count > MAX_CHEFS:
        raise ValueError('The kitchen has four total chef slots. Reduce bots to invite more friends.')
    for token in [token for token,p in room['players'].items() if p['bot']]:
        del room['players'][token]
    for index in range(count):
        token = join(room,NAMES[index])
        room['players'][token].update(bot=True,brain={},bot_status='Ready to help')
    room['bot_count'] = count
    notify(room, f'{count} bot teammate'+('s' if count != 1 else '')+' ready.')


def release(room, player):
    brain = player['brain']
    if brain.get('has_plate'):
        counter = room['stations'][brain['counter']]
        if isinstance(counter['item'],list):
            room['dirty'] += 1
            counter['item'] = None
    if isinstance(player['held'],list):
        room['dirty'] += 1
    player['held'] = None
    player['brain'] = {}


def station(room, kind):
    return next(s for s in room['stations'] if s['kind']==kind)


def assign(room, player, recipes):
    others = [p['brain'] for p in room['players'].values() if p['bot'] and p is not player]
    reserved_orders = {b.get('order') for b in others}
    reserved_counters = {b.get('counter') for b in others}
    reserved_stoves = {b.get('stove') for b in others}
    for order in room['orders']:
        if order['id'] in reserved_orders:
            continue
        if order['recipe']=='Lemonade':
            player['brain'].update(order=order['id'],recipe='Lemonade',phase='drink')
            return True
        counter = next((i for i,s in enumerate(room['stations']) if s['kind']=='counter' and s['item'] is None
                        and i not in reserved_counters and approaches(room,s)),None)
        stove = next((i for i,s in enumerate(room['stations']) if s['kind']=='stove' and s['item'] is None
                      and i not in reserved_stoves),None)
        if counter is None or stove is None and any(i.startswith('cooked') for i in recipes[order['recipe']]):
            continue
        player['brain'].update(order=order['id'],recipe=order['recipe'],counter=counter,stove=stove,phase='plate',part=0)
        return True
    player['bot_status'] = 'Waiting for a free ticket / workstation'
    return False


def work(room, player, now, elapsed, interact, recipes):
    brain = player['brain']
    if brain.get('caught'):
        target = next((s for s in room['stations'] if s['kind']=='counter' and s['item'] is None and approaches(room,s)),None)
        player['bot_status'] = 'Putting caught food on a counter'
        if target and approach(room,player,target,elapsed):
            interact(room,player)
            brain.pop('caught')
        return
    if brain.get('order') and not any(o['id']==brain['order'] for o in room['orders']):
        claimed = {p['brain'].get('order') for p in room['players'].values() if p['bot'] and p is not player}
        replacement = next((o for o in room['orders'] if o['recipe']==brain['recipe'] and o['id'] not in claimed),None)
        if replacement:
            brain['order'] = replacement['id']
        else:
            release(room,player)
            brain = player['brain']
    if not brain.get('order'):
        fire = next((s for s in room['stations'] if s['item']=='fire'),None)
        if fire:
            player['bot_status']='Fire patrol'
            target = fire if player['held']=='extinguisher' else station(room,'extinguisher')
            if approach(room,player,target,elapsed):
                interact(room,player)
                if target is fire: player['held']=None
            return
        if player['held']=='extinguisher': player['held']=None
    if not brain.get('order') and not assign(room,player,recipes):
        if room['dirty'] and player['held'] is None:
            target = station(room,'sink')
            if approach(room,player,target,elapsed): interact(room,player)
        return
    if brain['recipe']=='Lemonade':
        target=station(room,'drinks' if player['held'] is None else 'serve')
        player['bot_status']='Mixing / serving lemonade'
        if approach(room,player,target,elapsed):
            interact(room,player)
            if target['kind']=='serve': release(room,player)
        return
    phase, parts = brain['phase'], recipes[brain['recipe']]
    counter = room['stations'][brain['counter']]
    wanted = parts[min(brain['part'],len(parts)-1)]

    def use(target):
        if approach(room,player,target,elapsed):
            interact(room,player)
            return True
        return False

    player['bot_status'] = brain['recipe']+' · '+phase
    if phase=='plate':
        if room['plates']:
            if use(station(room,'plates')): brain['phase']='put plate'
        elif room['dirty']:
            if use(station(room,'sink')): player['bot_status']='Washing dishes'
        else:
            player['bot_status']='Waiting for a clean plate'
    elif phase=='put plate':
        if counter['item'] is not None:
            release(room,player)
        elif use(counter): brain.update(phase='ingredient',has_plate=True)
    elif phase=='ingredient':
        raw = wanted.replace('chopped ','').replace('cooked ','')
        if use(station(room,raw)):
            brain['phase']='chop' if raw in ('tomato','lettuce','meat','fish') else 'cook' if raw=='rice' else 'assemble'
    elif phase=='chop':
        boards = [s for s in room['stations'] if s['kind']=='chop']
        target = min(boards,key=lambda s:(s['x']-player['x'])**2+(s['y']-player['y'])**2)
        if use(target): brain['phase']='cook' if wanted.startswith('cooked') else 'assemble'
    elif phase=='cook':
        stove = room['stations'][brain['stove']]
        if stove['item'] is None and use(stove): brain['phase']='wait'
    elif phase=='wait':
        stove = room['stations'][brain['stove']]
        if stove['item']=='fire': brain['phase']='fetch extinguisher'
        elif stove['item']==wanted:
            if use(stove): brain['phase']='assemble'
        elif stove['item'] is None:
            release(room,player)
    elif phase=='fetch extinguisher':
        if use(station(room,'extinguisher')): brain['phase']='extinguish'
    elif phase=='extinguish':
        stove = room['stations'][brain['stove']]
        if use(stove):
            player['held']=None
            brain['phase']='ingredient'
    elif phase=='assemble':
        if not isinstance(counter['item'],list):
            release(room,player)
        elif use(counter):
            brain['part'] += 1
            brain['phase']='collect plate' if brain['part']==len(parts) else 'ingredient'
    elif phase=='collect plate':
        if not isinstance(counter['item'],list) or sorted(counter['item'])!=sorted(parts):
            release(room,player)
        elif use(counter): brain['phase']='serve'
    elif phase=='serve':
        if use(station(room,'serve')): release(room,player)


def tick_bots(room, now, interact, recipes):
    if any(s['motion'] for s in room['stations']):
        return
    for player in list(room['players'].values()):
        if room['finished']: return
        if not player['bot'] or player['task'] or player['stunned_until'] > now:
            continue
        brain = player['brain']
        elapsed = min(.2,max(0,now-brain.get('last',now-.1)))
        if elapsed < .08:
            continue
        brain['last'] = now
        try:
            work(room,player,now,elapsed,interact,recipes)
        except ValueError as error:
            release(room,player)
            player['bot_status']='Replanning: '+str(error)
            player['brain']['last']=now+.4
