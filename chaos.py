"""Warned, difficulty-scaled visual surprises and station relocations."""
import random
from modes import notify

CHAOS = {
    'easy': {'first':45,'interval':55,'duration':4,'kinds':['confetti','shuffle_counters']},
    'medium': {'first':28,'interval':40,'duration':5,'kinds':['shuffle_ingredients','shuffle_counters','steam']},
    'hard': {'first':24,'interval':33,'duration':5,'kinds':['shuffle_stoves','shuffle_ingredients','shuffle_counters','steam']},
    'expert': {'first':20,'interval':27,'duration':6,'kinds':['shuffle_prep','shuffle_stoves','shuffle_ingredients','steam']},
    'chef': {'first':17,'interval':22,'duration':6,'kinds':['rush','carousel','shuffle_prep','steam']},
    'chef-de-cuisine': {'first':14,'interval':18,'duration':7,'kinds':['carousel','rush','shuffle_prep','steam']},
}
LABELS = {'confetti':'Receipt confetti!', 'steam':'Steam rush!', 'shuffle_ingredients':'Ingredient crates on the move!',
          'shuffle_prep':'Prep station shuffle!', 'carousel':'Kitchen carousel — hold onto your hats!',
          'shuffle_counters':'Counter shuffle!', 'shuffle_stoves':'Stoves on the move!', 'rush':'Dinner rush — stoves and ingredients move!'}
INGREDIENTS = ('tomato','lettuce','meat','fish','rice','bun')


def select_stations(room, kind):
    kinds = {'shuffle_counters':('counter',),'shuffle_stoves':('stove',),
             'shuffle_ingredients':INGREDIENTS,'shuffle_prep':('chop','plates','sink','extinguisher'),
             'rush':('stove',)+INGREDIENTS}
    if kind=='carousel':
        return [i for i,s in enumerate(room['stations']) if s['kind']!='serve']
    if kind not in kinds:
        return []
    options = [i for i,s in enumerate(room['stations']) if s['kind'] in kinds[kind]]
    return random.sample(options,len(options) if kind in ('rush','shuffle_ingredients') else 2)


def reset(room, now):
    room.update(chaos=None,chaos_count=0,next_chaos=0 if room['demo'] else now+CHAOS[room['difficulty']]['first'])


def begin_motion(room, event, now):
    stations = [room['stations'][i] for i in event['stations']]
    positions = [(s['x'],s['y']) for s in stations]
    for index,station in enumerate(stations):
        x,y = positions[(index+1)%len(stations)]
        station['motion']={'from_x':station['x'],'from_y':station['y'],'to_x':x,'to_y':y,'start':now,'end':now+1.4}


def tick(room, now):
    if room['demo']:
        return
    for station in room['stations']:
        motion = station['motion']
        if motion and now >= motion['end']:
            station.update(x=motion['to_x'],y=motion['to_y'],motion=None)
            for player in room['players'].values():
                if player['bot']:
                    player['brain'].pop('destination',None)
                    player['brain'].pop('path',None)
    event = room['chaos']
    config = CHAOS[room['difficulty']]
    if event:
        if event['phase']=='warning' and now >= event['start']:
            event.update(phase='active',start=now,end=now+config['duration'])
            if event['stations']:
                begin_motion(room,event,now)
            notify(room,event['label'],'warning','ready')
        elif event['phase']=='active' and now >= event['end']:
            room['chaos'] = None
            progress = max(0,min(1,1-(room['end']-now)/240))
            room['next_chaos'] = now+max(12,config['interval']*(1-.35*progress))
        return
    if now >= room['next_chaos']:
        kind = config['kinds'][0] if room['chaos_count']==0 else random.choice(config['kinds'])
        room['chaos_count'] += 1
        rank = list(CHAOS).index(room['difficulty'])
        room['chaos'] = {'id':room['chaos_count'],'kind':kind,'label':LABELS[kind], 'phase':'warning',
                         'start':now+3,'end':now+3+config['duration'],'intensity':rank+1+int((240-(room['end']-now))/90),
                         'stations':select_stations(room,kind)}
        notify(room,LABELS[kind]+' Get ready in 3 seconds.','warning')
