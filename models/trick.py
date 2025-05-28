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
        # 获取首出玩家编号
        lead_player_number = self.play_sequence[0][0]
    
        # 获取首出玩家出的所有牌
        lead_cards = [card for pn, card, _ in self.play_sequence if pn == lead_player_number]
        lead_count = len(lead_cards)
        # 出牌数量必须一致
        if len(cards) != len(lead_cards):
            return False, "出牌数量不一致"
    
        lead_rep_card = self.valid_play_sequence[0][1]
        lead_value = Cards.card_value(lead_rep_card, self.trump_rank, self.trump_suit)
        lead_suit = Cards.get_suit(lead_rep_card)
    
        player_cards = player.hand
    
        if lead_value < 100:
            same_suit_cards = [c for c in player_cards if Cards.get_suit(c) == lead_suit and Cards.card_value(c, self.trump_rank, self.trump_suit) < 100]
            required_cards = same_suit_cards
        else:
            main_cards = [c for c in player_cards if Cards.card_value(c, self.trump_rank, self.trump_suit) >= 100]
            required_cards = main_cards
    
        required_count = len(required_cards)
        
        if required_count >= lead_count:
            # 必须出 lead_count 张 required 类型牌
            actual_required = [c for c in cards if c in required_cards]
            if len(actual_required) < lead_count:
                return False, "需要出同样花色的牌！"
        else:
            # 必须把所有 required 类型牌都打出去
            for rc in required_cards:
                if rc not in cards:
                    return False, "手中还有必须出的花色！"
        
        return True, None
    
    
    def record_play(self, player: Player, cards: List[str], trump_rank: str, trump_suit: str) -> Tuple[Optional[str], Optional[str]]:
        """
        判断并记录玩家出牌，处理合法性和代表牌记录
        """
        expected = (self.starting_player_index + len(set(pn for pn, _, _ in self.play_sequence))) % 4
        if player.player_number != expected:
            return f"❌ 现在不是你出牌，请等待玩家 {expected} 出牌", None
    
        # 首出：直接判定牌型是否合法
        if self.is_first_play:
            valid, representative, celebrate = Cards.is_valid_combo(cards, trump_rank, trump_suit)
            if not valid:
                return "❌ 非法牌型！请重新出牌！", None
            else:
                self.valid_play_sequence.append((player.player_number, representative, player.team_id))
    
        else:
            # 非首出：必须跟花
            bo, msg = self.is_following_legally(player, cards)
            if not bo:
                return msg, None
            # 检查牌型本身是否合法（比如两张必须完全相同等）
            valid, representative, celebrate = Cards.is_valid_combo(cards, trump_rank, trump_suit)
            if valid:
                self.valid_play_sequence.append((player.player_number, representative, player.team_id))
        # 合理跟牌则加入记录
        for card in cards:
            self.play_sequence.append((player.player_number, card, player.team_id))
    
        return expected, celebrate
            
    def resolve(self) -> Tuple[int, str, int, int]:
        """
        结算当前一轮 Trick：
        - 确定赢家编号和牌
        - 记录胜利队伍 ID
        - 累加得分
        返回：(赢家编号, 最大牌, 队伍ID, 总得分)
        """
        # 获取首家代表牌的花色和数值
        lead_card = self.valid_play_sequence[0][1]
        lead_value = Cards.card_value(lead_card, self.trump_rank, self.trump_suit)
        lead_suit = Cards.get_suit(lead_card)
    
        # 定义调整后的比较值
        def adjust(card: str) -> int:
            val = Cards.card_value(card, self.trump_rank, self.trump_suit)
            if lead_value < 100 and Cards.get_suit(card) == lead_suit and val < 100:
                return val + 20
            return val
    
        # 找出最大牌对应的玩家、牌和队伍
        winner_number, winning_card, winning_team = max(
            self.valid_play_sequence,
            key=lambda x: adjust(x[1])
        )
    
        self.winning_player_number = winner_number
        self.winning_team_id = winning_team
    
        # 累加所有出牌的得分
        self.points = sum(
            5 if Cards.get_rank(card) == '5' else
            10 if Cards.get_rank(card) in ['10', 'K'] else 0
            for _, card, _ in self.play_sequence
        )
    
        return winner_number, winning_card, winning_team, self.points
        
    



