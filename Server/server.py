from flask import Flask, render_template, request, redirect, url_for
from flask_socketio import SocketIO, join_room, leave_room, emit
from utils import *


app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'
socketio = SocketIO(app)

# Room management
rooms: dict[str:Room] = {}


@app.route('/')
def index():
    return render_template('index.html')

@app.route('/create_room', methods=['POST'])
def create_room():
    global rooms
    room_id = request.form['new_room_id']
    if 'roles' in request.form:
        roles = []
        name = request.form['name']
        for role in cards_prototypes:
            if(role in request.form and int(request.form[role]) > 0):
                roles += [role for a in range(int(request.form[role]))]
        rooms[room_id] = Room(cards=roles)
        return redirect(url_for('room', room_id=room_id, name=name))

    if room_id not in rooms:
        return render_template('select_roles.html', room_id=room_id, roles=list(cards_prototypes))
    return redirect(url_for('room', room_id=room_id, name=name))

@app.route('/get_rooms', methods=['GET'])
def get_rooms():
    global rooms
    return list(rooms), 200

@app.route('/room', methods=['GET', 'POST'])
def room(room_id=None, name=None):
    global rooms
    if room_id == None:
        room_id = request.values['room_id']
    if name == None:
        name = request.values['name']

    if room_id not in rooms:
        return render_template('select_roles.html', room_id=room_id, name=name, roles=list(cards_prototypes))
    
    current_room:Room = rooms[room_id]
    return render_template('room.html', room_id=room_id, name=name, roles=[r.name for r in current_room.cards], players=list(current_room.players))

@socketio.on('join')
def on_join(data):
    global rooms
    name = data['name']
    room_id = data['room_id']
    if(name == 'kill'):
        del rooms[room_id]


    join_room(room_id)
    room:Room = rooms[room_id]

    match room.add_player(Player(name, request.sid)):
        case True:
            emit('players', list(room.players), room=room_id)

            if len(room.players) == len(room.cards):
                emit('ready', 'The game is starting!', room=room_id)
                room.dist_cards()
                for player in room.players.values():
                    emit('role', player.card.game_start(room), room=player.sid)
                activate_leader(room_id)
        case error:
            emit('error', error)

@socketio.on('leave')
def on_leave(data):
    global rooms
    name = data['name']
    room_id = data['room_id']
    leave_room(room_id)

    if room_id in rooms and rooms[room_id].remove_player(name):
        emit('update', f'{name} has left the room.', room=room_id)

    if len(rooms[room_id].players) == 0:
        del rooms[room_id]

@socketio.on('get_role')
def on_get_role(data):
    global rooms
    name = data['name']
    room_id = data['room_id']
    room:Room = rooms[room_id]
    player:Player = room.players[name]
    emit('role', player.card.game_start(room), room=player.sid)

@socketio.on('leaders_quest')
def on_leaders_quest(data):
    global rooms
    name = data['name']
    room_id = data['room_id']
    room:Room = rooms[room_id]
    player:Player = room.players[name]
    if(room.get_leader() is not player or request.sid != player.sid):
        emit('error', 'Nice try! XD')
        return

    room.game.quest_history[-1]['on'] = data['members']

    emit('prequest_vote', data['members'], room=room_id)

@socketio.on('prequest_vote')
def on_prequest_vote(data):
    global rooms
    name = data['name']
    room_id = data['room_id']
    room:Room = rooms[room_id]
    player:Player = room.players[name]

    if request.sid != player.sid:
        emit('error', 'Nice try! XD')
        return
    
    if('votes' not in room.game.quest_history[-1]):
        room.game.quest_history[-1]['votes'] = []

    votes = room.game.quest_history[-1]['votes']

    if(data['vote']):
        votes.append(name)

    room.game.vote_count += 1
    if(room.game.vote_count == len(room.players)):
        room.game.vote_count = 0
        emit('prequest_result', votes, room=room_id)
        if len(votes) > len(room.players)/2:
            for member in room.game.quest_history[-1]['on']:
                member:Player = room.players[member]
                emit('quest_vote', member.card.get_options(room), room=member.sid)
        else:
            room.game.unsent_quests += 1
            activate_leader(room_id)

@socketio.on('quest_vote')
def on_quest_vote(data):
    global rooms
    name = data['name']
    room_id = data['room_id']
    room:Room = rooms[room_id]
    player:Player = room.players[name]
    
    if request.sid != player.sid:
        emit('error', 'Nice try! XD')
        return
    
    if('results' not in room.game.quest_history[-1]):
        room.game.quest_history[-1]['results'] = []
    
    choice = data['choice']

    room.game.quest_history[-1]['results'].append(choice)

    room.game.vote_count += 1
    if(room.game.vote_count == room.game.get_quest().size):
        room.game.vote_count = 0

        results = room.game.quest_history[-1]['results']
        passed = room.game.get_quest().evaluate(results)
        room.game.quest_history[-1]['passed'] = passed
        if(passed):
            room.game.passes += 1
        else:
            room.game.fails += 1

        random.shuffle(results)
        emit('quest_result', {'results':results, 'passed': passed}, room=room_id)
        activate_leader(room_id)


def activate_leader(room_id):
    global rooms
    room:Room = rooms[room_id]
    room.game.quest_history.append({'leader':room.get_leader().name})
    emit('leader', {'count':room.game.get_quest().size, 'leader':room.get_leader().name}, room=room_id)


if __name__ == '__main__':
    socketio.run(app, debug=True)