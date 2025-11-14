# tests/test_play_round.py
# We drive play_round() deterministically by monkeypatching:
#   - input() for bets/choices
#   - Deck with a FakeDeck that yields a known dealing order

from blackjack import Card, play_round

class FakeDeck:
    """Deals cards from a predefined list, popping from the end to match .deal()."""
    def __init__(self, sequence):
        # store so that last elements are dealt first (pop())
        self.cards = list(sequence)

    def shuffle(self):
        pass

    def deal(self):
        return self.cards.pop()

def _monkeypatch_deck(module, fake_deck):
    module.Deck = lambda: fake_deck


def test_player_hits_and_busts(monkeypatch):
    import blackjack as bj
    # Player will hit and bust
    seq = [
        Card("Hearts", "10"),   # player
        Card("Clubs", "9"),     # dealer
        Card("Spades", "8"),    # player -> 18
        Card("Diamonds", "7"),  # dealer
        Card("Hearts", "9"),    # next hit -> 27 bust
    ]
    fake = FakeDeck(sequence=seq)
    _monkeypatch_deck(bj, fake)

    inputs = iter(["100", "h"])  # bet=100, then choose hit -> bust
    monkeypatch.setattr("builtins.input", lambda *args, **kwargs: next(inputs))

    money_after = play_round(1000)
    assert money_after == 900

def test_player_stands_dealer_busts(monkeypatch):
    import blackjack as bj
    # Player stands on 20; dealer draws to bust
    seq = [
        Card("Hearts", "10"),   # player -> first
        Card("Clubs", "6"),     # dealer
        Card("Spades", "Q"),    # player -> 20
        Card("Diamonds", "9"),  # dealer -> 15, must hit
        Card("Spades", "8"),    # dealer hit -> 23 bust
    ]
    fake = FakeDeck(sequence=seq)
    _monkeypatch_deck(bj, fake)

    inputs = iter(["150", "s"])  # bet=150, stand
    monkeypatch.setattr("builtins.input", lambda *args, **kwargs: next(inputs))

    money_after = play_round(1000)
    assert money_after == 1150
