"""Optional audit: verify saved coin flips, boards, scores and pairings."""

import argparse
from collections import Counter
import json
from pathlib import Path
import random

from Action import Action
from GameState import GameState
from main import _derived_seed, standings_for


def verify(results):
    if results.get("rules") != "simultaneous-coin-v1":
        raise ValueError("this log is not a simultaneous-coin-v1 tournament")
    names = [record["name"] for record in results["standings"]]
    if len(names) < 2 or len(names) != len(set(names)):
        raise ValueError("invalid participant list")
    paired_rounds = results["paired_rounds"]
    games = results["games"]
    if type(paired_rounds) is not int or paired_rounds <= 0 or len(games) != len(names) * (len(names) - 1) * paired_rounds:
        raise ValueError("wrong number of paired games")

    schedules = Counter()
    for game in games:
        first, second = game["first"], game["second"]
        index = game["pair_index"]
        if (first not in names or second not in names or first == second or
                type(index) is not int or not 0 <= index < paired_rounds):
            raise ValueError("invalid pairing")
        schedules[tuple(sorted((first, second))) + (index, first)] += 1
        state = GameState()
        coin_seed = int(_derived_seed(results["tournament_seed"],
                                      tuple(sorted((first, second))), index, "referee"), 16)
        rng = random.Random(coin_seed)
        for logged in game["rounds"]:
            if state.winner() != 0:
                raise ValueError("recorded moves after the game ended")
            o, x = logged["choices"]["O"], logged["choices"]["X"]
            try:
                coin = state.resolve_round(Action(o), Action(x), rng)
            except ValueError as error:
                raise ValueError("invalid logged round") from error
            expected = "O" if coin == 1 else "X" if coin == 2 else None
            if (logged["number"] != state.round_number or logged["coin_winner"] != expected
                    or logged["board"] != state.pieces):
                raise ValueError("board or referee coin does not match the logged choices")
        if game["round_count"] != state.round_number:
            raise ValueError("wrong round count")
        if game["reason"] in ("forfeit", "double_forfeit"):
            forfeits = game["forfeits"]
            expected_count = 1 if game["reason"] == "forfeit" else 2
            if (state.winner() != 0 or len(forfeits) != expected_count or
                    set(forfeits) != set(game["errors"]) or
                    not set(forfeits).issubset({first, second}) or
                    game["winner"] != (second if forfeits == [first] else
                                      first if forfeits == [second] else None)):
                raise ValueError("invalid forfeit record")
        elif (state.winner() == 0 or game["forfeits"] or
              game["reason"] != state.result_reason or
              game["winner"] != ({1: first, 2: second}.get(state.winner()))):
            raise ValueError("incorrect winner, draw or ending reason")

    from itertools import combinations
    for first, second in combinations(sorted(names), 2):
        for index in range(paired_rounds):
            if (schedules[(first, second, index, first)] != 1 or
                    schedules[(first, second, index, second)] != 1):
                raise ValueError("missing or duplicated seat-swapped game")

    quality = {record["name"]: record["quality"] for record in results["standings"]}
    if all(score is None for score in quality.values()):
        quality = None
    computed = standings_for(names, games, paired_rounds, quality)
    if computed != results["standings"]:
        raise ValueError("standings do not match the recorded games and quality scores")
    return len(games)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("results", type=Path, help="JSON file saved by main.py")
    args = parser.parse_args()
    try:
        count = verify(json.loads(args.results.read_text(encoding="utf-8")))
    except (OSError, ValueError, KeyError, TypeError) as error:
        parser.error(str(error))
    print(f"Verified {count} games: pairings, referee coins, boards and standings match.")


if __name__ == "__main__":
    main()
