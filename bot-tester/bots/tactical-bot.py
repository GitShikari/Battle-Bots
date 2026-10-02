"""Reference rung 4 (strongest public): average over the opponent and the coin.

This is the same idea as example-bot.py, tidied up. For every square we could
choose, it averages the resulting board score over:
  * every square the opponent might choose (we cannot see their move), and
  * both coin outcomes when we choose the same square.
It then picks the best average. That is a real step up from the greedy bots:
it respects that the opponent moves at the same time and that collisions are a
coin toss.

See example-bot.py for a line-by-line explanation of the Player class. To go
further still, read HINTS.md (looking one round ahead, mixing your play).
"""

import random

from Action import Action


LINES = ((0, 1, 2), (3, 4, 5), (6, 7, 8),
         (0, 3, 6), (1, 4, 7), (2, 5, 8),
         (0, 4, 8), (2, 4, 6))


def line_score(board):
    """Rough value of a board from our point of view (ours are 1s)."""
    for line in LINES:
        if all(board[i] == 1 for i in line):
            return 10.0
        if all(board[i] == 2 for i in line):
            return -10.0
    score = 0.0
    for line in LINES:
        cells = [board[i] for i in line]
        if 2 not in cells:
            score += cells.count(1)
        if 1 not in cells:
            score -= cells.count(2)
    return score / 10.0


class Player:
    def __init__(self, gamestate):
        self.gamestate = gamestate
        self.action = Action(-1)

    def run(self):
        self.act(self.gamestate)

    def act(self, gamestate):
        board = gamestate.pieces
        empty = [i for i in range(9) if board[i] == 0]

        results = []
        for mine in empty:
            total = 0.0
            for theirs in empty:
                if mine == theirs:
                    ours = board.copy()
                    ours[mine] = 1
                    theirs_board = board.copy()
                    theirs_board[mine] = 2
                    total += (line_score(ours) + line_score(theirs_board)) / 2
                else:
                    after = board.copy()
                    after[mine] = 1
                    after[theirs] = 2
                    total += line_score(after)
            results.append(total / len(empty))

        best = max(results)
        choices = [move for move, value in zip(empty, results) if value >= best - 1e-9]
        self.action = Action(random.choice(choices))
