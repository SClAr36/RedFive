# 队伍类：一个队伍包含两个玩家、一个主数，以及分数和是否为庄家标志

from dataclasses import dataclass
from typing import List
from .player import Player
from .enums import Rank

@dataclass
class Team:
    """代表一个队伍，含成员、主数、得分和是否为庄"""
    team_id: int                    # 队伍编号（0 或 1）
    members: List[Player]          # 队伍成员
    trump_rank: Rank               # 当前主数（例如 Rank.FIVE）
    is_dealer: bool = False        # 是否为当前庄家

    def promote_trump(self):
        """如果庄家赢了一局，主数 +1（循环回到最小）"""
        all_ranks = list(Rank)
        idx = all_ranks.index(self.trump_rank)
        self.trump_rank = all_ranks[(idx + 1) % len(all_ranks)]
