"""Authoritative rules for simultaneous-choice 3x3 tic-tac-toe."""

from Action import Action


WIN_LINES = (
    (0, 1, 2), (3, 4, 5), (6, 7, 8),
    (0, 3, 6), (1, 4, 7), (2, 5, 8),
    (0, 4, 8), (2, 4, 6),
)


class GameState:
    def __init__(self) -> None:
        self.pieces = [0] * 9  # 0 empty, 1 O, 2 X.
        self.round_number = 0
        self.result = 0  # 0 ongoing, 1 O, 2 X, -1 draw.
        self.result_reason = None

    def winner(self) -> int:
        return self.result

    def valid_action(self, action: Action) -> bool:
        move = getattr(action, "move", None)
        return (self.result == 0 and type(move) is int and
                0 <= move < 9 and self.pieces[move] == 0)

    def resolve_round(self, o_action: Action, x_action: Action, rng):
        """Apply both sealed choices, then check lines. Return coin winner or None.

        Both actions must be legal on the board BEFORE either is resolved. An
        invalid round raises ValueError without changing the authoritative state.
        """
        if not self.valid_action(o_action) or not self.valid_action(x_action):
            raise ValueError("both choices must be empty squares before the round")

        o_move, x_move = o_action.move, x_action.move
        coin_winner = None
        if o_move == x_move:
            coin_winner = 1 + rng.getrandbits(1)
            self.pieces[o_move] = coin_winner
        else:
            self.pieces[o_move], self.pieces[x_move] = 1, 2
        self.round_number += 1

        o_wins = self._has_line(1)
        x_wins = self._has_line(2)
        if o_wins and x_wins:
            self.result = -1
            self.result_reason = "double_line"
        elif o_wins or x_wins:
            self.result = 1 if o_wins else 2
            self.result_reason = "line"
        elif all(self.pieces):
            self.result = -1
            self.result_reason = "full_board"
        return coin_winner

    def _has_line(self, player):
        return any(all(self.pieces[i] == player for i in line) for line in WIN_LINES)

    def view_for(self, player_number: int):
        """Independent, seed-free board: the receiving bot always sees itself as 1."""
        if self.result != 0 or type(player_number) is not int or player_number not in (1, 2):
            raise ValueError("bot view is available only during an active game")
        view = GameState()
        view.pieces = [value if player_number == 1 or value == 0 else 3 - value
                       for value in self.pieces]
        view.round_number = self.round_number
        return view

    def render(self) -> str:
        symbols = ".OX"
        rows = [" | ".join(symbols[self.pieces[3 * row + col]] for col in range(3))
                for row in range(3)]
        return "\n---+---+---\n".join(rows) + f"\ncompleted rounds: {self.round_number}"

    def draw(self):
        print(self.render())
