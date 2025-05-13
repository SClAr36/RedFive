import random
from typing import List, Dict, Tuple, Optional
from collections import defaultdict


class Cards:
    # 定义扑克牌的点数顺序
    RANK_ORDER = ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A']

    # 定义扑克牌的花色
    SUITS = ['♠', '♥', '♣', '♦']

    # 定义大小王
    JOKERS = ['JOKER1', 'JOKER2']

    # 定义每个花色对应的颜色
    SUIT_COLOR = {
        '♠': 'black', '♣': 'black',  # 黑色花色
        '♥': 'red', '♦': 'red'  # 红色花色
    }

    @staticmethod
    def get_rank(card: str) -> str:
        """
        获取一张牌的点数部分。
        参数：
            card: 牌的字符串表示（例如 '5♠', 'A♥'）。
        返回：
            牌的点数部分（例如 '5', 'A'）。
        """
        if card in Cards.JOKERS:
            return card
        if card[:-1] == '10':
            return '10'
        return card[:-1]

    @staticmethod
    def get_suit(card: str) -> str:
        """
        获取一张牌的花色部分。
        参数：
            card: 牌的字符串表示（例如 '5♠', 'A♥'）。
        返回：
            牌的花色部分（例如 '♠', '♥'）。
        """
        if card in Cards.JOKERS:
            return ''
        return card[-1]

    @staticmethod
    def sort_hand(cards: List[str], rank_input: str, suit_input: str) -> List[str]:
        """
        对手牌进行排序，按特定规则。
        参数：
            cards: 需要排序的牌列表。
            rank_input: 用户指定的“主数”。
            suit_input: 用户指定的“主花色”。
        返回：
            排序后的牌列表。
        """
        buckets = defaultdict(list)
        special_rank = []
        special_rank_same_suit = []
        special_3_same_color = []
        special_3_same_suit = []
        jokers = []
        red_heart_5 = []

        for card in cards:
            if card in Cards.JOKERS:
                jokers.append(card)
            elif card == '5♥':
                red_heart_5.append(card)
            else:
                rank = Cards.get_rank(card)
                suit = Cards.get_suit(card)

                if rank == rank_input and suit == suit_input:
                    special_rank_same_suit.append(card)
                elif rank == rank_input:
                    special_rank.append(card)
                elif rank == '3' and Cards.SUIT_COLOR[suit] == Cards.SUIT_COLOR[suit_input]:
                    if suit == suit_input:
                        special_3_same_suit.append(card)
                    else:
                        special_3_same_color.append(card)
                else:
                    buckets[suit].append(card)

        for suit in Cards.SUITS:
            buckets[suit].sort(key=lambda x: Cards.RANK_ORDER.index(Cards.get_rank(x)))

        suit_order = [s for s in Cards.SUITS if s != suit_input] + [suit_input]

        result = []
        for s in suit_order:
            result.extend(buckets[s])

        result += special_rank
        result += special_rank_same_suit
        result += special_3_same_color
        result += special_3_same_suit
        result += jokers
        result += red_heart_5

        return result

    @staticmethod
    def create_deck() -> List[str]:
        """
        创建一副扑克牌（两副），包括大小王。
        返回：包含两副牌和大小王的列表。
        """
        single_deck = [rank + suit for suit in Cards.SUITS for rank in Cards.RANK_ORDER]
        single_deck += Cards.JOKERS
        return single_deck * 2

    @staticmethod
    def deal_and_sort(rank_input: str, suit_input: str) -> Dict[int, List[str]]:
        """
        发牌并排序，返回排序后的结果。
        参数：
            rank_input: 用户选择的主数。
            suit_input: 用户选择的主花色。
        返回：
            sorted_players: 每个玩家排序后的手牌。
        """
        deck = Cards.create_deck()
        random.shuffle(deck)

        hidden = deck[:8]
        remaining = deck[8:]

        players = defaultdict(list)

        for i in range(100):
            players[i % 4].append(remaining[i])

        players[0].extend(hidden)

        sorted_players = {}
        for i in range(4):
            sorted_players[i] = Cards.sort_hand(players[i], rank_input, suit_input)

        return hidden, sorted_players
    

    @staticmethod
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
    
    @staticmethod
    def card_value(card: str, trump_rank: str, trump_suit: str) -> int:
        # 为不同大小的牌赋分，牌越大分值越大

        trump_color = Cards.SUIT_COLOR[trump_suit] 
        same_color_suits = [s for s, color in Cards.SUIT_COLOR.items() if color == Cards.SUIT_COLOR[trump_suit]]
    
        advisor = f"3{trump_suit}"
        deputy_suit = [s for s in same_color_suits if s != trump_suit][0]
        deputy_advisor = f"3{deputy_suit}"
            
        card_suit = Cards.get_suit(card)
        card_rank = Cards.get_rank(card)
        card_value = Cards.card_rank_value(card)
        
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

    @staticmethod    
    def is_valid_combo(cards: List[str], trump_rank: str, trump_suit: str) -> Tuple[bool, Optional[str]]:
        ranks = [Cards.get_rank(c) for c in cards]
        suits = [Cards.get_suit(c) for c in cards]
        colors = [Cards.SUIT_COLOR.get(s, '') for s in suits]

        same_color = len(set(colors)) == 1
        same_suit = len(set(suits)) == 1

        advisor = f"3{trump_suit}"
        deputy_suit = next(s for s, c in Cards.SUIT_COLOR.items() if c == Cards.SUIT_COLOR[trump_suit] and s != trump_suit)
        deputy_advisor = f"3{deputy_suit}"

        sorted_ranks = Cards.sort_hand(ranks, trump_rank, trump_suit)
        
        if not cards:
            return False, None #非法牌型！请重新出牌！
    
        if len(cards) == 1:
            return True, cards[0]
    
        if len(cards) == 2:
            return (True, cards[0]) if cards[0] == cards[1] else (False, None)
    
        if len(cards) == 3:
            # 三张 Joker
            if all(r in Cards.JOKERS for r in cards):
                return True, cards[0]
    
            # 三张主数，颜色相同
            if all(r == trump_rank for r in ranks) and same_color:
                return True, cards[0]
    
            # 三张 advisor，颜色相同
            if all(c in [advisor, deputy_advisor] for c in cards):
                return True, cards[0]
    
            # 特殊组合，且要求三张牌同花色
            if same_suit:
                if trump_rank not in ['K', 'A']:
                    if sorted_ranks in [['K', 'K', 'A'], ['K', 'A', 'A']]:
                        return True, cards[0]
                elif trump_rank == 'K':
                    if sorted_ranks in [['Q', 'Q', 'A'], ['Q', 'A', 'A']]:
                        return True, cards[0]
                elif trump_rank == 'A':
                    if sorted_ranks in [['Q', 'Q', 'K'], ['Q', 'K', 'K']]:
                        return True, cards[0]
        
        if len(cards) == 4:
            # 四张 Joker
            if all(r in Cards.JOKERS for r in cards):
                return True, cards[0]
    
            # 四张主数，颜色相同
            if all(r == trump_rank for r in ranks) and same_color:
                return True, cards[0]
    
            # 四张 advisor，颜色相同
            if all(c in [advisor, deputy_advisor] for c in cards):
                return True, cards[0]
            
            # 四张同花色，必须连号（拖拉机）
            if same_suit:
                r1, r2, r3, r4 = sorted_ranks
                if not (r1 == r2 and r3 == r4):
                    return False, None  # 不是两对
            
                i1 = Cards.RANK_ORDER.index(r3)
                i3 = Cards.RANK_ORDER.index(r3)
                i_trump = Cards.RANK_ORDER.index(trump_rank)
            
                # 1. 紧邻合法
                if i3 == i1 + 1:
                    return True, cards[0]
            
                # 2. 中间隔了一个主数合法
                if i3 == i1 + 2 and i1 + 1 == i_trump:
                    return True, cards[0]

        return False, None



# -------------------- 运行示例 --------------------
if __name__ == '__main__':
    # 获取用户输入的主数和主花色
    rank_input = input("choose the prime number: ")
    suit_input = input("choose the prime suit: ")

    # 调用发牌并排序函数
    hidden, players = Cards.deal_and_sort(rank_input, suit_input)

    # 输出最初抽出的 8 张牌
    print("最初抽出的 8 张牌：", hidden)

    # 输出每个玩家的排序后手牌
    for i in range(4):
        print(f"\n玩家 {i} 的排序后手牌（共 {len(players[i])} 张）：")
        print(players[i])
