import uuid
import json
from typing import Dict, Optional
from websockets import WebSocketServerProtocol

from models.player import Player
from models.room import Room
from models.team import Team


#TODO: assign player 和 join room 分开，以便玩家在index页面能做更多事（比如修改昵称）存player进localstorage
#TODO：退出房间时自动清理玩家和房间
class RoomManager:
    """统一管理所有房间（room_id）、每个连接对应的玩家，以及广播"""

    def __init__(self):
        self.rooms: Dict[str, Room] = {}
        self.ws_to_player: Dict[WebSocketServerProtocol, Player] = {}

    def create_room(self, ws, room_name: str = None) -> Room:
        """创建一个新房间，返回 Room 实例"""
        room_id = str(uuid.uuid4())
        room = Room(room_id=room_id, room_name=room_name, teams={0: Team(team_id=0, members=[]), 1: Team(team_id=1, members=[])})
        self.rooms[room_id] = room
        return room

    def assign_player(self, ws, room: Optional[Room] = None) -> Player:
        """为新 WebSocket 分配房间和玩家"""
        """自动分配房间时选未满的；若没找到或房间已满，则创建新房间"""
        if room is None:
            room = next((r for r in self.rooms.values() if len(r.players) < 4), None)
            if room is None:
                room = self.create_room("未命名房间")  # 👈 只传名称，不传 ws
    
        if len(room.players) >= 4:
            # 房间满员时，抛出异常或返回 None
            raise ValueError("房间已满，无法加入。请重新选择！")

        # 为新玩家创建 Player 实例
        player = Player(player_id=str(uuid.uuid4()))
        self.ws_to_player[ws] = player
        # 处理房间内信息：玩家加入、设置 player number
        room.players.append(player)
        number = room.players.index(player)
        player.player_number = number
        return player

    def get_room(self, ws) -> Room:
        """根据连接 ws 找到玩家所在 Room 实例"""
        player = self.ws_to_player[ws]
        for room in self.rooms.values():
            if player in room.players:
                return room
        raise KeyError("未找到对应房间")
    
    def get_team(self, ws) -> Team:
        """根据连接 ws 找到玩家所在 Team 实例"""
        player = self.ws_to_player[ws]
        room = self.get_room(ws)
        for team in room.teams.values():
            if player in team.members:
                return team
        raise KeyError("未找到对应队伍")
    
    def get_player(self, ws) -> Player:
        """根据连接 ws 找到对应的 Player 实例"""
        return self.ws_to_player.get(ws)

    async def broadcast(self, room: Room, payload: dict, exclude_ws=None):
        """给房间内所有玩家广播消息，可选排除某一连接"""
        msg = json.dumps(payload)
        for ws, p in list(self.ws_to_player.items()):
            if p in room.players and ws != exclude_ws:
                try:
                    await ws.send(msg)
                except:
                    pass
