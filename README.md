# Battle Bots: Simultaneous Tic-Tac-Toe

Two bots choose a square **at the same time** on a 3×3 board. They cannot see each other's choice until the round is over. Build a single-file Python bot and try to predict, defend and adapt!

## Rules

Squares are numbered left to right, top to bottom:

```text
 0 | 1 | 2
---+---+---
 3 | 4 | 5
---+---+---
 6 | 7 | 8
```

1. Both bots receive the **same pre-round board** and independently choose **one square that is empty on that board**. Neither bot sees the other's current choice.
2. If the choices differ, put both marks down. If they match, the referee flips a **fair coin**: the winning bot claims that square and the other bot places nothing that round. The coin is flipped only for a collision.
3. After resolving the whole round, three of your marks in a row, column or diagonal wins. If **both** bots make a line in the same round, it is a draw. A full board without a sole winner is a draw.
4. An invalid action, crash or timeout forfeits the game to the other bot. If **both** bots fail in the same round, neither receives points for that game.

There is no first move: O and X are merely labels so the match log can show both choices. Each bot is given its own normalized view.

## Your bot

Submit a **single Python script** named `teamname_bot.py`. See [example-bot.py](example-bot.py), or start from any bot in `bot-tester/bots/`. Define a `Player` class with `act(gamestate)` and set `self.action = Action(i)` for an **integer** square `i` from `0` through `8` where `gamestate.pieces[i] == 0`. One new `Player` object is made **each round**, so do not rely on its fields to remember earlier rounds.

New to Python or classes? Read [PYTHON_BASICS.md](PYTHON_BASICS.md) first. You do **not** need `threading` or `super().__init__()` — the runner simply calls `run()`.

The smallest working bot looks like this:

```python
from Action import Action

class Player:
    def __init__(self, gamestate):
        self.gamestate = gamestate
        self.action = Action(-1)

    def run(self):
        self.act(self.gamestate)

    def act(self, gamestate):
        self.action = Action(gamestate.pieces.index(0))
```

It always picks the first free square. It is legal, but predictable and easy to beat.

| Bot-facing field | Meaning |
| --- | --- |
| `gamestate.pieces` | Nine integers: `0` empty, `1` **your** mark, `2` the opponent's, regardless of whether the log calls you O or X. |
| `gamestate.round_number` | Number of completed rounds, beginning at `0`. |

Bot standard output is suppressed. The example bot averages the result of a choice over the opponent's possible choices, treating a same-square coin as 50/50; it is a starting point, not a perfect strategy. Plain alternating-turn tic-tac-toe minimax does **not** model simultaneous choices or the referee's coin.

## Reference bots and hints

`bot-tester/bots/` contains a small ladder, easiest first. Play against them, beat them, then climb. Read [HINTS.md](HINTS.md) for the ideas behind each rung and how to go beyond them.

| Bot | Idea | Its weakness |
| --- | --- | --- |
| `random-bot.py` | pick any empty square | no plan at all |
| `first-empty-bot.py` | always the lowest empty square | completely predictable |
| `greedy-bot.py` | build your own lines, ignore the opponent | no defence |
| `win-block-bot.py` | win if you can, else collide with their winning square | a collision is only a 50/50 coin |
| `tactical-bot.py` | average over the opponent's moves and the coin | looks only one round ahead |

## Test locally

Install **Python 3** and put your file in `bot-tester/bots/`. From the repository's top directory, run:

```sh
python3 bot-tester/validate.py bot-tester/bots/teamname_bot.py
python3 bot-tester/main.py --paired-rounds 2 --seed demo
```

On Windows, use `python` or `py` if `python3` is not available. **Validate** checks six board positions and two full games; passing is not a guarantee that every possible board is handled. **Simulate** plays everyone in the bots folder; `--paired-rounds 2` is a quick local run. Use `--seed demo` only to reproduce **local** matches; the official referee generates its own private seed. A bot that deliberately reseeds itself can still behave differently on another run. To check a **local** saved result, run `python3 bot-tester/verify_results.py bot-tester/tournament-results.json --allow-embedded-seed`. That checks consistency, not who created the log; an official log needs a separately supplied seed and signature for authentication.

By default a local tournament uses **10 paired seed rounds: 20 games per pair**, swapping O/X labels each pair of games. **The two seat orders get different coin and bot-random streams**; their outcomes are not copies. Each bot has a **hard 2.5-second wall-clock limit per choice**, including process startup; a bot still running after the deadline forfeits that game. You can test a different limit with `--timeout SECONDS`. Results are saved in `bot-tester/tournament-results.json`. The official judge uses an explicit hashed roster rather than this local tester's bot folder.

The local tester runs files in `bot-tester/bots/` as ordinary Python processes with **your account's permissions**. Run only scripts you trust on your own computer. It is not the official judge. For the official event, organizers use isolated bot processes, an explicit hashed submission roster and a private random seed generated inside the referee. Official results are signed and audited separately from this local tester. A locally saved JSON log by itself is not proof of an official result; after judging, the organizer can release the seed, original signature and verification key for `verify_results.py`.

## Submission: code **and** strategy PDF

Send **both** `teamname_bot.py` and `teamname_strategy.pdf` through the submission link announced by the coordinators. The PDF should be at most **two pages**. In your own words, explain:

- How your bot chooses a square, including what it assumes about the other bot and how it treats collisions/coin outcomes.
- Which ideas you tried, what changed while testing, and at least one weakness or edge case you noticed.
- How you tested it (for example, both O/X labels, different opponents, or repeatable seeds). A brief explanation and small example are enough; fancy diagrams and advanced algorithms are not required.

AI coding assistance is allowed. We evaluate the behavior, the code and your ability to explain the decisions—not a guess about whether you used an AI tool.
The sample bots use only the Python standard library; no third-party package is guaranteed on the judging machine. Your script must be self-contained apart from the provided `Action` and `GameState` modules.

## Judging

**Performance (primary).** Each game awards 1 for a win, 0.5 for a draw, and 0 for a loss; a double forfeit gives 0 to both. Every entrant plays every other entrant for the same number of paired games (both O and X). Your **performance** is your average points per game.

**Ranking is banded.** Because the coin adds luck, two bots whose performances differ by less than the tournament's statistical noise band are treated as **tied on performance**. The band shrinks as more games are played. Within a tied band, the code/PDF quality score decides the order. A bot in a strictly better band always outranks one in a worse band, so a nicer write-up can never overtake a clearly stronger bot. Genuinely equal bots still tie — that is expected, and is exactly what the quality score is for.

**Quality (0–20), used to order bots within a performance band.** Same rubric for everyone:

| Criterion | Points | What we look for |
| --- | ---: | --- |
| General strategy | 0–6 | Works across different boards and opponents; reasoning rather than a large unexplained board-to-move lookup. |
| Reasoning | 0–6 | PDF explains choices, opponent uncertainty, collisions and tradeoffs; matches what the code does. |
| Testing and iteration | 0–4 | Evidence of trying different situations, learning from failures and checking edge cases. |
| Clarity and robustness | 0–4 | Understandable code and reliable decisions within the announced limits. |

Remaining ties (same band and quality): head-to-head points, then wins, then fewest forfeits, then a shared rank. The organizer records the quality subscores and brief reasons, and publishes results and match logs. A short strategy walkthrough may be requested to clarify a submission; eloquence and code length are not scoring criteria.

## Submission details

- Submission link: **to be announced**.
- Submission deadline and time zone: **to be announced**.
- Tournament and results timeline: **to be announced**.
- Prizes and participation details: **to be announced**.
