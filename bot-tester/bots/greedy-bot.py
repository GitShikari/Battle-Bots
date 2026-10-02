"""Reference rung 2: build your own lines as fast as possible.

For each free square, this bot asks "how much does MY position improve if I put
a mark there?" and picks the best one. It never considers what the opponent
might do, and it ignores the coin. That single-mindedness is surprisingly
strong, but it has no defence.

See example-bot.py for a line-by-line explanation of the Player class.
"""

from Action import Action


LINES = ((0, 1, 2), (3, 4, 5), (6, 7, 8),
         (0, 3, 6), (1, 4, 7), (2, 5, 8),
         (0, 4, 8), (2, 4, 6))


def own_potential(board):
    """Score only OUR opportunities; ignore the opponent entirely."""
    total = 0
    for line in LINES:
        cells = [board[i] for i in line]
        if 2 in cells:
            continue                      # blocked by the opponent
        # A line with 0/1/2 of our marks is worth 0/1/3/10 points.
        total += (0, 1, 3, 10)[cells.count(1)]
    return total


class Player:
    def __init__(self, gamestate):
        self.gamestate = gamestate
        self.action = Action(-1)

    def run(self):
        self.act(self.gamestate)

    def act(self, gamestate):
        board = gamestate.pieces
        best_square = None
        best_score = None
        for square in range(9):
            if board[square] != 0:
                continue
            trial = board.copy()
            trial[square] = 1             # pretend we place here
            score = own_potential(trial)
            if best_score is None or score > best_score:
                best_score = score
                best_square = square
        # HINT: this ignores the opponent's move and the coin. Averaging over
        # what they might do (see example-bot.py) is the next step up.
        self.action = Action(best_square)
