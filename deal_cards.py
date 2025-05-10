import random
from typing import List, Tuple
from collections import defaultdict

# -------------------- 配置 --------------------

RANK_ORDER = ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A']
SUITS = ['♠', '♥', '♣', '♦']
JOKERS = ['JOKER1', 'JOKER2']
SUIT_COLOR = {
    '♠': 'black', '♣': 'black',
    '♥': 'red', '♦': 'red'
}

# -------------------- 工具函数 --------------------

def create_deck() -> List[str]:
    single_deck = [rank + suit for suit in SUITS for rank in RANK_ORDER]
    single_deck += JOKERS  # 一副牌加大小王
    return single_deck * 2  # 两副

def get_rank(card: str) -> str:
    if card in JOKERS:
        return card
    if card[:-1] == '10':
        return '10'
    return card[:-1]

def get_suit(card: str) -> str:
    if card in JOKERS:
        return ''
    return card[-1]

def sort_hand(cards: List[str], rank_input: str, suit_input: str) -> List[str]:
    buckets = defaultdict(list)
    special_rank = []
    special_rank_same_suit = []
    special_3_same_color = []
    special_3_same_suit = []
    jokers = []
    red_heart_5 = []

    for card in cards:
        if card in JOKERS:
            jokers.append(card)
        elif card == '5♥':
            red_heart_5.append(card)
        else:
            rank = get_rank(card)
            suit = get_suit(card)

            if rank == rank_input and suit == suit_input:
                special_rank_same_suit.append(card)
            elif rank == rank_input:
                special_rank.append(card)
            elif rank == '3' and SUIT_COLOR[suit] == SUIT_COLOR[suit_input]:
                if suit == suit_input:
                    special_3_same_suit.append(card)
                else:
                    special_3_same_color.append(card)
            else:
                buckets[suit].append(card)

    for suit in SUITS:
        buckets[suit].sort(key=lambda x: RANK_ORDER.index(get_rank(x)))

    suit_order = [s for s in SUITS if s != suit_input] + [suit_input]
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

# def sort_hand_new(cards: List[str], rank_input: str, suit_input: str) -> Tuple[List[str], List[int]]:
#     index_map = {card: [] for card in cards}
#     for i, card in enumerate(cards):
#         index_map[card].append(i)

#     buckets = defaultdict(list)
#     special_rank = []
#     special_rank_same_suit = []
#     special_3_same_color = []
#     special_3_same_suit = []
#     jokers = []
#     red_heart_5 = []

#     for card in cards:
#         if card in JOKERS:
#             jokers.append(card)
#         elif card == '5♥':
#             red_heart_5.append(card)
#         else:
#             rank = get_rank(card)
#             suit = get_suit(card)

#             if rank == rank_input and suit == suit_input:
#                 special_rank_same_suit.append(card)
#             elif rank == rank_input:
#                 special_rank.append(card)
#             elif rank == '3' and SUIT_COLOR[suit] == SUIT_COLOR[suit_input]:
#                 if suit == suit_input:
#                     special_3_same_suit.append(card)
#                 else:
#                     special_3_same_color.append(card)
#             else:
#                 buckets[suit].append(card)

#     for suit in SUITS:
#         buckets[suit].sort(key=lambda x: RANK_ORDER.index(get_rank(x)))

#     suit_order = [s for s in SUITS if s != suit_input] + [suit_input]
#     result = []
#     for s in suit_order:
#         result.extend(buckets[s])

#     result += special_rank
#     result += special_rank_same_suit
#     result += special_3_same_color
#     result += special_3_same_suit
#     result += jokers
#     result += red_heart_5

#     # 查找排序后每张牌在原始 cards 中的索引
#     index_order = []
#     for card in result:
#         index_order.append(index_map[card].pop(0))

#     return result, index_order


# -------------------- 主程序 --------------------


def deal_and_sort(rank_input: str, suit_input: str):
    deck = create_deck()
    random.shuffle(deck)

    # 抽出8张
    hidden = deck[:8]
    remaining = deck[8:]

    players = defaultdict(list)

    # 发100张
    for i in range(100):
        players[i % 4].append(remaining[i])

    # 加上8张给玩家3
    players[3].extend(hidden)

    # 排序
    sorted_players = {}
    for i in range(4):
        sorted_players[i] = sort_hand(players[i], rank_input, suit_input)

    return hidden, sorted_players

# -------------------- 运行示例 --------------------

if __name__ == '__main__':
    rank_input = input("choose the prime number: ")
    suit_input = input("choose the prime suit: ")
    hidden, players = deal_and_sort(rank_input, suit_input)

    print("最初抽出的 8 张牌：", hidden)
    for i in range(4):
        print(f"\n玩家 {i} 的排序后手牌（共 {len(players[i])} 张）：")
        print(players[i])
