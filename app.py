from flask import Flask, render_template, request, session, redirect, url_for
from flask_socketio import SocketIO, join_room, leave_room, send
import random
import string
from flask_socketio import emit

app = Flask(__name__)
app.config["SECRET_KEY"] = "your_secret_key"
socketio = SocketIO(app)

rooms = {}

def generate_unique_code(length):
    while True:
        code = ''.join(random.choices(string.ascii_uppercase, k=length))
        if code not in rooms:
            return code

@app.route("/", methods=["GET", "POST"])
def home():
    session.clear()
    if request.method == "POST":
        name = request.form.get("name")
        code = request.form.get("code")
        join = request.form.get("join", False)
        create = request.form.get("create", False)

        if not name:
            return render_template("home.html", error="Please enter a name.", code=code, name=name)

        if join != False and not code:
            return render_template("home.html", error="Please enter a room code.", code=code, name=name)
        
        room = code
        if create != False:
            room = generate_unique_code(4)
            rooms[room] = {"members": 0, "messages": []}
        elif code not in rooms:
            return render_template("home.html", error="Room does not exist.", code=code, name=name)
        
        session["room"] = room
        session["name"] = name
        return redirect(url_for("room"))

    return render_template("home.html")

@app.route("/room")
def room():
    room = session.get("room")
    if room is None or session.get("name") is None or room not in rooms:
        return redirect(url_for("home"))

    return render_template("room.html", code=room, messages=rooms[room]["messages"])

@socketio.on("message")
def message(data):
    room = session.get("room")
    if room is not None and room in rooms:
        content = {
            "name": session.get("name"),
            "message": data["data"]
        }
        send(content, to=room)
        rooms[room]["messages"].append(content)
        print(f"{session.get('name')} said: {data['data']}")

@socketio.on("connect")
def connect():
    room = session.get("room")
    name = session.get("name")
    if room is not None and name is not None:
        if room in rooms:
            join_room(room)
            send({"name": name, "message": "has entered the room"}, to=room)
            rooms[room]["members"] += 1
            print(f"{name} joined room {room}")
        else:
            leave_room()

@socketio.on('disconnect')
def disconnect():
    room = session.get("room")
    name = session.get("name")
    if room is not None and name is not None:
        if room in rooms:
            leave_room(room)
            rooms[room]["members"] -= 1
            if rooms[room]["members"] <= 0:
                del rooms[room]
            send({"name": name, "message": "has left the room"}, to=room)
            print(f"{name} has left room {room}")
    return redirect(url_for("home"))


if __name__ == "__main__":
    socketio.run(app, debug=True)
