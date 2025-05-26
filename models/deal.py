import random
from dataclasses import dataclass, field
from collections import deque
from typing import List, Optional, Tuple, Dict
from .team import Team
from .enums import Rank

from .trick import Trick
from .player import Player
from .cards import Cards

# 未来：创建一个新的类 Trick_slice，只记录 trick 中的重要信息放到 tricks 中

@dataclass
class Deal:
    """一局完整的发牌与25轮出牌(25 tricks)，包含局编号"""
    deal_number: int                         # 第几局（由 Game 控制）
    dealer: Player                           # 坐庄玩家
    dealer_team: Team                        # 庄队
    challenger_team: Team                    # 挑战队
    trump_rank: Rank                         # 主数
    trump_suit: str                          # 主花色（例如 '♠'）
    tricks: List[Trick] = field(default_factory=list)  # 每轮 trick 记录
    final_cards: List[str] = field(default_factory=list) #每轮底牌
    hidden_cards: List[str] = field(default_factory=list) #每轮藏牌

    def deal_to_players(self, suit, players: List["Player"], dealer: "Player", dealer_team: "Team") -> Dict[int, List[str]]:
        """
        发牌并排序，每位玩家手牌写入 player.hand，同时返回排序后的手牌结构。
        """
        self.trump_rank = dealer_team.trump_rank
        self.trump_suit = suit
        
        deck = Cards.create_deck()
        random.shuffle(deck)
    
        self.final_cards = deck[:8]
        remaining = deque(deck[8:])
    
        for p in players:
            p.hand.clear()
    
        for i, card in enumerate(remaining):
            players[i % 4].hand.append(card)
    
        dealer.hand.extend(self.final_cards)
    
        for idx, p in enumerate(players):
            p.hand = Cards.sort_hand(p.hand, self.trump_rank, self.trump_suit)
    

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

    def final_points(self) -> Tuple[int, int]:
        """
        结算本轮，加上藏牌分数，返回双方最后总分
        """
        hidden = self.hidden_cards
        added_points = sum(
            5 if Cards.get_rank(card) == '5' else
            10 if Cards.get_rank(card) in ['10', 'K'] else 0
            for card in hidden
        )
        scores = self.get_team_points()
        dealer_score = scores[self.dealer_team.team_id]
        challenger_score = scores[self.challenger_team.team_id]
        if self.tricks[-1].winning_team_id == self.challenger_team.team_id:
            challenger_score = challenger_score + 2 * added_points
            
        return dealer_score, challenger_score

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

        return dealer_score, challenger_score, next_dealer, next_dealer.trump_rank