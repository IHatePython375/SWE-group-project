# tests/test_gamestatistics.py
import json
import os
from blackjack import Gamestatistics

def test_score_game_sorts_and_truncates(tmp_path, monkeypatch):
    # force the JSON file into a temp dir
    monkeypatch.chdir(tmp_path)
    gs = Gamestatistics()
    assert gs.scores == []

    # Add 12 entries; only top 10 by final_money should remain
    for i in range(12):
        gs.score_game(player_name=f"P{i}", final_money=1000 + i, rounds_completed=10)

    assert len(gs.scores) == 10
    # top should be highest final_money
    assert gs.scores[0]["final_money"] == 1000 + 11
    # file created
    assert os.path.exists("blackjack_scores.json")
    data = json.loads(open("blackjack_scores.json").read())
    assert len(data) == 10
    # profit computed relative to 1000
    assert data[0]["profit"] == 11
