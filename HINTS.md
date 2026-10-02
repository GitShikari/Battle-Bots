# Hints: how to build a stronger bot

You do **not** need game theory or advanced maths to take part. Start with a
legal bot, then climb the rungs below. Each one is a real improvement, and the
reference bots in `bot-tester/bots/` show the early steps.

If Python itself is new to you, read [`PYTHON_BASICS.md`](PYTHON_BASICS.md)
first, then [`example-bot.py`](example-bot.py).

## Rung 0 — play legally
Return any empty square. This is `random-bot.py`. It works, but loses to almost
anything. First make sure your bot runs and never forfeits.

## Rung 1 — stop picking by habit
`first-empty-bot.py` always takes the lowest-numbered square. Because it is
fixed, an opponent can plan around it. Any rule that ignores the board is easy
to beat.

## Rung 2 — build your own threats
`greedy-bot.py` scores each square by how much it improves **your** lines and
picks the best. This is already much stronger than a fixed rule. Its blind spot
is that it never thinks about the opponent.

## Rung 3 — respect the opponent
You and your opponent choose **at the same time**, so you cannot react. Instead,
for each square you might pick, ask what happens for *every* square they might
pick, and take the best average. We do not ship a bot for this rung — writing it
yourself is the first real jump. `example-bot.py` only does rung 2.

## Rung 4 — treat a collision as a coin
If you and the opponent pick the same square, a fair coin decides who gets it.
Average the two outcomes: 50% of "I get the square" plus 50% of "they get it".
The rung-3 bots already fold this in; make sure yours does too.

## Rung 5 — look one round ahead
The board right after this round is **not final**. Instead of scoring it
directly, estimate how good it will be once you both play again. Even one extra
round of "if they do X and I answer with Y" separates you from the rung-3 bots.
This is the single biggest jump past the public reference bots.

## Rung 6 — be unpredictable
If you always choose the same "best" square, a thoughtful opponent can plan
around you. Choosing at random among your near-equal best moves makes you much
harder to exploit.

## Rung 7 (optional) — solve it exactly
This game is small enough to solve perfectly with *backward induction* (work
out the value of every board starting from the end) and a *matrix game* (a small
linear program) at each board. You do not need this to do well, and it is only
slightly stronger than a good look-ahead bot, but it is the theoretical ceiling.

---

## Background reading (optional)
These explain the ideas behind the rungs. None of them are required to compete.

- **Expected value** — averaging over uncertain outcomes (the coin, the hidden
  opponent move): <https://en.wikipedia.org/wiki/Expected_value>
- **Simultaneous games** — best response, maximin, mixed strategies:
  <https://en.wikipedia.org/wiki/Simultaneous_game>
- **Nash equilibrium** — the stable "no one can gain by changing alone" idea:
  <https://en.wikipedia.org/wiki/Nash_equilibrium>
- **Minimax / expectiminimax** — searching a game tree with an opponent and with
  chance: <https://en.wikipedia.org/wiki/Minimax>,
  <https://en.wikipedia.org/wiki/Expectiminimax>
- **Free video course** — Yale Open Courses, *Game Theory* (ECON 159, Ben Polak);
  see especially the lectures on best responses and mixed strategies:
  <https://oyc.yale.edu/economics/econ-159>
