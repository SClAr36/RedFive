from dataclasses import dataclass, field
from typing import List, Dict, Optional
from .player import Player
from .team import Team
from .game import Game
from .deal import Deal

#TODO：支持房间改名
@dataclass
class Room:
    """一个房间，包含固定的玩家、队伍，允许多局游戏"""
    room_id: str
    players: List[Player] = field(default_factory=list)
    teams: Dict[int, Team] = field(default_factory=dict)
    active_game: Optional[Game] = None
    past_games: List[Game] = field(default_factory=list)
    game_count: int = 0

    # 开始游戏，默认两队主数为 2
    def start_new_game(self, rank0=None, rank1=None): #FIXME:主数输入不一定按0、1顺序，可能按庄顺序
        # 清空当前游戏状态
        if self.active_game:
            self.past_games.append(self.active_game)
        # 设置两队主数为指定的 rank0 和 rank1
        self.teams[0].trump_rank = rank0
        self.teams[1].trump_rank = rank1
        # 初始化新的游戏
        self.active_game = Game(players=self.players, teams=self.teams)
        self.game_count += 1
        return self.active_game
