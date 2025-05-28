import uuid
import json
from typing import Dict
from websockets import WebSocketServerProtocol

from models.player import Player
from models.room import Room
from models.team import Team


class RoomManager:
    """统一管理所有房间（room_id）、每个连接对应的玩家，以及广播"""

    def __init__(self):
        self.rooms: Dict[str, Room] = {}
        self.ws_to_player: Dict[WebSocketServerProtocol, Player] = {}

    def assign_player(self, ws) -> Player:
        """为新 WebSocket 分配房间和玩家"""
        for room in self.rooms.values():
            if len(room.players) < 4:
                break
        else:
            room_id = str(uuid.uuid4())[:8]
            players = []
            teams = {
                0: Team(team_id=0, members=[]),
                1: Team(team_id=1, members=[]),
            }
            room = Room(room_id=room_id, players=players, teams=teams)
            self.rooms[room_id] = room

        player = Player(player_id=str(uuid.uuid4())[:8])
        room.players.append(player)
        self.ws_to_player[ws] = player
        return player

    def get_room(self, ws) -> Room:
        """根据连接 ws 找到玩家所在 Room 实例"""
        player = self.ws_to_player[ws]
        for room in self.rooms.values():
            if player in room.players:
                return room
        raise KeyError("未找到对应房间")

    async def broadcast(self, room: Room, payload: dict, exclude_ws=None):
        """给房间内所有玩家广播消息，可选排除某一连接"""
        msg = json.dumps(payload)
        for ws, p in list(self.ws_to_player.items()):
            if p in room.players and ws != exclude_ws:
                try:
                    await ws.send(msg)
                except:
                    pass
