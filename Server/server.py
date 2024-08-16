from flask import Flask, render_template, request, redirect, url_for, session
import random
from utils import *



app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Replace with a secure key in production

selectable_roles = [
    'Merlin', 
    'Assasin', 
    'Loyal Servant of Arthur', 
    'Loyal Servant of Arthur', 
    'Loyal Servant of Arthur', 
    'Loyal Servant of Arthur', 
    'Loyal Servant of Arthur', 
    'Minion of Mordrid', 
    'Minion of Mordrid', 
    'Minion of Mordrid', 
    'Mordred', 
    'Morgana', 
    'Percival', 
    'Oberon', 
    'Good Sorcerer', 
    'Bad Sorcerer', 
    'Good Lancelot', 
    'Bad Lancelot', 
    'Lunatic', 
    ]

rooms = {}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/join_room', methods=['POST'])
def join_room():
    room_id = request.form['room_id']
    session['room_id'] = room_id
    if room_id not in rooms:
        redirect(url_for('role_select'))
    return redirect(url_for('room', room_id=room_id))
    
@app.route('/role_select', methods=['GET', 'POST'])
def join_room():
    room_id = session['room_id']
    if request.method == 'POST':
        roles = session['roles']
        print(roles)
        return roles
        rooms[room_id] = Room(room_id,[cards[r] for r in roles])
    return render_template('role_select.html', room_id=room_id, roles=selectable_roles)


@app.route('/room/<room_id>', methods=['GET', 'POST'])
def room(room_id):
    if room_id not in rooms:
        return "Room not found!", 404

    if request.method == 'POST':
        if len(rooms[room_id]['members']) < rooms[room_id]['max_players']:
            user = request.form['username']
            return redirect(url_for('waiting'))
        else:
            return "Room is full!", 400

    return render_template('room.html', room_id=room_id, members=rooms[room_id]['members'])

@app.route('/role')
def role():
    username = session.get('name')
    room = session.get('room')
    if not username or not room:
        return redirect(url_for('index'))
    
    return render_template('role.html', username=username, role=role)

@app.route('/perform_action')
def perform_action():
    role = session.get('role')
    room = session.get('room')
    if not role:
        return redirect(url_for('index'))


    return "sdgfs"

if __name__ == '__main__':
    app.run(debug=True)