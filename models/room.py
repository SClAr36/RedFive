from dataclasses import dataclass, field
from typing import List, Dict, Optional
from .player import Player
from .team import Team
from .game import Game
from .deal import Deal

@dataclass
class Room:
    """一个房间，包含固定的玩家、队伍，允许多局游戏"""
    room_id: str
    players: List[Player] = field(default_factory=list)
    teams: Dict[int, Team] = field(default_factory=dict)
    active_game: Optional[Game] = None
    past_games: List[Game] = field(default_factory=list)
    game_count: int = 0

    # 开始默认游戏
    def start_new_game(self):
        # if self.active_game:
        #     self.past_games.append(self.active_game)
        # 将两队主数设为 2
        self.teams[0].trump_rank = 2
        self.teams[1].trump_rank = 2
        self.active_game = Game(players=self.players, teams=self.teams)
        self.game_count += 1
        
    # 开始一局独立的 deal，但仍把这个 deal 包裹在 active_game 中
    def start_independent_deal_game(self):
        self.teams[0].trump_rank = None
        self.teams[1].trump_rank = None
        self.active_game = Game(players=self.players, teams=self.teams, is_default=False)

