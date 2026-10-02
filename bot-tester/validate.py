"""Check one bot's file, legal choices, and two complete sample games."""

import argparse
import math
from pathlib import Path

from GameState import GameState
from main import BOT_NAME, DEFAULT_TIMEOUT, play_game, request_move


def check_bot(path, timeout=DEFAULT_TIMEOUT):
    path = Path(path).resolve()
    if not path.is_file() or not BOT_NAME.fullmatch(path.name):
        raise ValueError("provide one .py bot file with a simple filename")

    sample_boards = (
        ("empty", [0] * 9, 0),
        ("in progress", [1, 2, 0, 0, 1, 2, 0, 0, 0], 2),
        ("one empty square", [1, 2, 1, 1, 2, 2, 2, 1, 0], 6),
    )
    for label, board, rounds in sample_boards:
        for player in (1, 2):
            state = GameState()
            state.pieces = board.copy()
            state.round_number = rounds
            move, error = request_move(path, state.view_for(player), timeout, bot_seed="4")
            if error is not None:
                raise ValueError(f"{label}, perspective {player}: {error}")
            from Action import Action
            if not state.view_for(player).valid_action(Action(move)):
                raise ValueError(f"{label}, perspective {player}: illegal choice {move}")

    samples = Path(__file__).resolve().parent / "bots"
    opponent = samples / ("random-bot.py" if path.stem == "win-block-bot" else
                          "win-block-bot.py")
    for first, second in ((path, opponent), (opponent, path)):
        game = play_game(first, second, timeout, coin_seed=7)
        if path.stem in game["forfeits"]:
            raise ValueError(f"sample game as {('O' if first == path else 'X')}: "
                             f"{game['errors'][path.stem]}")
    return "6 sample positions and 2 complete games passed"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("bot", type=Path, help="path to a single-file Python bot")
    parser.add_argument("--timeout", type=float, default=DEFAULT_TIMEOUT)
    args = parser.parse_args()
    if not math.isfinite(args.timeout) or args.timeout <= 0:
        parser.error("timeout must be positive and finite")
    try:
        print(f"Valid bot: {check_bot(args.bot, args.timeout)}")
    except (OSError, ValueError) as error:
        parser.error(str(error))


if __name__ == "__main__":
    main()
