"""Stable station identities and difficulty-specific recipe/layout selection."""
RECIPES = {'Salad':['chopped tomato','chopped lettuce'], 'Burger':['cooked meat','bun'],
           'Fish & rice':['cooked fish','cooked rice'], 'Lemonade':['lemonade']}
STATIONS = [
    ('Tomatoes',1,1,'tomato'),('Lettuce',3,1,'lettuce'),('Meat',5,1,'meat'),
    ('Fish',7,1,'fish'),('Rice',9,1,'rice'),('Buns',11,1,'bun'),
    ('Chop',1,4,'chop'),('Chop',1,6,'chop'),('Stove',5,4,'stove'),
    ('Stove',7,4,'stove'),('Stove',9,4,'stove'),('Plates',3,8,'plates'),
    ('Sink',5,8,'sink'),('Serve',13,4,'serve'),('Counter',7,8,'counter'),
    ('Counter',9,8,'counter'),('Extinguisher',11,8,'extinguisher'),
    ('Counter',0,3,'counter'),('Counter',0,5,'counter'),('Counter',0,7,'counter'),
    ('Counter',12,2,'counter'),('Counter',12,8,'counter')]


def menu(room):
    return {name:parts for name,parts in RECIPES.items()
            if name!='Lemonade' or not room['demo'] and room['difficulty']!='easy'}


def stations(difficulty, demo):
    layout = STATIONS+([('Drinks',11,6,'drinks')] if not demo and difficulty!='easy' else [])
    return [dict(name=n,x=x,y=y,home_x=x,home_y=y,kind=k,item=None,ready=0,motion=None,
                 fire_since=0,fire_alerts=[]) for n,x,y,k in layout]
