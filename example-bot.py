"""Example bot: weigh each choice against all possible opponent choices."""

import random
from threading import Thread

from Action import Action


LINES = ((0, 1, 2), (3, 4, 5), (6, 7, 8),
         (0, 3, 6), (1, 4, 7), (2, 5, 8),
         (0, 4, 8), (2, 4, 6))


def score(board):
    """Score a resulting board from our perspective (our mark is always 1)."""
    ours = any(all(board[i] == 1 for i in line) for line in LINES)
    theirs = any(all(board[i] == 2 for i in line) for line in LINES)
    if ours or theirs:
        return (10 if ours else 0) - (10 if theirs else 0)
    # An unblocked line with two of our marks is promising, but not a win yet.
    potential = 0
    for line in LINES:
        cells = [board[i] for i in line]
        if 2 not in cells:
            potential += cells.count(1)
        if 1 not in cells:
            potential -= cells.count(2)
    return potential / 10


class Player(Thread):
    def __init__(self, *args):
        super().__init__()
        self.args = args
        self.action = Action(-1)

    def act(self, gamestate):
        # Both bots choose on the SAME board; the opponent's move is hidden.
        board = gamestate.pieces
        empty = [i for i, piece in enumerate(board) if piece == 0]
        results = []
        for mine in empty:
            total = 0
            for theirs in empty:
                if mine == theirs:
                    # A fair coin awards a collision to either player.
                    winning_coin = board.copy()
                    losing_coin = board.copy()
                    winning_coin[mine], losing_coin[mine] = 1, 2
                    total += (score(winning_coin) + score(losing_coin)) / 2
                else:
                    next_board = board.copy()
                    next_board[mine], next_board[theirs] = 1, 2
                    total += score(next_board)
            results.append(total / len(empty))

        best = max(results)
        self.action = Action(random.choice(
            [move for move, value in zip(empty, results) if value >= best - 1e-9]
        ))

    def run(self):
        self.act(self.args[0])
