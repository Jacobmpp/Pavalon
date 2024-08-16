import random, copy

class Card:
    def __init__(self, name, good, start, knows_evil=None, appears_evil=None, known_to_evil=None, options=None):
        self.name = name
        self.good = good
        self.knows_evil = knows_evil if knows_evil != None else not good
        self.appears_evil = appears_evil if appears_evil != None else not good
        self.known_to_evil = known_to_evil if known_to_evil != None else not good
        self.start = start
        self.options = options if options != None else ['SUCCESS'] if good else ['SUCCESS', 'FAIL']

    
    def game_start(self, room) -> str: # return a response to be given to the player based on their role and the room state
        if isinstance(self.start, str):
            alignment = 'GOOD' if self.good else 'EVIL'
            return f'{self.name} - You are {alignment}\n{self.start}'
        return self.start(room)

class Merlin:
    pass

class Quest:
    def __init__(self, size, fails_to_fail):
        self.size = size
        self.fails_to_fail = fails_to_fail

    def evaluate(self, votes):
        fail = len([v for v in votes if v == 'FAIL'])
        magic = len([v for v in votes if v == 'MAGIC'])
        return (fail < self.fails_to_fail) != (magic % 2 == 1)

class Game:
    def __init__(self, good, evil, quest_sizes):
        self.good = good
        self.evil = evil
        self.quest_sizes = quest_sizes

    def get_quest(self, index) -> Quest:
        return Quest(self.quest_sizes[index], 2 if (index == 3 and self.good + self.evil >= 7) else 1)

counts = {
    5: Game(3, 2, [2,3,2,3,3]),
    6: Game(4, 2, [2,3,4,3,4]),
    7: Game(4, 3, [2,3,3,4,4]),
    8: Game(5, 3, [3,4,4,5,5]),
    9: Game(6, 3, [3,4,4,5,5]),
   10: Game(6, 4, [3,4,4,5,5])
}

class Player:
    def __init__(self, name):
        self.name = name

    def set_card(self, card:Card):
        self.card = card

class Room:
    def __init__(self, cards:list[Card]):
        self.cards:list[Card] = cards
        self.players:dict[Player] = {}

    def add_player(self, player:Player) -> bool:
        if len(self.players) < len(self.cards) and player.name not in self.players:
            self.players[player.name] = player
            return True
        return False

    def remove_player(self, name) -> bool:
        if(name in self.players):
            del self.players[name]
            return True
        return False

    def add_card(self, card:Card):
        self.cards.append(card)

    def remove_card(self, name) -> bool:
        matches = [i for i, c in enumerate(self.cards) if c.name == name]
        if(len(matches)>0):
            self.cards.pop(matches[0])
            return True
        return False
    
    def dist_cards(self):
        cards = copy.deepcopy(self.cards)
        random.shuffle(cards)
        for i, player in enumerate(self.players.values):
            player.set_card(cards[i])

    def get_known_to_evil(self) -> list[str]:
        return [p.name for p in self.players if p.card.known_to_evil]
    
    def get_appears_evil(self) -> list[str]:
        return [p.name for p in self.players if p.card.appears_evil]
    
    def get_percival_sees(self):
        pair = [p.name for p in self.players if p.card.name in ['Merlin', 'Morgana']]
        random.shuffle(pair)
        return "<b>{pair[0]}</b> and <b>{pair[1]}</b>"


cards = {
    'Merlin' : Card('Merlin', True, lambda room: (f"You are Merlin - You are GOOD\nYou can only put a <b>SUCCESS</b> when placed on a quest. You see these players as evil: {str(room.get_appears_evil())}")),
    'Loyal Servant of Arthur' : Card('Loyal Servant of Arthur', True, 'You can only put in <b>SUCCESS</b> when placed on a quest.'),
    'Assasin' : Card('Assasin', False, 'You can put a <b>SUCCESS</b> or <b>FAILURE</b> when placed on a quest and get final say on who you beleive to be Merlin.'),
    'Oberon' : Card('Oberon', False, 'You can put a <b>SUCCESS</b> or <b>FAILURE</b> when placed on a quest but you do not know anything else.', False, True, False),
    'Morgana' : Card('Morgana', False, 'You can put a <b>SUCCESS</b> or <b>FAILURE</b> when placed on a quest. Percival sees you and Merlin, but does not know who is whom.'),
    'Mordred' : Card('Mordred', False, 'You can put a <b>SUCCESS</b> or <b>FAILURE</b> when placed on a quest. You are not known to Merlin. If there is no assasin, you get final say on who you believe to be Merlin.', appears_evil=False),
    'Percival' : Card('Percival', True, lambda room: (f"You are Percival - You are GOOD\nYou can only put a <b>SUCCESS</b> when placed on a quest. You know that between {room.get_percival_sees()} one is Merlin and one is Morgana, but not which")),
    'Lunatic' : Card('Lunatic', False, 'You can only put a <b>FAILURE</b> when placed on a quest.', options=['FAIL']), 
    'Good Sorcerer' : Card('Good Sorcerer', True, 'You can put a <b>SUCCESS</b> or a <b>MAGIC</b> when placed on a quest. Each MAGIC will invert the result of the quest.', options=['SUCCESS', 'MAGIC']),
    'Evil Sorcerer' : Card('Evil Sorcerer', False, 'You can put a <b>SUCCESS</b> or a <b>MAGIC</b> when placed on a quest. Each MAGIC will invert the result of the quest.', options=['SUCCESS', 'MAGIC']),
    'Good Lancelot' : Card('Good Lancelot', True, lambda room: (f"You are GOOD Lancelot\nYou can only put a <b>SUCCESS</b> when placed on a quest. You know that {[p.name for p in room.players if p.card.name == 'Evil Lancelot'][0]} is EVIL Lancelot")), 
    'Evil Lancelot' : Card('Evil Lancelot', True, lambda room: (f"You are EVIL Lancelot\nYou can put a <b>SUCCESS</b> or <b>FAILURE</b> when placed on a quest. You know that {[p.name for p in room.players if p.card.name == 'Good Lancelot'][0]} is GOOD Lancelot")), 
}
