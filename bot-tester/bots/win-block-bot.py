"""Reference rung 3: take a win, else try to collide with their winning square.

This bot adds one layer of defence to rung 2:
  1. If a square would complete OUR line, take it.
  2. Otherwise, if a square would let the OPPONENT complete a line, pick that
     same square. Because the choices are simultaneous, matching their square
     forces a coin -- so this "block" only works half the time.
  3. Otherwise prefer the centre, then corners.

That coin-only block is the key weakness. An opponent notices it and the value
of looking one round ahead is the next step.

See example-bot.py for a line-by-line explanation of the Player class.
"""

from Action import Action


LINES = ((0, 1, 2), (3, 4, 5), (6, 7, 8),
         (0, 3, 6), (1, 4, 7), (2, 5, 8),
         (0, 4, 8), (2, 4, 6))


def completes_line(board, mark, square):
    """Would putting `mark` on `square` make three in a row?"""
    trial = board.copy()
    trial[square] = mark
    return any(all(trial[i] == mark for i in line) for line in LINES)


class Player:
    def __init__(self, gamestate):
        self.gamestate = gamestate
        self.action = Action(-1)

    def run(self):
        self.act(self.gamestate)

    def act(self, gamestate):
        board = gamestate.pieces
        empty = [i for i in range(9) if board[i] == 0]

        # 1. Win right now if we can.
        for square in empty:
            if completes_line(board, 1, square):
                self.action = Action(square)
                return

        # 2. Else collide with the square that would complete their line.
        for square in empty:
            if completes_line(board, 2, square):
                # HINT: a collision is only a 50/50 coin, so this is a partial
                # block. Judging the whole round -- including the coin -- is
                # what the expected-value bot does.
                self.action = Action(square)
                return

        # 3. Else take the centre, then any corner, then anything.
        preference = sorted(empty, key=lambda s: (s != 4, s not in (0, 2, 6, 8), s))
        self.action = Action(preference[0])
