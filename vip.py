"""Difficulty-scaled guest visits with explicit ticket rewards and consequences."""
from modes import notify, settings

VISITS = {
    'easy': (1,100,75), 'medium': (2,150,100), 'hard': (3,200,125),
    'expert': (4,250,150), 'chef': (5,300,200), 'chef-de-cuisine': (6,400,250),
}


def reset(room, launch):
    room.update(vip_visits=0,next_vip=0)
    if not room['demo']:
        decorate(room,room['orders'][-1],launch)


def decorate(room, order, now):
    count,bonus,penalty = VISITS[room['difficulty']]
    critic = room['vip_visits'] % 2 == 1
    room['vip_visits'] += 1
    order.update(guest='Critic' if critic else 'VIP',bonus=bonus*3//2 if critic else bonus,
                 penalty=penalty*2 if critic else penalty)
    if critic:
        order['patience'] *= .85
        order['expires'] = now+order['patience']
    room['next_vip'] = now+240/(count+1)
    notify(room,f"{order['guest']} arrived: {order['recipe']}! Bonus +{order['bonus']}; failure −{order['penalty']}.",'warning','ready')


def tick(room, now, make_ticket):
    if room['demo']:
        return
    count = VISITS[room['difficulty']][0]
    if room['vip_visits'] < count and now >= room['next_vip'] and len(room['orders'])+len(room['diners']) < settings(room)['max_customers']:
        order = make_ticket(room)
        decorate(room,order,now)
        room['orders'].append(order)


def failure(room, order):
    if 'guest' in order:
        room['stats']['vip_missed'] += 1
        return order['penalty']
    return 25


def close(room):
    """Outstanding special guests count as missed visits at the service buzzer."""
    special = [o for o in room['orders'] if 'guest' in o]
    if special:
        penalty = sum(failure(room,o) for o in special)
        room['score'] -= penalty
        room['combo'] = 1
        room['orders'] = [o for o in room['orders'] if 'guest' not in o]
        notify(room,f'Unserved VIP/critic guests: −{penalty} points.','warning')
