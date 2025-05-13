from dataclasses import dataclass, field
from typing import List, Tuple, Optional, Dict

from .player import Player
from .team import Team
from .cards import Cards

@dataclass
class Trick:
    """表示一轮出牌（4人各出一张）的记录和结果"""
    trump_rank: str  # 主数
    trump_suit: str  # 主花色
    starting_player_index: int  # 这一轮从哪位玩家开始（0~3）(加上默认庄家)
    winning_team_id: Optional[int] = None
    trick_number: int = 0 #这是第几轮出牌
    play_sequence: List[Tuple[int, str, int]] = field(default_factory=list)  # 每一出牌: (player_number, card, team_id)
    valid_play_sequence: List[Tuple[int, str, int]] = field(default_factory=list) #有效牌记录
    winining_player_number: Optional[int] = None  # 赢家编号
    points: int = 0
    
    @property
    def is_first_play(self) -> bool:
        return len(self.play_sequence) == 0
    
    def is_following_legally(self, player: Player, cards: List[str]) -> bool:
        """
        判断非首出玩家是否符合跟牌规则：
        - 如果有和首家相同花色的牌，必须跟同花色
        - 否则可自由出牌
        """
        # if not self.play_sequence:
        #     return True  # 首出无需跟
    
        # lead_card = self.play_sequence[0][1]
        # lead_suit = Cards.get_suit(lead_card)
        # player_suits = [Cards.get_suit(c) for c in player.hand]
    
        # if lead_suit in player_suits:
        #     return all(Cards.get_suit(c) == lead_suit for c in cards)
    
        return True  # 没有 lead_suit 可以出其他
    
    def record_play(self, player: Player, cards: List[str], trump_rank: str, trump_suit: str) -> Optional[str]:
        """
        判断并记录玩家出牌，处理合法性和代表牌记录
        """
        expected = (self.starting_player_index + len(set(pn for pn, _, _ in self.play_sequence))) % 4
        if player.player_number != expected:
            return f"❌ 现在不是你出牌，请等待玩家 {expected} 出牌"
    
        # 首出：直接判定牌型是否合法
        if self.is_first_play:
            valid, representative = Cards.is_valid_combo(cards, trump_rank, trump_suit)
            if not valid:
                return "❌ 非法牌型！请重新出牌！"
            else:
                self.valid_play_sequence.append((player.player_number, representative, player.team_id))
    
        else:
            # 非首出：必须跟花
            if not self.is_following_legally(player, cards):
                return "❌ 出牌必须跟首家花色！"
    
            # 检查牌型是否符合规则（比如两张必须完全相同等）
            valid, representative = Cards.is_valid_combo(cards, trump_rank, trump_suit)
            if valid:
                self.valid_play_sequence.append((player.player_number, representative, player.team_id))
    
        # 合法则加入记录
        for card in cards:
            self.play_sequence.append((player.player_number, card, player.team_id))
    
        return None    
            
    def resolve(self) -> Tuple[int, str, int, int]:
        """
        结算当前一轮 Trick：
        - 确定赢家编号和牌
        - 记录胜利队伍 ID
        - 累加得分
        返回：(赢家编号, 最大牌, 队伍ID, 总得分)
        """
    
        # 找出最大牌
        winner_number, winning_card, winning_team = max(
            self.valid_play_sequence, key=lambda x: Cards.card_value(x[1], self.trump_rank, self.trump_suit)
        )
    
        self.winning_player_number = winner_number
        self.winning_team_id = winning_team
    
        # 统计得分
        self.points = sum(
            5 if Cards.get_rank(card) == '5' else
            10 if Cards.get_rank(card) in ['10', 'K'] else 0
            for _, card, _ in self.play_sequence
        )
    
        return winner_number, winning_card, winning_team, self.points
    
    



