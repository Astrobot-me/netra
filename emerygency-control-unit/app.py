from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app, cors_allowed_origins="*")

ambulance_sockets = {}  # ambulanceId -> socketId mapping

@app.route('/')
def index():
    return render_template('index.html')

@socketio.on('register-ambulance')
def handle_register_ambulance(data):
    ambulance_id = data.get('ambulanceId')
    ambulance_sockets[ambulance_id] = request.sid
    print(f"Ambulance {ambulance_id} registered with sid {request.sid}")

@socketio.on('disconnect')
def handle_disconnect():
    sid = request.sid
    to_remove = [amb_id for amb_id, s_id in ambulance_sockets.items() if s_id == sid]
    for amb_id in to_remove:
        print(f"Ambulance {amb_id} disconnected")
        ambulance_sockets.pop(amb_id)

@socketio.on('ambulance-operate')
def handle_ambulance_operate(data):
    ambulance_id = data.get('ambulanceId')
    trigger = data.get('trigger')
    print(f"Assigning ambulance {ambulance_id} with trigger {trigger}")

    ambulance_sid = ambulance_sockets.get(ambulance_id)
    if ambulance_sid:
        emit('trigger-assigned', {'trigger': trigger}, room=ambulance_sid)
        print(f"Trigger sent to ambulance {ambulance_id}")
    else:
        print(f"Ambulance driver {ambulance_id} not connected!")

if __name__ == '__main__':
    socketio.run(app, debug=True)
