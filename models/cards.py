import random
from typing import List, Dict, Tuple, Optional
from collections import defaultdict


class Cards:
    # 定义扑克牌的点数顺序
    RANK_ORDER = ["2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K", "A"]
    
    # 定义所有合法主数
    RANK_TRUMP_ORDER = ["2", "4", "6", "7", "8", "9", "10", "J", "Q", "K", "A"]

    # 定义扑克牌的花色
    SUITS = ["♠", "♥", "♣", "♦"]

    # 定义大小王
    JOKERS = ["JOKER1", "JOKER2"]

    # 定义每个花色对应的颜色
    SUIT_COLOR = {
        "♠": "black",
        "♣": "black",  # 黑色花色
        "♥": "red",
        "♦": "red",  # 红色花色
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
        if card[:-1] == "10":
            return "10"
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
            return ""
        return card[-1]

    @staticmethod
    def sort_hand(hand: List[str], rank_input: str, suit_input: str) -> List[str]:
        def trump_card_weights(x):
            """
            主数花色要求相连, 将输入值 x 转换，使得序列 [0.001, 0.01, 0.1, 1] 变换后按大小排序为 [0.001, 0.1, 0.01, 1]
            """

            if x == 0.001:
                return 0.001  # 保持最小
            elif x == 0.01:
                return 0.1  # 变大，成为第三位
            elif x == 0.1:
                return 0.01  # 变小，成为第二位
            elif x == 1:
                return 1  # 保持最大
            else:
                return x  # 其他值保持不变

        # 定义花色权重
        suit_weights = {}

        if suit_input == "♠":
            suit_weights = {"♥": 0.001, "♣": 0.01, "♦": 0.1, "♠": 1}
        elif suit_input == "♥":
            suit_weights = {"♠": 0.001, "♦": 0.01, "♣": 0.1, "♥": 1}
        elif suit_input == "♣":
            suit_weights = {"♥": 0.001, "♠": 0.01, "♦": 0.1, "♣": 1}
        else:  # ♦
            suit_weights = {"♠": 0.001, "♥": 0.01, "♣": 0.1, "♦": 1}

        def get_sort_value(card):
            card_val = Cards.card_value(card, rank_input, suit_input)
            if card_val < 100:  # trump_suit always > 100
                card_val = card_val * suit_weights[Cards.get_suit(card)]
            if Cards.get_rank(card) == rank_input:
                card_val = card_val + trump_card_weights(
                    suit_weights[Cards.get_suit(card)]
                )
            return card_val

        # 使用自定义排序函数
        return sorted(hand, key=get_sort_value)

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

        if rank == "JOKER1":
            return 400
        elif rank == "JOKER2":
            return 450
        elif rank in ["J", "Q", "K", "A"]:
            rank_value = {"J": 11, "Q": 12, "K": 13, "A": 14}
            return rank_value[rank]
        else:
            return int(rank)

    @staticmethod
    def card_value(card: str, trump_rank: str, trump_suit: str) -> int:
        # 为不同大小的牌赋分，牌越大分值越大

        trump_color = Cards.SUIT_COLOR[trump_suit]
        same_color_suits = [
            s
            for s, color in Cards.SUIT_COLOR.items()
            if color == Cards.SUIT_COLOR[trump_suit]
        ]

        advisor = f"3{trump_suit}"
        deputy_suit = [s for s in same_color_suits if s != trump_suit][0]
        deputy_advisor = f"3{deputy_suit}"

        card_suit = Cards.get_suit(card)
        card_rank = Cards.get_rank(card)
        card_value = Cards.card_rank_value(card)

        if card == "5♥":
            card_value = 500
        elif card == advisor:
            card_value = 350
        elif card == deputy_advisor:
            card_value = 300
        elif card_rank == trump_rank and card_suit == trump_suit:
            card_value += 250
        elif card_rank == trump_rank:
            card_value += 200
        elif card_suit == trump_suit:
            card_value += 100
        return card_value

    @staticmethod
    def is_valid_combo(
        cards: List[str], trump_rank: str, trump_suit: str
    ) -> Tuple[bool, Optional[str], Optional[str]]:
        ranks = [Cards.get_rank(c) for c in cards]
        suits = [Cards.get_suit(c) for c in cards]
        colors = [Cards.SUIT_COLOR.get(s, "") for s in suits]
        trump_color = Cards.SUIT_COLOR[trump_suit]
        i_trump = Cards.RANK_ORDER.index(trump_rank)
        
        same_color = len(set(colors)) == 1
        same_suit = len(set(suits)) == 1

        advisor = f"3{trump_suit}"
        deputy_suit = next(
            s
            for s, c in Cards.SUIT_COLOR.items()
            if c == trump_color and s != trump_suit
        )
        deputy_advisor = f"3{deputy_suit}"

        sorted_ranks = sorted(ranks)
        sorted_cards = Cards.sort_hand(cards, trump_rank, trump_suit)
        
        counts = {r: ranks.count(r) for r in set(ranks)}

        if len(cards) == 1:
            return True, cards[0], None

        elif len(cards) == 2:
            return (True, cards[0], None) if cards[0] == cards[1] else (False, None, None)

        elif len(cards) == 3:
            # 三张 Joker
            if all(r in Cards.JOKERS for r in cards):
                return True, cards[0], "KING!"

            # 三张主数，颜色相同
            if all(r == trump_rank for r in ranks) and same_color:
                return True, sorted_cards[2], "KING!"

            # 三张 advisor，颜色相同
            if all(c in [advisor, deputy_advisor] for c in cards):
                return True, cards[0], "KING!"

            # 特殊组合，且要求三张牌同花色
            if same_suit:
                if trump_rank not in ["K", "A"]:
                    if sorted_ranks in [["A", "K", "K"], ["A", "A", "K"]]:
                        return True, cards[0], "siu!!!"
                elif trump_rank == "K":
                    if sorted_ranks in [["A", "Q", "Q"], ["A", "A", "Q"]]:
                        return True, cards[0], "siu!!!"
                elif trump_rank == "A":
                    if sorted_ranks in [["K", "Q", "Q"], ["K", "K", "Q"]]:
                        return True, cards[0], "siu!!!"

        if len(cards) == 4:
            # 四张 Joker
            if all(r in Cards.JOKERS for r in cards):
                return True, cards[0], "KING!"

            # 四张主数，颜色相同
            if all(r == trump_rank for r in ranks) and same_color:
                return True, cards[0], "KING!"

            # 四张 advisor，颜色相同
            if all(c in [advisor, deputy_advisor] for c in cards):
                return True, cards[0], "KING!"

            # 四张同花色，必须连号（拖拉机）
            if same_suit and all(x not in cards for x in ["JOKER1", "JOKER2", "5♥"]) and trump_rank not in ranks:
                # 1) 两种点数各两张
                if len(counts) == 2 and all(v == 2 for v in counts.values()):
                    # 按照 RANK_ORDER 排序唯一点数
                    unique = sorted(counts.keys(),
                                    key=lambda r: Cards.RANK_ORDER.index(r))
                    i0, i1 = (Cards.RANK_ORDER.index(r) for r in unique)
                    if colors[0] != trump_color:                        
                        # 紧邻
                        if i1 == i0 + 1:
                            return True, cards[0], "tractor!"
                        # 隔一个主数
                        if i1 == i0 + 2 and i0 + 1 == i_trump:
                            return True, cards[0], "tractor!"
                    else: # 若和主花色相同，需隔一个参谋判定合法
                        if "3" not in ranks:
                            if i1 == i0 + 1:
                                return True, cards[0], "tractor!"
                            # 隔一个主数
                            if i1 == i0 + 2 and i0 + 1 == i_trump:
                                return True, cards[0], "tractor!"
                            if trump_rank != "4":
                                if i0 == 2 and i1 == 4:
                                    return True, cards[0], "tractor!"
                            else:
                                if i0 == 2 and i1 == 5:
                                    return True, cards[0], "tractor!"
                        

        elif len(cards) == 6:
            unique_ranks = sorted(counts.keys(), key=lambda r: Cards.RANK_ORDER.index(r))
            idxs = [Cards.RANK_ORDER.index(r) for r in unique_ranks]

            # 六张同花色三对拖拉机（允许隔一个主数）
            # 1) 同一花色，且不含大小王和 5♥
            if same_suit and all(c not in Cards.JOKERS and c != "5♥" for c in cards):
                # 2) 不含主数
                if trump_rank not in ranks:
                    # 3) 恰好三种点数，每种正好两张
                    if len(counts) == 3 and all(v == 2 for v in counts.values()):
                        # 4) 按大小排序后的唯一点数
                        # 5) 检查是否是连续三对，或中间隔一个主数
                        cond_adjacent = (idxs[1] - idxs[0] == 1 and
                                         idxs[2] - idxs[1] == 1)
                        cond_skip1 = (idxs[1] - idxs[0] == 1 and
                                      idxs[2] - idxs[1] == 2 and
                                      idxs[1] + 1 == i_trump)
                        cond_skip0 = (idxs[1] - idxs[0] == 2 and
                                      idxs[0] + 1 == i_trump and
                                      idxs[2] - idxs[1] == 1)
                        if cond_adjacent or cond_skip1 or cond_skip0:
                            # 代表牌这里暂且返回第一张，或按需改为最大对子的一张
                            return True, cards[0], "lulu!"
        
        elif len(cards) == 8:
            unique_ranks = sorted(counts.keys(), key=lambda r: Cards.RANK_ORDER.index(r))
            idxs = [Cards.RANK_ORDER.index(r) for r in unique_ranks]
            i_trump = Cards.RANK_ORDER.index(trump_rank)        
            if same_suit and all(c not in Cards.JOKERS and c != "5♥" for c in cards):
                # 2) 不含主数
                if trump_rank not in ranks:
                    # 3) 恰好四种点数，每种正好两张
                    if len(counts) == 4 and all(v == 2 for v in counts.values()):
                        # 4) 按大小排序后的唯一点数
                        # 5) 检查是否是连续三对，或中间隔一个主数
                        cond_adjacent = (idxs[1] - idxs[0] == 1 and
                                         idxs[2] - idxs[1] == 1 and
                                         idxs[3] - idxs[2] == 1)
                        cond_skip2 = (idxs[1] - idxs[0] == 1 and
                                      idxs[2] - idxs[1] == 1 and
                                      idxs[3] - idxs[2] == 2 and
                                      idxs[2] + 1 == i_trump)
                        cond_skip1 = (idxs[1] - idxs[0] == 1 and
                                      idxs[2] - idxs[1] == 2 and
                                      idxs[1] + 1 == i_trump and
                                      idxs[3] - idxs[2] == 1)
                        cond_skip0 = (idxs[1] - idxs[0] == 2 and
                                      idxs[0] + 1 == i_trump and
                                      idxs[2] - idxs[1] == 1 and
                                      idxs[3] - idxs[2] == 1)
                        if cond_adjacent or cond_skip2 or cond_skip1 or cond_skip0:
                            # 代表牌这里暂且返回第一张，或按需改为最大对子的一张
                            return True, cards[0], "dragon!!!"

        # 最后一行：所有情况都不符合时
        return False, None, None


# -------------------- 运行示例 --------------------
# if __name__ == "__main__":
#     # 获取用户输入的主数和主花色
#     rank_input = input("choose the prime number: ")
#     suit_input = input("choose the prime suit: ")

#     # 调用发牌并排序函数
#     hidden, players = Cards.deal_and_sort(rank_input, suit_input)

#     # 输出最初抽出的 8 张牌
#     print("最初抽出的 8 张牌：", hidden)

#     # 输出每个玩家的排序后手牌
#     for i in range(4):
#         print(f"\n玩家 {i} 的排序后手牌（共 {len(players[i])} 张）：")
#         print(players[i])
