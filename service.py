"""Plate validation, normal scoring, and special guest outcomes."""
import time
from modes import notify, round_clock
import vip
import outcomes
import dining


def serve(room, player, recipes):
    held = player['held']
    drink = held=='lemonade'
    if not isinstance(held,list) and not drink:
        raise ValueError('Serve a plated meal or a finished drink.')
    ingredients = ['lemonade'] if drink else held
    index = next((i for i,o in enumerate(room['orders']) if sorted(recipes[o['recipe']])==sorted(ingredients)),None)
    if index is None:
        room['stats']['incorrect'] += 1
        special = room['orders'] and 'guest' in room['orders'][0]
        penalty = vip.failure(room,room['orders'].pop(0)) if special else 50
        room['score'] -= penalty
        room['combo'] = 1
        notify(room,f"Wrong dish! −{penalty} points."+(' Special guest left unhappy.' if special else ' Check the recipe.'),'danger','wrong')
    else:
        order = room['orders'].pop(index)
        if index != 0:
            room['combo'] = 1
        points = 100*room['combo']+round(30*max(0,order['expires']-time.time())/order['patience'])
        if 'guest' in order:
            points += order['bonus']
            room['stats']['vip_served'] += 1
        room['score'] += points
        room['stats']['served'] += 1
        if drink: room['stats']['drinks'] += 1
        dining.seat(room,order,time.time())
        player['served'] += 1
        prefix = order['guest']+' delighted! ' if 'guest' in order else ''
        notify(room,f"{prefix}{order['recipe']} served! +{points}",'success','serve')
        room['stats']['best_combo'] = max(room['stats']['best_combo'],room['combo'])
        if index == 0:
            room['combo'] = min(4,room['combo']+1)
        if room['demo']:
            room['demo_served'] = True
            room['end'] = time.time()
            round_clock(room,time.time())
    if not drink: room['dirty'] += 1
    player['held'] = None
    outcomes.check(room,time.time())
