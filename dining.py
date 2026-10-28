"""Successful orders seat customers in four shared dining-room chairs."""
SEATS = 4
EATING_SECONDS = 12


def seat(room, order, now):
    tick(room,now)
    occupied = {d['seat'] for d in room['diners']}
    available = next((i for i in range(SEATS) if i not in occupied),None)
    if available is not None:
        room['diners'].append({'id':order['id'],'recipe':order['recipe'],'guest':order.get('guest'),
                               'seat':available,'sat_at':now,'leave_at':now+EATING_SECONDS})


def tick(room, now):
    room['diners'] = [d for d in room['diners'] if d['leave_at']>now]
