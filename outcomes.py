"""One frozen result for natural endings and immediate kitchen failures."""
from modes import notify, settings

SCORE_FLOOR = -200
FIRE_LIMIT = 20


def finish(room, now, reason=None):
    if room['finished']:
        return
    from vip import close
    close(room)
    if not room['demo']:
        room['score'] = max(SCORE_FLOOR,room['score'])
        if room['score'] <= SCORE_FLOOR:
            reason = reason or 'Score reached −200. The kitchen lost its service license.'
    won = room.get('demo_served',False) if room['demo'] else not reason and room['score']>=room['target']
    room.update(finished=True,paused=False,paused_at=0,end=min(room['end'],now),failure_reason=reason,fire_deadline=0)
    room['results'] = {'round_id':room['round_id'],'demo':room['demo'],'won':bool(won),
        'winner':'Kitchen crew' if won else None,'score':room['score'],'target':room['target'],
        'difficulty':settings(room)['label'],'stats':dict(room['stats']),'reason':reason,
        'chefs':[{'name':p['name'],'served':p['served']} for p in room['players'].values()]}
    message = reason or (('Practice dish complete!' if won else 'Practice time is up. Retry or continue.') if room['demo'] else
                        ('Service complete — target reached!' if won else 'Service complete — target missed. Try again!'))
    notify(room,message,'success' if won else 'danger')


def check(room, now):
    if room['finished']:
        return False
    if room['demo']:
        return True
    if room['score'] <= SCORE_FLOOR:
        finish(room,now,'Score reached −200. The kitchen lost its service license.')
        return False
    fires = [s for s in room['stations'] if s['item']=='fire']
    room['fire_deadline'] = min((s['fire_since']+FIRE_LIMIT for s in fires),default=0)
    for stove in fires:
        remaining = stove['fire_since']+FIRE_LIMIT-now
        if remaining <= 0:
            finish(room,now,'Kitchen shutdown: a stove burned for 20 seconds.')
            return False
        for seconds in (10,5):
            if remaining<=seconds and seconds not in stove['fire_alerts']:
                stove['fire_alerts'].append(seconds)
                notify(room,f'Fire emergency! Extinguish the stove within {seconds}s or lose the round.','danger','fire')
    return True
