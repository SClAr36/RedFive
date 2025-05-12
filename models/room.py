from dataclasses import dataclass, field
from typing import List, Dict, Optional
from .player import Player
from .team import Team
from .game import Game
from .enums import Rank

@dataclass
class Room:
    """一个房间，包含固定的玩家、队伍，允许多局游戏"""
    room_id: str
    players: List[Player] = field(default_factory=list)
    teams: Dict[int, Team] = field(default_factory=dict)
    active_game: Optional[Game] = None
    past_games: List[Game] = field(default_factory=list)
    game_count: int = 0

    def start_new_game(self, new_team_config: Optional[Dict[int, List[Player]]] = None):
        if self.active_game:
            self.past_games.append(self.active_game)

        # 如果指定了新的分队方式，就构造新的 Team，否则默认分组
        if new_team_config:
            teams = {
                0: Team(team_id=0, members=new_team_config[0], trump_rank=Rank.TWO),
                1: Team(team_id=1, members=new_team_config[1], trump_rank=Rank.TWO),
            }
        else:
            teams = {
                0: Team(team_id=0, members=[], trump_rank=Rank.TWO),
                1: Team(team_id=1, members=[], trump_rank=Rank.TWO),
            }

        self.active_game = Game(players=self.players, teams=teams)
        self.round_count += 1

