import random
from typing import List, Dict
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

        players[3].extend(hidden)

        sorted_players = {}
        for i in range(4):
            sorted_players[i] = Cards.sort_hand(players[i], rank_input, suit_input)

        return hidden, sorted_players


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
