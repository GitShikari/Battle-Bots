"""Small baseline bot: commit to one empty square each round."""

import random
from threading import Thread

from Action import Action


class Player(Thread):
    def __init__(self, *args):
        super().__init__()
        self.args = args
        self.action = Action(-1)

    def act(self, gamestate):
        # Both bots choose from the same pre-round board, even if they collide.
        open_squares = [i for i, piece in enumerate(gamestate.pieces) if piece == 0]
        self.action = Action(random.choice(open_squares))

    def run(self):
        self.act(self.args[0])
