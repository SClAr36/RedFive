# Game 类：完整管理一局游戏，包括玩家、队伍和每轮历史记录
from dataclasses import dataclass, field
from typing import List, Dict, Optional
from .player import Player
from .team import Team
from .deal import Deal

@dataclass
class DealResult:
    """记录一局 Deal 的结果"""
    deal_number: int
    dealer_team_id: int
    winner_team_id: int
    points: int

@dataclass
class Game:
    """一盘完整的牌局，管理多个 Deal"""
    players: List[Player]
    teams: Dict[int, Team]
    history: List[DealResult] = field(default_factory=list)
    current_deal: Optional[Deal] = None
    deal_counter: int = 0

    # @property
    # def dealer(self) -> Team:
    #     """获取当前庄家队伍"""
    #     return next(t for t in self.teams.values() if t.is_dealer)

    # @property
    # def challenger(self) -> Team:
    #     return next(t for t in self.teams.values() if not t.is_dealer)

    def start_new_deal(self, suit: str, dealer_team: Team, challenger_team: Team):
        """开始新的一局 deal（由 Game 控制编号）"""
        self.deal_counter += 1
        self.current_deal = Deal(
            deal_number=self.deal_counter,
            dealer_team=dealer_team,
            challenger_team=challenger_team,
            trump_rank=dealer_team.trump_rank,
            trump_suit=suit
        )

    def finish_current_deal(self) -> Dict:
        """结算当前 deal 并返回下轮信息"""
        if not self.current_deal:
            raise RuntimeError("当前没有正在进行的 Deal")

        scores, next_dealer, next_trump_rank = self.current_deal.finish_deal()
        winner_id = max(scores, key=scores.get)

        self.history.append(DealResult(
            deal_number=self.current_deal.deal_number,
            dealer_team_id=self.current_deal.dealer_team.team_id,
            winner_team_id=winner_id,
            points=scores[winner_id]
        ))

        return {
            "scores": scores,
            "next_dealer_team_id": next_dealer.team_id,
            "next_trump_rank": next_trump_rank.name,
            "deal_number": self.current_deal.deal_number
        }
