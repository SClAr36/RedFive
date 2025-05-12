# Game 类：完整管理一个房间的游戏状态，包括玩家、队伍和历史记录

from dataclasses import dataclass, field
from typing import List, Dict
from .player import Player
from .team import Team
from .enums import Rank

@dataclass
class RoundResult:
    """一局结束后的结果记录"""
    dealer_team_id: int
    winner_team_id: int
    points: int

@dataclass
class Game:
    """一个完整的 4 人房间游戏，包含玩家、队伍、历史等"""
    players: List[Player]
    teams: Dict[int, Team]
    history: List[RoundResult] = field(default_factory=list)

    def __post_init__(self):
        """初始化：把 4 个玩家分为两个队"""
        assert len(self.players) == 4
        self.teams[0].members = self.players[:2]
        self.teams[1].members = self.players[2:]

    @property
    def dealer(self) -> Team:
        """获取当前庄家队伍"""
        return next(t for t in self.teams.values() if t.is_dealer)

    def start_round(self, dealer_team_id: int):
        """开始新一局游戏，指定哪个队是庄家"""
        for t in self.teams.values():
            t.is_dealer = (t.team_id == dealer_team_id)

    def finish_round(self, winner_team_id: int, points: int = 1):
        """一局结束，记录赢家并更新分数/主数"""
        dealer_id = self.dealer.team_id
        self.history.append(RoundResult(dealer_id, winner_team_id, points))
        if winner_team_id == dealer_id:
            self.teams[dealer_id].promote_trump()
        self.teams[winner_team_id].score += points
