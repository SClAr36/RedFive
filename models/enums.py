# 枚举类：定义扑克牌的点数顺序

from enum import Enum

class Rank(Enum):
    """扑克牌点数枚举，从 2 到 A"""
    TWO = 2
    THREE = 3
    FOUR = 4
    FIVE = 5
    SIX = 6
    SEVEN = 7
    EIGHT = 8
    NINE = 9
    TEN = 10
    J = 11
    Q = 12
    K = 13
    A = 14
    
RANK_STR_TO_ENUM = {
    "2": Rank.TWO,
    "3": Rank.THREE,
    "4": Rank.FOUR,
    "5": Rank.FIVE,
    "6": Rank.SIX,
    "7": Rank.SEVEN,
    "8": Rank.EIGHT,
    "9": Rank.NINE,
    "10": Rank.TEN,
    "J": Rank.J,
    "Q": Rank.Q,
    "K": Rank.K,
    "A": Rank.A,
}

