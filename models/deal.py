from dataclasses import dataclass, field
from typing import List, Optional, Tuple, Dict
from .team import Team
from .enums import Rank

from .trick import Trick


@dataclass
class Deal:
    """一局完整的发牌与25轮出牌(25 tricks)，包含局编号"""
    deal_number: int                         # 第几局（由 Game 控制）
    dealer_team: Team                        # 庄队
    challenger_team: Team                    # 挑战队
    trump_rank: Rank                         # 主数
    trump_suit: str                          # 主花色（例如 '♠'）
    tricks: List[Trick] = field(default_factory=list)  # 每轮 trick 记录

    def get_team_points(self) -> Dict[int, int]:
        """统计两支队伍的得分"""
        result = {
            self.dealer_team.team_id: 0,
            self.challenger_team.team_id: 0
        }
        for trick in self.tricks:
            if trick.winning_team_id is not None:
                result[trick.winning_team_id] += trick.points
        return result

    def finish_deal(self) -> Tuple[Dict[int, int], Team, Rank]:
        """
        结算本轮，返回：
        - scores: 双方得分 {team_id: points}
        - next_dealer: 下一轮的庄队 Team
        - next_trump_rank: 下一轮的主数（来自庄家）
        """
        scores = self.get_team_points()
        challenger_score = scores[self.challenger_team.team_id]

        if challenger_score >= 80:
            # 挑战成功，换庄
            self.dealer_team.is_dealer = False
            self.challenger_team.is_dealer = True
            next_dealer = self.challenger_team
        else:
            # 挑战失败，庄家主数+1
            result = self.dealer_team.promote_trump()
            next_dealer = self.dealer_team
        
        if result == "victory":
            print("🏁 游戏结束，庄家完全胜利！")

        return scores, next_dealer, next_dealer.trump_rank