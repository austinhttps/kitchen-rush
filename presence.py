"""Expire human chefs whose HTTP heartbeat has stopped."""
from bots import host_token
from modes import notify

DISCONNECT_AFTER_SECONDS = 15


def expire_disconnected(room, now):
    expired=[]
    for token,player in list(room['players'].items()):
        if player['bot'] or now-player['last'] <= DISCONNECT_AFTER_SECONDS:
            continue
        if player['task'] and player['task']['kind']=='wash':
            room['dirty'] += 1
        if isinstance(player['held'],list):
            room['dirty'] += 1
        del room['players'][token]
        room['disconnected_tokens'].append(token)
        expired.append(player['name'])
    room['disconnected_tokens']=room['disconnected_tokens'][-32:]
    if expired:
        names=', '.join(expired)
        notify(room,f'{names} disconnected; chef slot released.','warning')
    return host_token(room) is not None
