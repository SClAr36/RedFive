# 玩家类：定义一个游戏玩家的基本信息和手牌

from dataclasses import dataclass, field
from typing import List, Optional

@dataclass
class Player:
    """表示一个玩家，包括身份、昵称和手牌"""
    player_id: str                         # 玩家唯一 ID
    nickname: Optional[str] = None        # 可选昵称
    hand: List[str] = field(default_factory=list)  # 当前手牌
