"""
Rohan Bot v1
Battle-Bots: simultaneous Tic-Tac-Toe

Strategy:
- Consider every legal square we could choose.
- For each of our choices, consider every legal square the opponent
  could choose.
- Resolve the round exactly, including the 50/50 collision.
- Score the resulting position.
- Choose the move with the highest average score over all opponent choices.

This is intentionally our first "thinking" bot: it goes beyond the
public greedy/win-block bots without relying on alternating-turn minimax.
"""

from Action import Action

LINES = (
    (0, 1, 2), (3, 4, 5), (6, 7, 8),
    (0, 3, 6), (1, 4, 7), (2, 5, 8),
    (0, 4, 8), (2, 4, 6),
)

WIN = 10000.0
LOSS = -10000.0


def winner_state(board):
    """Return 1 if we win, 2 if opponent wins, 0 otherwise, 3 for both."""
    me = False
    opp = False

    for a, b, c in LINES:
        if board[a] == board[b] == board[c] == 1:
            me = True
        if board[a] == board[b] == board[c] == 2:
            opp = True

    if me and opp:
        return 3
    if me:
        return 1
    if opp:
        return 2
    return 0


def position_score(board):
    """Evaluate a resolved board from our perspective."""
    result = winner_state(board)

    if result == 1:
        return WIN
    if result == 2:
        return LOSS
    if result == 3:
        return 0.0

    score = 0.0

    # Prefer lines where we have more marks and the opponent has none.
    # Preferably, winning threats are much more valuable than one-mark lines.
    own_weights = {0: 0.0, 1: 1.0, 2: 12.0}
    opp_weights = {0: 0.0, 1: 1.0, 2: 12.0}

    for line in LINES:
        cells = [board[i] for i in line]
        own = cells.count(1)
        opp = cells.count(2)

        if own and opp:
            continue

        if own:
            score += own_weights[own]
        elif opp:
            score -= opp_weights[opp]

    # Mild positional preference among otherwise similar positions.
    # Center participates in 4 lines; corners in 3; edges in 2.
    for square in (4,):
        if board[square] == 1:
            score += 1.5
        elif board[square] == 2:
            score -= 1.5

    for square in (0, 2, 6, 8):
        if board[square] == 1:
            score += 0.5
        elif board[square] == 2:
            score -= 0.5

    return score


def resolve(board, my_move, opp_move):
    """
    Return one or two possible boards after the simultaneous round.

    Different squares -> one deterministic result.
    Same square -> two equally likely results because of the referee coin.
    """
    if my_move != opp_move:
        result = board.copy()
        result[my_move] = 1
        result[opp_move] = 2
        return (result,)

    mine = board.copy()
    mine[my_move] = 1

    theirs = board.copy()
    theirs[opp_move] = 2

    return (mine, theirs)


def expected_move_score(board, my_move, legal_opponent_moves):
    """Average our score over all possible opponent choices."""
    total = 0.0

    for opp_move in legal_opponent_moves:
        outcomes = resolve(board, my_move, opp_move)

        if len(outcomes) == 1:
            total += position_score(outcomes[0])
        else:
            # Collision: fair 50/50 coin.
            total += 0.5 * position_score(outcomes[0])
            total += 0.5 * position_score(outcomes[1])

    return total / len(legal_opponent_moves)


class Player:
    def __init__(self, gamestate):
        self.gamestate = gamestate
        self.action = Action(-1)

    def run(self):
        self.act(self.gamestate)

    def act(self, gamestate):
        board = gamestate.pieces
        legal = [i for i in range(9) if board[i] == 0]

        # Defensive fallback; the referee should never ask us to move
        # with no legal square.
        if not legal:
            self.action = Action(0)
            return

        best_move = legal[0]
        best_score = float("-inf")

        for my_move in legal:
            score = expected_move_score(board, my_move, legal)

            if score > best_score:
                best_score = score
                best_move = my_move

        self.action = Action(best_move)
