import random, copy

from flask.cli import F

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
    
    def __repr__(self):
        return "\n  " + self.name

class Quest:
    def __init__(self, size, fails_to_fail):
        self.size = size
        self.fails_to_fail = fails_to_fail

    def evaluate(self, votes):
        fail = len([v for v in votes if v == 'FAIL'])
        magic = len([v for v in votes if v == 'MAGIC'])
        return (fail < self.fails_to_fail) != (magic % 2 == 1)

class Game:
    counts = {
        3: (2, 1, [1,2,2,2,2]),
        4: (2, 2, [2,2,2,3,2]),
        5: (3, 2, [2,3,2,3,3]),
        6: (4, 2, [2,3,4,3,4]),
        7: (4, 3, [2,3,3,4,4]),
        8: (5, 3, [3,4,4,5,5]),
        9: (6, 3, [3,4,4,5,5]),
        10: (6, 4, [3,4,4,5,5]),
        11: (7, 4, [3,4,5,6,6]),
        12: (8, 4, [3,4,5,6,6]),
        13: (8, 5, [4,5,5,7,6])
    }
    def __init__(self, good, evil=None, quest_sizes=None):
        if evil is None:
            good, evil, quest_sizes = Game.counts[good]
            quest_sizes = copy.deepcopy(quest_sizes)
        self.good = good
        self.evil = evil
        self.quest_sizes = quest_sizes
        self.leader_index = random.randint(0,good+evil-1)
        self.passes = 0
        self.fails = 0

    def get_quest(self, index=None) -> Quest:
        if(index == None):
            index = (self.good+self.evil)
        return Quest(self.quest_sizes[index], 2 if (index == 3 and self.good + self.evil >= 7) else 1)
    
    def get_round(self):
        return self.passes + self.fails + 1

    def __repr__(self) -> str:
        return f"(\n  Good: {self.good}, Evil: {self.evil}, Round: {self.get_round()},\n  Quest Sizes: {self.quest_sizes}\n)"




class Player:
    def __init__(self, name, sid):
        self.name = name
        self.card = None
        self.sid = sid

    def set_card(self, card:Card):
        self.card = card

    def __repr__(self) -> str:
        return f"\n  [Name: {self.name}, Card: {self.card}]"

class Room:
    def __init__(self, cards:list[str]):
        self.cards:list[Card] = [copy.deepcopy(cards_prototypes[name]) for name in cards]
        self.players:dict[Player] = {}
        self.game = Game(len(cards))

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
        for i, player in enumerate(self.players.values()):
            player.set_card(cards[i])

    def get_known_to_evil(self) -> list[str]:
        return [p.name for p in self.players.values() if p.card.known_to_evil]
    
    def get_appears_evil(self) -> list[str]:
        return [p.name for p in self.players.values() if p.card.appears_evil]
    
    def get_percival_sees(self):
        pair = [p.name for p in self.players.values() if p.card.name in ['Merlin', 'Morgana']]
        random.shuffle(pair)
        return f"<b>{pair[0]}</b> and <b>{pair[1]}</b>"
    
    def __repr__(self):
        return f"[\nPlayers: {self.players},\nCards: {self.cards},\nGame: {self.game}\n]"


cards_prototypes = {
    'Merlin' : Card('Merlin', True, lambda room: (f"You are Merlin - You are GOOD\nYou can only put a <b>SUCCESS</b> when placed on a quest. You see these players as evil: {', '.join(room.get_appears_evil())}")),
    'Loyal Servant of Arthur' : Card('Loyal Servant of Arthur', True, 'You can only put in <b>SUCCESS</b> when placed on a quest.'),
    'Assasin' : Card('Assasin', False, 'You can put a <b>SUCCESS</b> or <b>FAILURE</b> when placed on a quest and get final say on who you beleive to be Merlin.'),
    'Minion of Mordred' : Card('Minion of Mordred', False, 'You can put a <b>SUCCESS</b> or <b>FAILURE</b> when placed on a quest.'),
    'Oberon' : Card('Oberon', False, 'You can put a <b>SUCCESS</b> or <b>FAILURE</b> when placed on a quest but you do not know anything else.', False, True, False),
    'Morgana' : Card('Morgana', False, 'You can put a <b>SUCCESS</b> or <b>FAILURE</b> when placed on a quest. Percival sees you and Merlin, but does not know who is whom.'),
    'Mordred' : Card('Mordred', False, 'You can put a <b>SUCCESS</b> or <b>FAILURE</b> when placed on a quest. You are not known to Merlin. If there is no assasin, you get final say on who you believe to be Merlin.', appears_evil=False),
    'Percival' : Card('Percival', True, lambda room: (f"You are Percival - You are GOOD\nYou can only put a <b>SUCCESS</b> when placed on a quest. You know that between {room.get_percival_sees()} one is Merlin and one is Morgana, but not which")),
    'Lunatic' : Card('Lunatic', False, 'You must put a <b>FAILURE</b> when placed on a quest.', options=['FAIL']), 
    'Good Sorcerer' : Card('Good Sorcerer', True, 'You can put a <b>SUCCESS</b> or a <b>MAGIC</b> when placed on a quest. Each MAGIC will invert the result of the quest.', options=['SUCCESS', 'MAGIC']),
    'Evil Sorcerer' : Card('Evil Sorcerer', False, 'You can put a <b>SUCCESS</b> or a <b>MAGIC</b> when placed on a quest. Each MAGIC will invert the result of the quest.', options=['SUCCESS', 'MAGIC']),
    'Good Lancelot' : Card('Good Lancelot', True, lambda room: (f"You are GOOD Lancelot\nYou can only put a <b>SUCCESS</b> when placed on a quest. You know that {[p.name for p in room.players if p.card.name == 'Evil Lancelot'][0]} is EVIL Lancelot")), 
    'Evil Lancelot' : Card('Evil Lancelot', True, lambda room: (f"You are EVIL Lancelot\nYou can put a <b>SUCCESS</b> or <b>FAILURE</b> when placed on a quest. You know that {[p.name for p in room.players if p.card.name == 'Good Lancelot'][0]} is GOOD Lancelot")), 
}