"""Send stable public chef IDs, never another chef's authentication token."""
import time
from bots import host_token
from modes import DIFFICULTIES, demo_data
from kitchen_layout import menu
from outcomes import SCORE_FLOOR, FIRE_LIMIT


def snapshot(room, token, recipes):
    now=time.time()
    host=host_token(room)
    players={p['id']:{key:value for key,value in p.items() if key!='brain'} for p in room['players'].values()}
    projectiles=[{**shot,'owner':room['players'][shot['owner']]['id'] if shot['owner'] in room['players'] else None} for shot in room['projectiles']]
    return {**{key:value for key,value in room.items() if key not in ('removed_tokens','disconnected_tokens')},'players':players,'projectiles':projectiles,
            'host':room['players'][host]['id'] if host else None,'you':room['players'][token]['id'],
            'now':room['paused_at'] if room['paused'] else max(now,room['launch_at']),
            'wall_now':now,'recipes':menu(room),'difficulties':DIFFICULTIES,'lesson':demo_data(room),
            'score_floor':SCORE_FLOOR,'fire_limit':FIRE_LIMIT}
