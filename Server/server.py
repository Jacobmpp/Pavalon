from flask import Flask, render_template, request, redirect, url_for
from flask_socketio import SocketIO, join_room, leave_room, emit
from utils import *

selectable_roles = [
    ' Merlin', 
    ' Assasin', 
    '1Loyal Servant of Arthur', 
    '2Loyal Servant of Arthur', 
    '3Loyal Servant of Arthur', 
    '4Loyal Servant of Arthur', 
    '5Loyal Servant of Arthur', 
    '1Minion of Mordred', 
    '2Minion of Mordred', 
    '3Minion of Mordred', 
    ' Mordred',
    ' Morgana', 
    ' Percival', 
    ' Oberon', 
    ' Good Sorcerer', 
    ' Bad Sorcerer', 
    ' Good Lancelot', 
    ' Bad Lancelot', 
    ' Lunatic', 
    ]

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
    room_id = request.form['room_id']
    name = request.form['name']
    if 'roles' in request.form:
        roles = []
        for role in selectable_roles:
            if(role in request.form and request.form[role]):
                roles.append(role[1:])
        rooms[room_id] = Room(cards=roles)
        return redirect(url_for('room', room_id=room_id))

    if room_id not in rooms:
        return render_template('select_roles.html', room_id=room_id, roles=selectable_roles)
    return render_template('index.html', room_id=room_id, message='Room already existed')

@app.route('/get_rooms', methods=['GET'])
def get_rooms():
    global rooms
    return list(rooms.keys()), 200

@app.route('/room', methods=['POST'])
def room():
    global rooms
    room_id = request.form['join_id']
    name = request.form['name']
    current_room = rooms[room_id]
    return render_template('role.html', room_id=room_id, name=name, roles=[str(r) for r in current_room.cards])
    return repr(rooms[room_id]).replace("\n", "<br>"), 200

@socketio.on('join')
def on_join(data):
    global rooms
    username = data['username']
    room_id = data['join_id']
    join_room(room_id)

    if room_id not in rooms:
        emit('That room does not exist yet.')

    if rooms[room_id].add_player(Player(username)):
        emit('update', f'{username} has joined the room.', room=room_id)

        if len(rooms[room_id].players) == len(rooms[room_id].cards):
            emit('game_start', 'The game is starting!', room=room_id)
            rooms[room_id].dist_cards()
            for player in rooms[room_id].players.values():
                emit('role', player.card.game_start(rooms[room_id]), room=request.sid)
    else:
        emit('error', 'You are already in that room.')

@socketio.on('leave')
def on_leave(data):
    global rooms
    username = data['username']
    room_id = data['room_id']
    leave_room(room_id)

    if room_id in rooms and rooms[room_id].remove_player(username):
        emit('update', f'{username} has left the room.', room=room_id)

    if len(rooms[room_id].players) == 0:
        del rooms[room_id]

if __name__ == '__main__':
    socketio.run(app, debug=True)