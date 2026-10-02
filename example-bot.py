"""
Battle Bots — starter bot (read me first!)

Welcome! Your job is to write a Python "bot" that plays simultaneous
tic-tac-toe on a 3x3 board. This file is a complete, working example with
comments explaining every line, including some Python basics. Copy it, rename
it to teamname_bot.py, and change the parts you want.

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

You may also see older example bots that write `class Player(Thread)` and
`super().__init__()`. That version inherited from Python's threading library,
which this competition used to need. It does not need it anymore: the runner
simply calls run() for you. A plain class like the one below is enough, so you
can ignore Thread entirely.
"""

# Importing gives us names defined in another file. `Action` is the small
# helper the runner uses to carry your chosen square.
from Action import Action


# The eight winning lines, written as triples of square numbers. We reuse this
# in the scoring helper below.
LINES = ((0, 1, 2), (3, 4, 5), (6, 7, 8),   # rows
         (0, 3, 6), (1, 4, 7), (2, 5, 8),   # columns
         (0, 4, 8), (2, 4, 6))              # diagonals


def line_score(board):
    """Give a rough score to a board from OUR point of view.

    board is a list of nine numbers (0 empty, 1 ours, 2 theirs). Bigger is
    better for us. We give a large bonus for a completed line and otherwise
    count how many of our marks sit in lines the opponent has not blocked.

    This is only a heuristic (a rule of thumb) -- it is not exact, but it is a
    good enough judge of "is this position promising?" for a starter bot.
    """
    for line in LINES:
        if all(board[i] == 1 for i in line):
            return 10.0      # we have three in a line: excellent
        if all(board[i] == 2 for i in line):
            return -10.0     # they have three in a line: terrible

    score = 0.0
    for line in LINES:
        cells = [board[i] for i in line]
        if 2 not in cells:           # they are not blocking this line
            score += cells.count(1)  # each of our marks here is useful
        if 1 not in cells:           # we are not blocking this line
            score -= cells.count(2)  # each of their marks here is dangerous
    return score / 10.0


class Player:
    """Our bot. The runner creates one and calls run() each round."""

    def __init__(self, gamestate):
        # __init__ runs when the runner builds Player(gamestate). Store what we
        # were given and give self.action a safe placeholder. act() will replace
        # it with the real move.
        self.gamestate = gamestate
        self.action = Action(-1)

    def run(self):
        # The runner calls this. We simply hand control to act().
        self.act(self.gamestate)

    def act(self, gamestate):
        # 1. Find the squares that are still free.
        board = gamestate.pieces               # the nine board numbers
        empty = [i for i in range(9) if board[i] == 0]

        # 2. For each square we might pick, work out how good it usually is.
        #    "Usually" means: average over every square the opponent might pick,
        #    and, if we pick the same square, average over both coin results.
        #    This is the key idea of the game and is called *expected value*.
        results = []                            # one number per candidate square
        for mine in empty:
            total = 0.0
            for theirs in empty:
                if mine == theirs:
                    # A collision: half the time we get the square, half the
                    # time they do. Try both and average.
                    ours = board.copy()
                    ours[mine] = 1
                    theirs_board = board.copy()
                    theirs_board[mine] = 2
                    total += (line_score(ours) + line_score(theirs_board)) / 2
                else:
                    # No collision: both marks go down. Score the result.
                    after = board.copy()
                    after[mine] = 1
                    after[theirs] = 2
                    total += line_score(after)
            results.append(total / len(empty))  # average over all opponent picks

        # 3. Choose the square with the best average. If several tie, pick one
        #    at random so we are not perfectly predictable.
        best = max(results)
        best_moves = [move for move, value in zip(empty, results) if value >= best - 1e-9]
        import random                            # standard library; safe to use
        self.action = Action(random.choice(best_moves))
