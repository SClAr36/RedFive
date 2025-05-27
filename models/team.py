# 队伍类：一个队伍包含两个玩家、一个主数，以及分数和是否为庄家标志

from dataclasses import dataclass, field
from typing import List, Optional
from .player import Player
from .enums import Rank
from .cards import Cards

@dataclass
class Team:
    """代表一个队伍，含成员、主数、得分和是否为庄"""
    team_id: int                    # 队伍编号（0 或 1）
    members: List[Player] = field(default_factory=list)          # 队伍成员
    trump_rank: Rank = None               # 当前主数（例如 Rank.FIVE）
    is_dealer: bool = False        # 是否为当前庄家


    def promote_trump(self): #TODO：抢二打四
        """如果庄家赢了一局，主数 +1（若已是最大则宣布胜利）"""
        all_ranks = Cards.RANK_TRUMP_ORDER
        idx = Cards.RANK_TRUMP_ORDER.index(self.trump_rank)
        if self.trump_rank == Rank.A:
            return "victory"
        self.trump_rank = Cards.RANK_TRUMP_ORDER[idx + 1]
        return self.trump_rank

    def add_member(self, player: Player) -> Optional[str]:
        """
        尝试将 player 加入本队伍。
        如果已满（>=2人），返回错误信息；否则添加并返回 None。
        """
        if len(self.members) >= 2:
            return f"❌ 队伍已满（现有{len(self.members)}人！"
        self.members.append(player)
        return None

    def remove_member(self, player: Player):
        """将 player 从本队伍移除（如果在列表中）"""
        if player in self.members:
            self.members.remove(player)