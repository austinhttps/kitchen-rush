"""Pause/resume shifts every simulation deadline, preserving remaining time."""
import time
from modes import notify


def toggle_pause(room):
    if not room['started'] or room['finished']:
        raise ValueError('Start a round before pausing the kitchen.')
    now = time.time()
    if now < room['launch_at']:
        raise ValueError('Wait for the opening countdown to finish.')
    if not room['paused']:
        room.update(paused=True,paused_at=now)
        notify(room,'Kitchen paused. All chefs and timers are frozen.')
        return
    delta = now-room['paused_at']
    for key in ('end','next_order','next_chaos','next_vip'):
        if room[key]: room[key] += delta
    for order in room['orders']:
        order['expires'] += delta
    for station in room['stations']:
        if station['ready']: station['ready'] += delta
        if station['fire_since']: station['fire_since'] += delta
        if station['motion']:
            for key in ('start','end'): station['motion'][key] += delta
    for player in room['players'].values():
        if player['task']: player['task']['end'] += delta
        if player['stunned_until']: player['stunned_until'] += delta
        if player['bot'] and 'last' in player['brain']: player['brain']['last'] += delta
        player['move_at'] = now
    for shot in room['projectiles']:
        shot['updated'] += delta
    if room['fire_deadline']: room['fire_deadline'] += delta
    for diner in room['diners']:
        diner['sat_at'] += delta
        diner['leave_at'] += delta
    if room['chaos']:
        for key in ('start','end'): room['chaos'][key] += delta
    room.update(paused=False,paused_at=0)
    notify(room,'Back to work! Service resumed.','success')
