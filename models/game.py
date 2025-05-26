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
    dealer: int
    dealer_team_points: int
    challenger_team_points: int

@dataclass
class Game:
    """一盘完整的牌局，管理多个 Deal"""
    players: List[Player]
    teams: Dict[int, Team]
    history: List[DealResult] = field(default_factory=list)
    current_deal: Optional[Deal] = None
    deal_counter: int = 0
    is_default: bool = True

    # @property
    # def dealer(self) -> Team:
    #     """获取当前庄家队伍"""
    #     return next(t for t in self.teams.values() if t.is_dealer)

    # @property
    # def challenger(self) -> Team:
    #     return next(t for t in self.teams.values() if not t.is_dealer)

    def start_new_deal(self, suit: str, dealer: Player, dealer_team: Team):
        """开始新的一局 deal（由 Game 控制编号）"""
        self.deal_counter += 1
        self.current_deal = Deal(
            deal_number=self.deal_counter,
            dealer=dealer,
            dealer_team=dealer_team,
            challenger_team=self.teams[(dealer_team.team_id + 1) % 2],
            trump_rank=dealer_team.trump_rank,
            trump_suit=suit
        )
        return self.current_deal

    def finish_current_deal(self):
        """结算当前 deal 并返回:
        庄家和挑战者的得分、下一个庄家队伍、下一个庄家玩家和下一个主数。
        """
        deal = self.current_deal
        if not deal:
            raise RuntimeError("当前没有正在进行的 Deal")

        dealer_score, challenger_score = deal.final_points()
        if challenger_score >= 80:
            # 挑战成功，换庄
            deal.dealer_team.is_dealer = False
            deal.challenger_team.is_dealer = True
            next_dealer_team = deal.challenger_team
            next_dealer = self.players[(deal.dealer.player_number + 1) % 4 ]
            next_trump_rank = deal.challenger_team.trump_rank
        else:
            # 挑战失败，庄家主数+1
            next_dealer_team = deal.dealer_team
            next_dealer = next(p for p in self.players if p.team_id == deal.dealer_team.team_id and p != deal.dealer)
            next_trump_rank = deal.dealer_team.promote_trump()        
        
        if next_trump_rank == "victory":
            print("🏁 游戏结束，庄家完全胜利！")
        
        self.history.append(DealResult(
            deal_number=deal.deal_number,
            dealer=deal.dealer,
            dealer_team_points=dealer_score,
            challenger_team_points=challenger_score
        ))

        return dealer_score, challenger_score, next_dealer_team, next_dealer, next_trump_rank
