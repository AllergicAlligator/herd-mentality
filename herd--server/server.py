import asyncio
import websockets
import json
import random
import string
from functions import countanswers, winners
from prompts import prompts

rooms = {}

def generate_code():
    return "".join(random.choices(string.ascii_uppercase + string.digits, k=6))

def broadcast(room_code, message):
    room = rooms[room_code]
    for ws in list(room["players"]):
        try:
            asyncio.ensure_future(ws.send(json.dumps(message)))
        except:
            pass

def remove_player(room_code, ws):
    room = rooms[room_code]
    if ws in room["players"]:
        name = room["players"][ws]
        print(f"{name} disconnected from room {room_code}")
        del room["players"][ws]
        if room_code in rooms:
            broadcast(room_code, {
                "type": "lobby",
                "code": room_code,
                "players": list(room["players"].values())
            })

def all_answered(room_code):
    room = rooms[room_code]
    active_players = set(room["active_players"])
    answered = set(room["answers"].keys())
    return answered >= active_players

async def game_loop(room_code):
    room = rooms[room_code]
    room["active_players"] = set(room["players"].values())
    round_number = 1
    WINNING_SCORE = 8

    while True:
        question = random.choice(prompts)
        room["question"] = question
        room["answers"] = {}
        room["next_round_ready"] = False

        broadcast(room_code, {
            "type": "question",
            "round": round_number,
            "question": question,
            "scoreboard": room["scoreboard"]
        })

        while not all_answered(room_code):
            await asyncio.sleep(0.5)

        counts = countanswers(len(room["answers"]), room["answers"])
        room["scoreboard"] = winners(counts, room["answers"], room["scoreboard"])

        broadcast(room_code, {
            "type": "results",
            "answers": room["answers"],
            "scoreboard": room["scoreboard"]
        })

        for ws, name in list(room["players"].items()):
            if name == room["host"]:
                await ws.send(json.dumps({
                    "type": "results_host",
                    "answers": room["answers"],
                    "scoreboard": room["scoreboard"]
                }))

        for name, score in room["scoreboard"].items():
            if score >= WINNING_SCORE:
                broadcast(room_code, {"type": "winner", "name": name})
                return

        while not room.get("next_round_ready", False):
            await asyncio.sleep(0.5)

        room["active_players"] = set(room["players"].values())
        round_number += 1

async def handle_client(ws):
    room_code = None
    try:
        async for message in ws:
            data = json.loads(message)
            action = data.get("action")

            if action == "create":
                room_code = generate_code()
                name = data["name"]
                rooms[room_code] = {
                    "players": {ws: name},
                    "answers": {},
                    "scoreboard": {name: 0},
                    "question": "",
                    "started": False,
                    "next_round_ready": False,
                    "host": name,
                    "active_players": set()
                }
                print(f"Room {room_code} created by {name}")
                await ws.send(json.dumps({
                    "type": "created",
                    "code": room_code,
                    "players": [name]
                }))

            elif action == "join":
                room_code = data["code"].strip().upper()
                name = data["name"]

                if room_code not in rooms:
                    await ws.send(json.dumps({"type": "error", "message": "Room not found!"}))
                    continue

                room = rooms[room_code]
                rooms[room_code]["players"][ws] = name
                rooms[room_code]["scoreboard"][name] = 0
                print(f"{name} joined room {room_code}")

                if room["started"]:
                    await ws.send(json.dumps({
                        "type": "waiting_next_round",
                        "scoreboard": room["scoreboard"]
                    }))
                else:
                    broadcast(room_code, {
                        "type": "lobby",
                        "code": room_code,
                        "players": list(rooms[room_code]["players"].values())
                    })

            elif action == "start":
                room_code = data["code"]
                room = rooms[room_code]

                if len(room["players"]) < 2:
                    await ws.send(json.dumps({"type": "error", "message": "Need at least 2 players!"}))
                    continue

                room["started"] = True
                asyncio.ensure_future(game_loop(room_code))

            elif action == "answer":
                found_code = None
                for code, room in rooms.items():
                    if ws in room["players"]:
                        found_code = code
                        break

                if not found_code:
                    continue

                room = rooms[found_code]
                name = room["players"].get(ws)

                if name and name not in room["answers"] and name in room["active_players"]:
                    room["answers"][name] = data["answer"].strip().lower()
                    print(f"[Room {found_code}] {name} answered: {data['answer']}")
                    await ws.send(json.dumps({"type": "waiting"}))

            elif action == "next_round":
                for code, room in rooms.items():
                    if ws in room["players"]:
                        room["next_round_ready"] = True
                        break

            elif action == "quit":
                for code, room in list(rooms.items()):
                    if ws in room["players"]:
                        broadcast(code, {"type": "game_quit"})
                        rooms.pop(code)
                        break

    except websockets.exceptions.ConnectionClosed:
        pass
    finally:
        if room_code and room_code in rooms:
            remove_player(room_code, ws)

async def main():
    print("Server started on port 8000")
    async with websockets.serve(handle_client, "0.0.0.0", 8000):
        await asyncio.Future()

asyncio.run(main())