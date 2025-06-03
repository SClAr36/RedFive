# 玩家类：定义一个游戏玩家的基本信息和手牌

from dataclasses import dataclass, field
from typing import List, Optional
#from room_manager import RoomManager #FIXME: 需要导入 RoomManager
#from .room import Room

@dataclass
class Player: #添加房间号、team_id 改为 Team 类信息
    """表示一个玩家，包括身份、昵称和手牌"""
    player_id: str                         # 玩家唯一 ID
    #room_id: Optional[str] = None          # 所属房间 ID
    nickname: Optional[str] = None        # 可选昵称
    hand: List[str] = field(default_factory=list)  # 当前手牌
    team_id: Optional[int] = None         # 所属队伍 ID
    player_number: Optional[int] = None              # 玩家在游戏中的序号（0~3）
    is_dealer: bool = False               # 是否为庄家
    hidden_cards: List[str] = field(default_factory=list)  # 藏牌
    
    # def get_room(self) -> Optional[Room]:
    #     """根据 room_id 获取对应的 Room 实例"""
    #     for room in rooms.values():
    #         if self.player_id in [p.player_id for p in room.players]:
    #             return room
    #     return None
    
    # def get_team(self) -> Optional['Team']:
    #     """根据 team_id 获取对应的 Team 实例"""
    #     for team in teams:
    #         if team.team_id == self.team_id:
    #             return team
    #     return None
