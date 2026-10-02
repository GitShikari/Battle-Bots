"""Reference rung 1: always take the lowest-numbered free square.

This bot is deterministic (no randomness) and therefore completely
predictable. A fixed rule like this is easy for an opponent to plan around --
which is exactly the lesson of this rung.

See example-bot.py for a line-by-line explanation of the Player class.
"""

from Action import Action


class Player:
    def __init__(self, gamestate):
        self.gamestate = gamestate
        self.action = Action(-1)

    def run(self):
        self.act(self.gamestate)

    def act(self, gamestate):
        # The first square whose value is 0 (empty) is our move.
        for square in range(9):
            if gamestate.pieces[square] == 0:
                # HINT: the opponent can predict exactly what you will do here.
                # Picking the best square, not the first, is the next step.
                self.action = Action(square)
                return
