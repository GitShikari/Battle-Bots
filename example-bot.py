"""
Battle Bots — starter bot (read me first!)

Welcome! Your job is to write a Python "bot" that plays simultaneous
tic-tac-toe on a 3x3 board. This file is a complete, working example with
comments explaining every line, including some Python basics. Copy it, rename
it to teamname_bot.py, and change the parts you want.

This starter is deliberately simple: it builds its OWN lines and does not think
about the opponent. That is a decent start, but it is beatable. Open HINTS.md to
see the next steps (averaging over the opponent's move, the coin, and looking
one round ahead).

--------------------------------------------------------------------------
THE GAME IN A NUTSHELL
--------------------------------------------------------------------------
The board squares are numbered 0..8 like this:

    0 | 1 | 2
    --+---+--
    3 | 4 | 5
    --+---+--
    6 | 7 | 8

Each round, BOTH bots secretly choose one empty square at the same time.
  * Different squares -> both marks appear.
  * Same square       -> a fair coin gives that square to one bot; the other
                         bot places nothing that round.
After the whole round, if you have three of your marks in a row, column or
diagonal, you win. If you and your opponent both complete a line in the same
round, it is a draw. If the board fills up with no winner, it is also a draw.

You will NOT see the opponent's choice for the round, and you will not know
the coin result until after you have chosen. So a good bot plans around "what
might they do?" rather than reacting.

--------------------------------------------------------------------------
WHAT THE RUNNER EXPECTS FROM YOUR FILE
--------------------------------------------------------------------------
Your file must define a class named Player with these three pieces:

    class Player:
        def __init__(self, gamestate):   # 1. set up; runs once per round
            ...
        def run(self):                   # 2. the runner calls this
            self.act(self.gamestate)
        def act(self, gamestate):        # 3. choose; set self.action
            self.action = Action(some_square)

The runner makes a fresh Player for every round and then calls run(). Your
chosen square is read from self.action at the end. If you do not set it, or you
choose an occupied/out-of-range square, you forfeit that game.

You can read two things from `gamestate`:
    gamestate.pieces        -> a list of nine numbers describing the board.
                               0 = empty, 1 = YOUR mark, 2 = opponent's mark.
    gamestate.round_number  -> how many rounds have finished (starts at 0).

Note that the board is always shown from YOUR point of view: your own marks
are always 1, even if the scoreboard calls you "O" or "X".

--------------------------------------------------------------------------
A 60-SECOND PYTHON PRIMER (skip if you already know this)
--------------------------------------------------------------------------
* A variable stores a value:            x = 5
* A list stores several values:         squares = [0, 0, 0]
* Indexing starts at 0:                 squares[0] is the first item
* len(squares) is how many items:       len([1, 2, 3]) == 3
* A function is reusable code:          def double(n): return n * 2
* A class is a blueprint for objects.   class Player: ...
  An object is one thing built from the blueprint. Creating it runs __init__.
* `self` means "this particular object". Inside methods you write self.thing to
  read or set that object's data.
* `__init__` (two underscores each side) is the setup method that runs when the
  object is created.
* Methods are just functions that live inside a class and take self first.

Your class does not need to inherit from anything here. The runner creates
`Player(gamestate)` and calls `run()` directly. Inheritance (for example
`class Player(Thread):`, or a `super().__init__()` call) belongs to Python's
threading library and is not needed for this competition, so a plain class like
the one below is enough.
"""

# Importing gives us names defined in another file. `Action` is the small
# helper the runner uses to carry your chosen square.
from Action import Action


# The eight winning lines, written as triples of square numbers. We reuse this
# below.
LINES = ((0, 1, 2), (3, 4, 5), (6, 7, 8),   # rows
         (0, 3, 6), (1, 4, 7), (2, 5, 8),   # columns
         (0, 4, 8), (2, 4, 6))              # diagonals


def own_score(board):
    """Score how good a board is for US, ignoring the opponent.

    board is a list of nine numbers (0 empty, 1 ours, 2 theirs). This counts how
    many of our marks sit in each line that the opponent has not blocked; a line
    with more of our marks is worth more. It is only a rule of thumb.
    """
    total = 0
    for line in LINES:
        cells = [board[i] for i in line]
        if 2 in cells:
            continue                        # the opponent blocks this line
        # 0, 1, 2 or 3 of our marks is worth 0, 1, 3 or 10 points.
        total += (0, 1, 3, 10)[cells.count(1)]
    return total


class Player:
    """Our bot. The runner creates one and calls run() each round."""

    def __init__(self, gamestate):
        # __init__ runs when the runner builds Player(gamestate). Store what we
        # were given and give self.action a safe placeholder. act() replaces it.
        self.gamestate = gamestate
        self.action = Action(-1)

    def run(self):
        # The runner calls this. We simply hand control to act().
        self.act(self.gamestate)

    def act(self, gamestate):
        board = gamestate.pieces

        # Try every free square, score our position after placing there, and
        # keep the best one.
        best_square = None
        best_value = None
        for square in range(9):
            if board[square] != 0:
                continue                        # not empty: skip it
            trial = board.copy()                # a copy we can edit safely
            trial[square] = 1                   # pretend we place here
            value = own_score(trial)
            if best_value is None or value > best_value:
                best_value = value
                best_square = square

        # HINT: this never considers the opponent's move or the coin. Averaging
        # over what they might do -- and treating a same-square pick as a 50/50
        # coin -- is the next step. See HINTS.md.
        self.action = Action(best_square)
