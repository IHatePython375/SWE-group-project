# tests/test_deck.py
from blackjack import Deck, Card

def test_deck_has_52_unique_cards():
    d = Deck()
    assert len(d.cards) == 52
    seen = {(c.suit, c.rank) for c in d.cards}
    assert len(seen) == 52

def test_deal_reduces_length_and_returns_card():
    d = Deck()
    before = len(d.cards)
    c = d.deal()
    assert isinstance(c, Card)
    assert len(d.cards) == before - 1

def test_shuffle_changes_order_most_of_the_time():
    d1 = Deck()
    d2 = Deck()
    # Shuffle only one of them
    d2.shuffle()
    # Extremely unlikely to be identical after shuffle
    orders_equal = [(c1.suit, c1.rank) for c1 in d1.cards] == [(c2.suit, c2.rank) for c2 in d2.cards]
    assert not orders_equal
