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
    winining_player_number: Optional[int] = None  # 赢家编号
    points: int = 0
    
    
    def record_play(self, player: Player, cards: List[str]) -> Optional[str]:
        """
        记录一个玩家的出牌动作：
        - 若当前不是该玩家轮次，返回错误信息；
        - 若出牌顺序正确，将所有牌加入 play_sequence；
        - 返回 None 表示成功。
        """
        expected = (self.starting_player_index + len(set(pn for pn, _, _ in self.play_sequence))) % 4
        if player.player_number != expected:
            return f"❌ 现在不是你出牌，请等待玩家 {expected} 出牌"
    
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
            self.play_sequence, key=lambda x: card_value(x[1], self.trump_rank, self.trump_suit)
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
    
    
def card_rank_value(card: str) -> int:
    """
    给一张牌赋值：
    - 普通点数牌按 J=11, Q=12, K=13, A=14
    - JOKER1=400, JOKER2=450
    """
    rank = Cards.get_rank(card)

    if rank == 'JOKER1':
        return 400
    elif rank == 'JOKER2':
        return 450
    elif rank in ['J', 'Q', 'K', 'A']:
        rank_value = {'J': 11, 'Q': 12, 'K': 13, 'A': 14}
        return rank_value[rank]
    else:
        return int(rank)   

def card_value(card: str, trump_rank: str, trump_suit: str) -> int:
    # 为不同大小的牌赋分，牌越大分值越大
    
    SUIT_COLOR = {
        '♠': 'black', '♣': 'black',  # 黑色花色
        '♥': 'red', '♦': 'red'  # 红色花色
    }

    advisor = "3♣"
    deputy_advisor = "3♠"

        
    card_suit = Cards.get_suit(card)
    card_rank = Cards.get_rank(card)
    card_value = card_rank_value(card)
    
    if card == '5♥':
        card_value = 500
    elif card == advisor:
        card_value = 350
    elif card == deputy_advisor:
        card_value =  300
    elif card_rank == trump_rank and card_suit == trump_suit:
        card_value += 250
    elif card_rank == trump_rank:
        card_value += 200
    elif card_suit == trump_suit:
        card_value += 100
    return card_value



