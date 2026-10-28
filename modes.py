"""Difficulty settings, practice lessons, and shared kitchen notifications."""
DIFFICULTIES = {
    'easy': {'label': 'Easy', 'patience': 100, 'interval': 30, 'burn': 15, 'target': 600, 'extra': 200, 'max_customers': 3},
    'medium': {'label': 'Medium', 'patience': 60, 'interval': 22, 'burn': 10, 'target': 1200, 'extra': 400, 'max_customers': 4},
    'hard': {'label': 'Hard', 'patience': 50, 'interval': 19, 'burn': 8, 'target': 1600, 'extra': 500, 'max_customers': 5},
    'expert': {'label': 'Expert', 'patience': 45, 'interval': 16, 'burn': 6, 'target': 2000, 'extra': 600, 'max_customers': 6},
    'chef': {'label': 'Chef', 'patience': 40, 'interval': 14, 'burn': 5, 'target': 2400, 'extra': 700, 'max_customers': 7},
    'chef-de-cuisine': {'label': 'Chef de Cuisine', 'patience': 35, 'interval': 12, 'burn': 4, 'target': 2800, 'extra': 800, 'max_customers': 8},
}
LESSONS = [
    {'title': 'Prep school', 'recipe': 'Salad', 'steps': [
        'Move with WASD / arrows or the touch arrows. Approach Tomatoes and interact (E).',
        'Take the tomato to Chop and interact. Wait 3 seconds. Leave it on a counter.',
        'Collect lettuce, chop it, and leave it on the other counter.',
        'Collect a clean plate. Interact at each ingredient counter to add both vegetables.',
        'Carry your salad to Serve and interact. One correct dish completes this round.']},
    {'title': 'Feel the heat', 'recipe': 'Burger', 'steps': [
        'Collect meat from the top row, then chop it at a cutting board.',
        'Put chopped meat on an empty Stove. Cooking takes 7 seconds.',
        'While it cooks, place a clean plate on a counter. Add a bun to that plate.',
        'With empty hands, retrieve the cooked meat before it burns. Add it to the plate.',
        'Pick up the burger plate and serve. If food burns, use the extinguisher.']},
    {'title': 'Full service', 'recipe': 'Fish & rice', 'steps': [
        'No clean plates this time! With empty hands, wash a dirty plate at Sink (3 seconds).',
        'Chop fish, then cook it on a Stove. Raw rice can go straight on another Stove.',
        'Fetch your washed plate from Plates and leave it on a counter.',
        'Retrieve the cooked fish and rice separately. Add each to the counter plate.',
        'Pick up the finished plate and serve. Then head back to join a real kitchen.']},
]


def settings(room):
    return DIFFICULTIES['easy' if room['demo'] else room['difficulty']]


def select_difficulty(value):
    if value not in DIFFICULTIES:
        raise ValueError('Choose a listed difficulty.')
    return value


def chef_name(name):
    nickname = name.strip()
    while nickname.lower() == 'chef' or nickname.lower().startswith('chef '):
        nickname = nickname[4:].strip()
    return 'Chef ' + (nickname[:16] or 'Rookie')


def notify(room, message, tone='info', sound=None):
    room['notice'] = message
    room['event_id'] += 1
    room['events'].append({'id': room['event_id'], 'message': message, 'tone': tone, 'sound':sound})
    room['events'] = room['events'][-20:]


def round_clock(room, now):
    if now >= room['end']:
        from outcomes import finish
        finish(room,now)
        return False
    for seconds in (60, 30, 10):
        if room['end']-now <= seconds and seconds not in room['clock_alerts']:
            room['clock_alerts'].append(seconds)
            notify(room, f'{seconds} seconds left!', 'warning')
    return True


def demo_data(room):
    if not room['demo']:
        return None
    return {**LESSONS[room['demo_round']], 'round': room['demo_round']+1, 'total': len(LESSONS)}
