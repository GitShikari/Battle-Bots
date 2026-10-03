# Rohan Bot v2
# Battle-Bots: simultaneous Tic-Tac-Toe
#
# Strategy:
# - Consider every legal square we could choose.
# - For each of our choices, predict the opponent's best response.
# - The opponent's response is chosen using the same board evaluator,
#   but from the opponent's perspective.
# - Resolve the simultaneous round exactly, including the 50/50 collision.
# - Evaluate the resulting position from our perspective.
# - Choose the move that leaves us with the highest score against
#   the opponent's predicted response.
#
# V1 averaged over ALL opponent moves.
# V2 models the opponent as a rational player and predicts their
# highest-scoring response to each candidate move.

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

    # Same heuristic as V1.
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

    # Mild positional preference.
    if board[4] == 1:
        score += 1.5
    elif board[4] == 2:
        score -= 1.5

    for square in (0, 2, 6, 8):
        if board[square] == 1:
            score += 0.5
        elif board[square] == 2:
            score -= 0.5

    return score


def opponent_position_score(board):
    """
    Evaluate a board from the opponent's perspective.

    We reuse exactly the V1 heuristic by swapping player labels.
    """
    swapped = board.copy()

    for i in range(9):
        if swapped[i] == 1:
            swapped[i] = 2
        elif swapped[i] == 2:
            swapped[i] = 1

    return position_score(swapped)


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


def expected_score(board, my_move, opp_move, evaluator):
    """
    Expected score for a fixed pair of simultaneous moves.

    evaluator decides whose perspective is being used.
    """
    outcomes = resolve(board, my_move, opp_move)

    if len(outcomes) == 1:
        return evaluator(outcomes[0])

    return (
        0.5 * evaluator(outcomes[0])
        + 0.5 * evaluator(outcomes[1])
    )


def predict_opponent_move(board, my_move, legal_opponent_moves):
    """
    Predict the opponent's best response to our candidate move.

    The opponent chooses the move with the highest expected score
    from THEIR perspective, including the collision coin flip.
    """
    best_opp_move = legal_opponent_moves[0]
    best_opp_score = float("-inf")

    for opp_move in legal_opponent_moves:
        score = expected_score(
            board,
            my_move,
            opp_move,
            opponent_position_score,
        )

        if score > best_opp_score:
            best_opp_score = score
            best_opp_move = opp_move

    return best_opp_move, best_opp_score


def v2_move_score(board, my_move, legal_opponent_moves):
    """
    Score one of our candidate moves against the opponent's
    predicted best response.
    """
    predicted_move, _ = predict_opponent_move(
        board,
        my_move,
        legal_opponent_moves,
    )

    our_score = expected_score(
        board,
        my_move,
        predicted_move,
        position_score,
    )

    return our_score, predicted_move


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
            score, predicted_opp_move = v2_move_score(
                board,
                my_move,
                legal,
            )

            if score > best_score:
                best_score = score
                best_move = my_move

        self.action = Action(best_move)
