"""Small grid pathfinder for chefs; uses the same collision bounds as human movement."""
from collections import deque
import math
from physics import walkable, move_player


def approaches(room, station):
    result = []
    for dx,dy in [(0,1),(0,-1),(1,0),(-1,0),(1,1),(-1,1),(1,-1),(-1,-1)]:
        x,y = station['x']+dx,station['y']+dy
        if walkable(room,x,y) and min(room['stations'],key=lambda s:(s['x']-x)**2+(s['y']-y)**2) is station:
            result.append((x,y))
    return result


def route(room, player, station):
    goals = set(approaches(room,station))
    origin = (round(player['x']),round(player['y']))
    queue, previous = deque([origin]), {origin:None}
    while queue:
        node = queue.popleft()
        if node in goals:
            path = []
            while node is not None:
                path.append(node)
                node = previous[node]
            return list(reversed(path))
        for dx,dy in [(0,1),(1,0),(0,-1),(-1,0)]:
            point = (node[0]+dx,node[1]+dy)
            if point not in previous and walkable(room,*point):
                previous[point] = node
                queue.append(point)
    return None


def approach(room, player, station, elapsed):
    nearest = min(room['stations'],key=lambda s:(s['x']-player['x'])**2+(s['y']-player['y'])**2)
    if nearest is station and math.hypot(station['x']-player['x'],station['y']-player['y']) < 1.45:
        return True
    brain = player['brain']
    target = room['stations'].index(station)
    if brain.get('destination') != target or not brain.get('path'):
        path = route(room,player,station)
        if path is None:
            raise ValueError('No route to '+station['name'])
        brain.update(destination=target,path=path)
    while brain['path'] and math.dist((player['x'],player['y']),brain['path'][0]) < .06:
        brain['path'].pop(0)
    if brain['path']:
        x,y = brain['path'][0]
        dx,dy = x-player['x'],y-player['y']
        distance = math.hypot(dx,dy)
        move_player(room,player,dx/distance,dy/distance,min(elapsed,distance/4))
    return False
