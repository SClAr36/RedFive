def card_value(card: str, rank_input: str, suit_input: str) -> int:
    """返回一张牌的价值，用于比较大小"""
    if card in JOKERS:
        return 100 + JOKERS.index(card)  # JOKER2 > JOKER1
    rank = get_rank(card)
    suit = get_suit(card)
    value = RANK_ORDER.index(rank)
    # 加权处理特殊牌
    if rank == rank_input and suit == suit_input:
        value += 40
    elif rank == rank_input:
        value += 30
    elif rank == '3' and SUIT_COLOR[suit] == SUIT_COLOR[suit_input]:
        value += 20
    elif suit == suit_input:
        value += 10
    return value

def compare_hands(hand1: List[str], hand2: List[str], rank_input: str, suit_input: str) -> int:
    """比较两个手牌，返回胜负"""
    h1 = sort_hand(hand1, rank_input, suit_input)
    h2 = sort_hand(hand2, rank_input, suit_input)
    for c1, c2 in zip(h1, h2):
        v1 = card_value(c1, rank_input, suit_input)
        v2 = card_value(c2, rank_input, suit_input)
        if v1 > v2:
            return 1
        elif v1 < v2:
            return -1
    # 如果到这里，说明都相同或一方手牌较短但前面都一样
    if len(h1) > len(h2):
        return 1
    elif len(h1) < len(h2):
        return -1
    return 0  # 平局
