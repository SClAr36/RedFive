import pytest
from .cards import Cards  # Assuming the code is in a file named cards.py


def test_get_rank():
    # Test regular cards
    assert Cards.get_rank("5♠") == "5"
    assert Cards.get_rank("A♥") == "A"
    assert Cards.get_rank("10♦") == "10"
    assert Cards.get_rank("J♣") == "J"

    # Test jokers
    assert Cards.get_rank("JOKER1") == "JOKER1"
    assert Cards.get_rank("JOKER2") == "JOKER2"


def test_get_suit():
    # Test regular cards
    assert Cards.get_suit("5♠") == "♠"
    assert Cards.get_suit("A♥") == "♥"
    assert Cards.get_suit("10♦") == "♦"
    assert Cards.get_suit("J♣") == "♣"

    # Test jokers
    assert Cards.get_suit("JOKER1") == ""
    assert Cards.get_suit("JOKER2") == ""


def test_sort_hand():
    # Test sorting with different trump rank and suit
    hand = [
        "A♣",
        "K♣",
        "Q♣",
        "J♣",
        "10♣",
        "9♣",
        "8♣",
        "7♣",
        "6♣",
        "5♣",
        "4♣",
        "3♣",
        "2♣",
        "A♦",
        "K♦",
        "Q♦",
        "J♦",
        "10♦",
        "9♦",
        "8♦",
        "7♦",
        "6♦",
        "5♦",
        "4♦",
        "3♦",
        "2♦",
        "A♥",
        "K♥",
        "Q♥",
        "J♥",
        "10♥",
        "9♥",
        "8♥",
        "7♥",
        "6♥",
        "5♥",
        "4♥",
        "3♥",
        "2♥",
        "A♠",
        "K♠",
        "Q♠",
        "J♠",
        "10♠",
        "9♠",
        "8♠",
        "7♠",
        "6♠",
        "5♠",
        "4♠",
        "3♠",
        "2♠",
        "JOKER2",
        "JOKER1",
    ]  # []

    # Test with 2 as trump rank and ♠ as trump suit
    sorted_hand = Cards.sort_hand(hand, "2", "♠")
    print(f"trump_rank=2, trump_suit=♠, {sorted_hand=}")
    # Expected order: regular hand by suit, special rank, special rank+suit, special 3s, jokers, 5♥
    assert sorted_hand[-1] == "5♥"  # 5♥ should be last
    assert "JOKER2" in sorted_hand[-2:]  # Joker should be near the end
    assert "JOKER1" in sorted_hand[-3:]  # Small joker should before the big joker

    sorted_hand = Cards.sort_hand(hand, "4", "♥")
    print(f"trump_rank=4, trump_suit=♥, {sorted_hand=}")

    sorted_hand = Cards.sort_hand(hand, "6", "♦")
    print(f"trump_rank=6, trump_suit=♦, {sorted_hand=}")

    sorted_hand = Cards.sort_hand(hand, "A", "♣")
    print(f"trump_rank=A, trump_suit=♣, {sorted_hand=}")

    hand = ["2♠", "2♣", "2♥", "2♠", "2♦", "2♣", "2♦", "2♥"]
    sorted_hand = Cards.sort_hand(hand, "4", "♥")
    print(f"{hand=}, trump_rank=2, trump_suit=♣, {sorted_hand=}")

    sorted_hand = Cards.sort_hand(hand, "2", "♦")
    print(f"{hand=}, trump_rank=2, trump_suit=♣, {sorted_hand=}")

    sorted_hand = Cards.sort_hand(hand, "2", "♣")
    print(f"{hand=}, trump_rank=2, trump_suit=♣, {sorted_hand=}")

    sorted_hand = Cards.sort_hand(hand, "2", "♠")
    print(f"{hand=}, trump_rank=2, trump_suit=♠, {sorted_hand=}")


def test_create_deck():
    deck = Cards.create_deck()
    # Should have 2 full decks (52 cards each) plus 2 jokers each = 108 cards
    assert len(deck) == 108

    # Check if all ranks and suits are present
    for rank in Cards.RANK_ORDER:
        for suit in Cards.SUITS:
            card = rank + suit
            # Each card should appear twice (2 decks)
            assert deck.count(card) == 2
    print(f"{deck=}")
    print(f"{Cards.sort_hand(deck, "2", "♠")=}")
    print(f"{Cards.sort_hand(deck, "4", "♥")=}")
    print(f"{Cards.sort_hand(deck, "6", "♦")=}")
    print(f"{Cards.sort_hand(deck, "A", "♣")=}")

    # Check jokers
    assert deck.count("JOKER1") == 2
    assert deck.count("JOKER2") == 2


def test_deal_and_sort(monkeypatch):
    # Mock shuffle to ensure deterministic behavior
    def mock_shuffle(x):
        pass

    import random

    monkeypatch.setattr(random, "shuffle", mock_shuffle)

    hidden, players = Cards.deal_and_sort("5", "♠")

    # Check if hidden has 8 cards
    assert len(hidden) == 8

    # Check if each player has correct number of cards
    assert len(players[0]) == 33  # Player 0 gets hidden cards too
    assert len(players[1]) == 25
    assert len(players[2]) == 25
    assert len(players[3]) == 25

    # Total cards should be 108
    total_cards = len(hidden) + sum(len(hand) for hand in players.values())
    assert total_cards == 108


def test_card_rank_value():
    # Test numeric cards
    assert Cards.card_rank_value("2♠") == 2
    assert Cards.card_rank_value("10♥") == 10

    # Test face cards
    assert Cards.card_rank_value("J♣") == 11
    assert Cards.card_rank_value("Q♦") == 12
    assert Cards.card_rank_value("K♠") == 13
    assert Cards.card_rank_value("A♥") == 14

    # Test jokers
    assert Cards.card_rank_value("JOKER1") == 400
    assert Cards.card_rank_value("JOKER2") == 450


def test_card_value():
    # Test with 5 as trump rank and ♠ as trump suit
    trump_rank = "5"
    trump_suit = "♠"

    # Test 5♥ (special card)
    assert Cards.card_value("5♥", trump_rank, trump_suit) == 500

    # Test advisor (3♠)
    assert Cards.card_value("3♠", trump_rank, trump_suit) == 350

    # Test deputy advisor (3♣ - same color as ♠)
    assert Cards.card_value("3♣", trump_rank, trump_suit) == 300

    # Test trump rank + suit
    assert Cards.card_value("5♠", trump_rank, trump_suit) == 255  # 5 + 250

    # Test trump rank only
    assert Cards.card_value("5♥", trump_rank, trump_suit) == 500  # Special case
    assert Cards.card_value("5♦", trump_rank, trump_suit) == 205  # 5 + 200

    # Test trump suit only
    assert Cards.card_value("A♠", trump_rank, trump_suit) == 114  # 14 + 100

    # Test regular card
    assert Cards.card_value("A♥", trump_rank, trump_suit) == 14


def test_is_valid_combo():
    trump_rank = "5"
    trump_suit = "♠"

    # Test single card
    assert Cards.is_valid_combo(["A♥"], trump_rank, trump_suit) == (True, "A♥")

    # Test pair (same cards)
    assert Cards.is_valid_combo(["A♥", "A♥"], trump_rank, trump_suit) == (True, "A♥")

    # Test invalid pair (different cards)
    assert Cards.is_valid_combo(["A♥", "K♥"], trump_rank, trump_suit) == (False, None)

    # Test three jokers
    assert Cards.is_valid_combo(
        ["JOKER1", "JOKER1", "JOKER2"], trump_rank, trump_suit
    ) == (True, "JOKER1")

    # Test three trump rank cards with same color
    assert Cards.is_valid_combo(["5♠", "5♠", "5♣"], trump_rank, trump_suit) == (
        True,
        "5♠",
    )

    # Test three advisors with same color
    assert Cards.is_valid_combo(["3♠", "3♠", "3♣"], trump_rank, trump_suit) == (
        True,
        "3♠",
    )

    # Test special combinations (A-K-K with same suit)
    assert Cards.is_valid_combo(["A♥", "K♥", "K♥"], trump_rank, trump_suit) == (
        True,
        "A♥",
    )

    # Test invalid three-card combination
    assert Cards.is_valid_combo(["A♥", "K♥", "Q♦"], trump_rank, trump_suit) == (
        False,
        None,
    )

    # Test empty list
    assert Cards.is_valid_combo([], trump_rank, trump_suit) == (False, None)


def test_edge_cases():
    # Test sorting with empty hand
    assert Cards.sort_hand([], "5", "♠") == []

    # Test card value with jokers
    assert Cards.card_value("JOKER1", "5", "♠") == 400
    assert Cards.card_value("JOKER2", "5", "♠") == 450

    # Test is_valid_combo with four cards
    trump_rank = "5"
    trump_suit = "♠"

    # Four jokers
    assert Cards.is_valid_combo(
        ["JOKER1", "JOKER1", "JOKER2", "JOKER2"], trump_rank, trump_suit
    ) == (True, "JOKER1")

    # Four trump cards with same color
    assert Cards.is_valid_combo(["5♠", "5♠", "5♣", "5♣"], trump_rank, trump_suit) == (
        True,
        "5♠",
    )

    # Four advisors
    assert Cards.is_valid_combo(["3♠", "3♠", "3♣", "3♣"], trump_rank, trump_suit) == (
        True,
        "3♠",
    )

    # Invalid four-card combination
    assert Cards.is_valid_combo(["A♥", "K♥", "Q♥", "J♥"], trump_rank, trump_suit) == (
        False,
        None,
    )


@pytest.mark.parametrize(
    "card,trump_rank,trump_suit,expected",
    [
        ("A♥", "K", "♠", 14),  # Regular card
        ("K♠", "K", "♠", 113),  # Trump suit
        ("K♥", "K", "♠", 213),  # Trump rank
        ("K♠", "K", "♠", 113),  # Trump rank + suit
        ("3♠", "K", "♠", 350),  # Advisor
        ("3♣", "K", "♠", 300),  # Deputy advisor
        ("5♥", "K", "♠", 500),  # Special 5♥
    ],
)
def test_parametrized_card_values(card, trump_rank, trump_suit, expected):
    assert Cards.card_value(card, trump_rank, trump_suit) == expected, (
        f"Failed for {card} with trump {trump_rank}{trump_suit}"
    )
