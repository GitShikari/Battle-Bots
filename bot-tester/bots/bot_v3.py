# Rohan Bot v3
# Battle-Bots: simultaneous Tic-Tac-Toe
#
# Strategy:
# - Consider every legal move we could choose.
# - Model the opponent's likely response instead of assuming every
#   opponent move is equally likely.
# - Give each opponent move a probability using how good that move
#   is from the opponent's perspective.
# - Convert those scores into a softmax probability distribution.
# - Evaluate our candidate move against the weighted distribution.
# - Resolve simultaneous moves exactly, including the 50/50 collision.
# - Choose the move with the highest expected score.
#
# V1: uniform probability over opponent moves.
# V2: opponent's single predicted best response.
# V3: probabilistic opponent prediction.
#
# The temperature controls how concentrated the prediction is.
# Higher temperature = more uncertainty / closer to V1.
# Lower temperature = stronger preference for the predicted best move.

from math import exp
from Action import Action


LINES = (
    (0, 1, 2), (3, 4, 5), (6, 7, 8),
    (0, 3, 6), (1, 4, 7), (2, 5, 8),
    (0, 4, 8), (2, 4, 6),
)

WIN = 10000.0
LOSS = -10000.0

# Moderate uncertainty: the opponent is likely to prefer good moves,
# but we do not assume they always choose the single best move.
TEMPERATURE = 8.0


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

    # Same heuristic as V1/V2.
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
    """Evaluate the board from the opponent's perspective."""
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
    """Expected score for a fixed pair of simultaneous moves."""
    outcomes = resolve(board, my_move, opp_move)

    if len(outcomes) == 1:
        return evaluator(outcomes[0])

    return (
        0.5 * evaluator(outcomes[0])
        + 0.5 * evaluator(outcomes[1])
    )


def softmax(values, temperature=TEMPERATURE):
    """
    Convert opponent move scores into probabilities.

    Subtracting the maximum keeps exp() numerically stable.
    """
    if not values:
        return []

    maximum = max(values)
    weights = [
        exp((value - maximum) / temperature)
        for value in values
    ]

    total = sum(weights)

    if total == 0.0:
        return [1.0 / len(values)] * len(values)

    return [weight / total for weight in weights]


def predict_opponent_distribution(
    board,
    my_move,
    legal_opponent_moves,
):
    """
    Estimate P(opponent move) using a softmax over the opponent's
    expected utility.

    Good opponent moves get higher probability, but weaker moves
    retain non-zero probability.
    """
    opponent_scores = []

    for opp_move in legal_opponent_moves:
        score = expected_score(
            board,
            my_move,
            opp_move,
            opponent_position_score,
        )
        opponent_scores.append(score)

    probabilities = softmax(opponent_scores)

    return list(zip(legal_opponent_moves, probabilities, opponent_scores))


def v3_move_score(board, my_move, legal_opponent_moves):
    """
    Calculate our expected score against the probabilistic
    opponent model.
    """
    prediction = predict_opponent_distribution(
        board,
        my_move,
        legal_opponent_moves,
    )

    total = 0.0

    for opp_move, probability, _ in prediction:
        outcome_score = expected_score(
            board,
            my_move,
            opp_move,
            position_score,
        )
        total += probability * outcome_score

    return total, prediction


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
            score, _ = v3_move_score(
                board,
                my_move,
                legal,
            )

            if score > best_score:
                best_score = score
                best_move = my_move

        self.action = Action(best_move)
