"""Reference rung 0 (easiest): pick any empty square at random.

This is the simplest legal bot. It never plans ahead, so almost any thoughtful
opponent beats it. Use it to check that your setup works, then move on.

See example-bot.py for a line-by-line explanation of the Player class.
"""

import random

from Action import Action


class Player:
    def __init__(self, gamestate):
        self.gamestate = gamestate
        self.action = Action(-1)

    def run(self):
        self.act(self.gamestate)

    def act(self, gamestate):
        # Collect the free squares, then pick one at random.
        empty = [i for i in range(9) if gamestate.pieces[i] == 0]
        # HINT: random is legal but planless. Beating this is the first rung.
        self.action = Action(random.choice(empty))
