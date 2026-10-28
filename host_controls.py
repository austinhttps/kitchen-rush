"""Host-only lifecycle actions; round controls do not trust client visibility."""
import time
from bots import host_token, release as release_bot
from modes import notify, round_clock, select_difficulty


def handle(room, token, kind, start, data):
    if kind == 'kick':
        if token != host_token(room):
            raise ValueError('Only the host can remove a chef from this kitchen.')
        target = data.get('player')
        by_id = {player['id']:key for key,player in room['players'].items()}
        if not isinstance(target,str) or target not in by_id or by_id[target] == token:
            raise ValueError('Choose another chef who is currently in this kitchen.')
        key = by_id[target]
        player = room['players'][key]
        if player['task'] and player['task']['kind']=='wash': room['dirty'] += 1
        if player['bot']:
            release_bot(room,player)
        elif isinstance(player['held'],list):
            room['dirty'] += 1
            player['held']=None
        del room['players'][key]
        if not player['bot']:
            room['removed_tokens'].append(key)
            room['removed_tokens'] = room['removed_tokens'][-32:]
        room['bot_count'] = sum(chef['bot'] for chef in room['players'].values())
        notify(room, f"{player['name']} removed from the kitchen.")
        return True
    if kind not in ('restart','end'):
        return False
    if token != host_token(room):
        raise ValueError('Only the host can restart or end service.')
    if not room['started'] or room['finished'] and kind=='end':
        raise ValueError('There is no live round to '+kind+'.')
    if kind == 'restart':
        difficulty = select_difficulty(data.get('difficulty',room['difficulty']))
        remove = data.get('remove',[])
        if not isinstance(remove,list) or any(not isinstance(value,str) for value in remove) or len(remove)!=len(set(remove)):
            raise ValueError('Choose a valid list of chefs to remove.')
        by_id = {p['id']:key for key,p in room['players'].items()}
        if any(value not in by_id or by_id[value]==token for value in remove):
            raise ValueError('The host must stay; choose chefs currently in this kitchen.')
        if room['demo'] and (remove or difficulty!=room['difficulty']):
            raise ValueError('Guided practice keeps its original setup.')
        for value in remove:
            key = by_id[value]
            if not room['players'][key]['bot']: room['removed_tokens'].append(key)
            del room['players'][key]
        room['removed_tokens'] = room['removed_tokens'][-32:]
        room['bot_count'] = sum(p['bot'] for p in room['players'].values())
        room['difficulty'] = difficulty
        room.update(started=False,paused=False)
        start(room,countdown=True)
    else:
        room.update(paused=False,paused_at=0,launch_at=0,end=time.time(),ended_early=True)
        round_clock(room,time.time())
    return True
