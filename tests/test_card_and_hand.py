# tests/test_card_and_hand.py
import builtins

from blackjack import Card, Hand

def test_card_str_and_value_faces_and_ace():
    assert str(Card("Hearts", "J")) == "J of Hearts"
    assert Card("Clubs", "Q").value() == 10
    assert Card("Spades", "K").value() == 10
    assert Card("Diamonds", "A").value() == 11
    assert Card("Hearts", "7").value() == 7

def test_hand_value_no_aces():
    h = Hand()
    h.add_card(Card("Hearts", "10"))
    h.add_card(Card("Clubs", "9"))
    assert h.calculate_value() == 19

def test_hand_value_single_ace_softening():
    h = Hand()
    h.add_card(Card("Hearts", "A"))   # 11
    h.add_card(Card("Clubs", "9"))    # 9
    h.add_card(Card("Spades", "5"))   # would be 25 -> soft to 15
    assert h.calculate_value() == 15

def test_hand_value_multiple_aces_softening():
    h = Hand()
    # A + A + 9: 11 + 11 + 9 = 31 -> soften one Ace: 21
    h.add_card(Card("Hearts", "A"))
    h.add_card(Card("Clubs", "A"))
    h.add_card(Card("Spades", "9"))
    assert h.calculate_value() == 21
