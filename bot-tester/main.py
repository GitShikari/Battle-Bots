"""Paired-seed local tournament for simultaneous tic-tac-toe."""

import argparse
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
from itertools import combinations
import math
import os
from pathlib import Path
import random
import re
import secrets
import signal
import subprocess
import sys
import tempfile
import time

BASE = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE))  # Single-file bots can import Action and GameState.

from Action import Action
from GameState import GameState

DEFAULT_TIMEOUT = 2.5  # Wall-clock seconds per choice, including worker startup.
DEFAULT_PAIRED_ROUNDS = 10  # 20 games per pair locally; the official referee uses far more.
DEFAULT_WORKERS = 1  # Games played in parallel; the official referee raises this.
BAND_Z = 2.8  # ~95% confidence, ~80% power for the two-bot performance gap.
BAND_SIGMA = 0.5  # Conservative per-game spread (points are 0/0.5/1).
OUTPUT_LIMIT = 8192
BOT_NAME = re.compile(r"[A-Za-z0-9][A-Za-z0-9_-]{0,59}\.py\Z")
QUALITY_CATEGORIES = {"generality": 6, "reasoning": 6, "testing": 4, "clarity": 4}
SCORING = "banded-v1"


def _safe_message(value):
    return "".join(character if " " <= character <= "~" else "?"
                   for character in str(value)[:300])


def request_move(path, view, timeout=DEFAULT_TIMEOUT, bot_seed="0"):
    """Forfeit if one choice exceeds its wall-clock deadline (not a sandbox)."""
    request = json.dumps({
        "pieces": view.pieces,
        "round_number": view.round_number,
        "bot_seed": bot_seed,
    }).encode("utf-8")
    deadline = time.monotonic() + timeout
    with tempfile.TemporaryFile() as output, tempfile.TemporaryFile() as errors:
        options = {"start_new_session": True} if os.name == "posix" else {}
        process = subprocess.Popen(
            [sys.executable, "-I", str(BASE / "worker.py"), str(path)],
            stdin=subprocess.PIPE, stdout=output, stderr=errors, close_fds=True, **options,
        )
        timed_out = False
        try:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                timed_out = True
            else:
                process.communicate(input=request, timeout=remaining)
                timed_out = time.monotonic() > deadline
        except subprocess.TimeoutExpired:
            timed_out = True
        finally:
            if os.name == "posix":
                try:
                    os.killpg(process.pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
            elif timed_out and process.poll() is None:
                process.kill()
            if timed_out:
                process.communicate()
        if timed_out:
            return None, "timeout"
        output.seek(0)
        payload = output.read(OUTPUT_LIMIT + 1)
        if process.returncode != 0 or len(payload) > OUTPUT_LIMIT:
            errors.seek(0)
            detail = _safe_message(errors.read(300).decode("utf-8", errors="replace")).strip()
            return None, (f"bot process failed: {detail[:200]}" if detail
                          else f"bot exited without an action (exit code {process.returncode})")
        try:
            reply = json.loads(payload)
            if type(reply) is not dict:
                raise ValueError("not an object")
            if "error" in reply:
                return None, _safe_message(reply["error"])
            move = reply["move"]
            if type(move) is not int:
                raise ValueError("not an integer")
            return move, None
        except (ValueError, KeyError, UnicodeDecodeError) as error:
            return None, f"invalid bot output: {error}"


def _derived_seed(master, pair, seed_index, label):
    context = f"{pair[0]}|{pair[1]}|{seed_index}|{label}".encode("ascii")
    return hashlib.blake2b(context, key=bytes.fromhex(master), digest_size=32).hexdigest()


def play_game(first, second, timeout=DEFAULT_TIMEOUT, coin_seed=0,
              bot_seed_for=None, move_provider=None, game_id=None):
    """Collect both sealed choices before resolving a round; O=first, X=second."""
    state = GameState()
    bots = {1: first, 2: second}
    rng = random.Random(coin_seed)
    game = {"first": first.stem, "second": second.stem, "rounds": [],
            "game_id": game_id or f"O:{first.stem}|X:{second.stem}"}
    provider = move_provider or request_move
    while state.winner() == 0:
        # These are copies of the SAME pre-round state. No bot learns the other
        # bot's current choice before committing its own.
        views = {player: state.view_for(player) for player in (1, 2)}
        choices = {}
        errors = {}
        # Launch both workers before reading either reply.
        with ThreadPoolExecutor(max_workers=2) as executor:
            pending = {
                player: executor.submit(
                    provider, bots[player], views[player], timeout,
                    bot_seed_for(bots[player].stem, state.round_number) if bot_seed_for else "0",
                )
                for player in (1, 2)
            }
            for player in (1, 2):
                move, error = pending[player].result()
                choices[player] = move
                if error is None and not state.valid_action(Action(move)):
                    error = f"illegal action: {move}"
                if error is not None:
                    errors[player] = error
        if errors:
            game["forfeits"] = [bots[player].stem for player in errors]
            game["errors"] = {bots[player].stem: error for player, error in errors.items()}
            game["winner"] = bots[3 - next(iter(errors))].stem if len(errors) == 1 else None
            game["reason"] = "forfeit" if len(errors) == 1 else "double_forfeit"
            break
        coin_winner = state.resolve_round(Action(choices[1]), Action(choices[2]), rng)
        game["rounds"].append({
            "number": state.round_number,
            "choices": {"O": choices[1], "X": choices[2]},
            "coin_winner": "O" if coin_winner == 1 else "X" if coin_winner == 2 else None,
            "board": state.pieces.copy(),
        })
    else:
        game["winner"] = bots[state.winner()].stem if state.winner() > 0 else None
        game["forfeits"] = []
        game["errors"] = {}
        game["reason"] = state.result_reason
    game["round_count"] = state.round_number
    return game


def validate_quality(names, quality):
    if quality is None:
        return None
    if type(quality) is not dict or set(quality) != set(names):
        raise ValueError("quality scorecard must have one entry per bot name")
    validated = {}
    for name in names:
        values = quality[name]
        if type(values) is not dict or set(values) != set(QUALITY_CATEGORIES):
            raise ValueError(f"{name}: expected {list(QUALITY_CATEGORIES)}")
        for category, limit in QUALITY_CATEGORIES.items():
            score = values[category]
            if type(score) is not int or not 0 <= score <= limit:
                raise ValueError(f"{name}: {category} must be an integer from 0 to {limit}")
        validated[name] = values.copy()
    return validated


def band_half_width(games_per_bot, band_z=BAND_Z, band_sigma=BAND_SIGMA):
    """Half-width of the statistically indistinguishable performance band."""
    if games_per_bot <= 0:
        return float("inf")
    return band_z * band_sigma * math.sqrt(2.0 / games_per_bot)


def standings_for(names, games, paired_rounds=DEFAULT_PAIRED_ROUNDS, quality=None):
    """Rank by performance band, then by human-scored quality within the band.

    Bots whose average points per game are within the tournament's noise band
    are statistically tied; quality then decides their order. A bot in a
    strictly higher band always outranks a lower one, so a nicer write-up
    cannot overtake a clearly stronger bot.
    """
    quality = validate_quality(names, quality)
    records = {name: dict(points=0.0, wins=0, draws=0, losses=0, forfeits=0, played=0)
               for name in names}
    pair_points = {name: {other: 0.0 for other in names if other != name}
                   for name in names}
    for game in games:
        first, second, winner = game["first"], game["second"], game["winner"]
        records[first]["played"] += 1
        records[second]["played"] += 1
        if game["reason"] == "double_forfeit":
            for name in (first, second):
                records[name]["losses"] += 1
                records[name]["forfeits"] += 1
        elif winner is None:
            for name, other in ((first, second), (second, first)):
                records[name]["points"] += 0.5
                records[name]["draws"] += 1
                pair_points[name][other] += 0.5
        else:
            loser = second if winner == first else first
            records[winner]["points"] += 1
            records[winner]["wins"] += 1
            records[loser]["losses"] += 1
            pair_points[winner][loser] += 1
            if game["forfeits"]:
                records[loser]["forfeits"] += 1

    for name in names:
        record = records[name]
        record["performance"] = record["points"] / (record["played"] or 1)
        record["quality"] = quality[name] if quality is not None else None
        record["quality_score"] = sum(quality[name].values()) if quality is not None else None

    # Band the bots by performance. The leader of each band is fixed, so a
    # long chain of tiny gaps does not merge the whole field into one band.
    by_performance = sorted(names, key=lambda name: (-records[name]["performance"], name))
    band = band_half_width(min((records[name]["played"] for name in names), default=0))
    band_of, current, leader = {}, 0, None
    for name in by_performance:
        performance = records[name]["performance"]
        if leader is None or performance <= leader - band:
            current += 1
            leader = performance
        band_of[name] = current
        records[name]["band"] = current

    # Head-to-head is only meaningful among bots in the same band.
    for name in names:
        band_mates = [other for other in names
                      if other != name and band_of[other] == band_of[name]]
        records[name]["head_to_head"] = sum(pair_points[name][other] for other in band_mates)

    def ranking_key(name):
        record = records[name]
        quality_score = record["quality_score"] if record["quality_score"] is not None else 0
        return (record["band"], -quality_score, -record["head_to_head"],
                -record["wins"], record["forfeits"])

    order = sorted(names, key=lambda name: (ranking_key(name), name))
    standings = []
    for position, name in enumerate(order, 1):
        rank = (standings[-1]["rank"]
                if standings and ranking_key(name) == ranking_key(order[position - 2])
                else position)
        standings.append({"name": name, "rank": rank, **records[name]})
    return standings


def run_tournament(paths, timeout=DEFAULT_TIMEOUT, paired_rounds=DEFAULT_PAIRED_ROUNDS,
                   seed=None, quality=None, move_provider=None, workers=DEFAULT_WORKERS):
    if not math.isfinite(timeout) or timeout <= 0:
        raise ValueError("timeout must be positive and finite")
    if type(paired_rounds) is not int or paired_rounds <= 0:
        raise ValueError("paired_rounds must be a positive integer")
    if type(workers) is not int or workers <= 0:
        raise ValueError("workers must be a positive integer")
    if seed is None:
        seed = secrets.token_hex(32)
    elif type(seed) is not str or not seed:
        raise ValueError("seed must be a non-empty string")
    elif not re.fullmatch(r"[0-9a-fA-F]{64}", seed):
        seed = hashlib.sha256(seed.encode("utf-8")).hexdigest()
    bots = []
    for path in paths:
        path = Path(path)
        if path.is_symlink() or not path.is_file() or not BOT_NAME.fullmatch(path.name):
            raise ValueError(f"invalid bot file: {path}")
        bots.append(path.resolve())
    bots.sort(key=lambda path: path.name)
    if len({path.stem for path in bots}) != len(bots):
        raise ValueError("bot filenames must have distinct names")
    if len(bots) < 2:
        raise ValueError("at least two bot files are required")
    names = [path.stem for path in bots]
    quality = validate_quality(names, quality)

    def play_task(task):
        first, second, index, o, x = task
        pair = (first.stem, second.stem)
        seat = f"O:{o.stem}|X:{x.stem}"
        game_id = f"{first.stem}|{second.stem}|{index}|{seat}"
        coin_seed = int(_derived_seed(seed, pair, index, f"referee|{seat}"), 16)

        def bot_seed_for(name, round_number):
            return _derived_seed(seed, pair, index,
                                 f"bot|{seat}|{name}|{round_number}")

        game = play_game(o, x, timeout, coin_seed, bot_seed_for,
                         move_provider=move_provider, game_id=game_id)
        game["pair_index"] = index
        return game

    tasks = [(first, second, index, o, x)
             for first, second in combinations(bots, 2)
             for index in range(paired_rounds)
             for o, x in ((first, second), (second, first))]
    if workers > 1:
        # Games are independent: each derives its own seeds, so results do not
        # depend on execution order. Parallelism only changes wall-clock time.
        with ThreadPoolExecutor(max_workers=workers) as executor:
            games = list(executor.map(play_task, tasks))
    else:
        games = [play_task(task) for task in tasks]
    games.sort(key=lambda game: game["game_id"])
    return {
        "rules": "simultaneous-coin-v2",
        "scoring": SCORING,
        "timeout_seconds": timeout,
        "paired_rounds": paired_rounds,
        "workers": workers,
        "band_half_width": band_half_width(2 * paired_rounds * (len(names) - 1)),
        "tournament_seed": seed,
        "games": games,
        "standings": standings_for(names, games, paired_rounds, quality),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--timeout", type=float, default=DEFAULT_TIMEOUT)
    parser.add_argument("--paired-rounds", type=int, default=DEFAULT_PAIRED_ROUNDS)
    parser.add_argument("--workers", type=int, default=DEFAULT_WORKERS,
                        help="games played in parallel (raise on a many-core judge)")
    parser.add_argument("--seed", help="optional repeatable local seed, e.g. demo")
    parser.add_argument("--quality", type=Path, help="JSON scorecard, 0–20 human-assessed points")
    parser.add_argument("--rescore", type=Path,
                        help="apply quality scores to saved results without rerunning bots")
    parser.add_argument("--log", type=Path, default=BASE / "tournament-results.json")
    args = parser.parse_args()
    if not math.isfinite(args.timeout) or args.timeout <= 0:
        parser.error("--timeout must be a positive finite number")
    if args.paired_rounds <= 0:
        parser.error("--paired-rounds must be positive")
    if args.workers <= 0:
        parser.error("--workers must be positive")
    try:
        quality = json.loads(args.quality.read_text(encoding="utf-8")) if args.quality else None
        if args.rescore:
            if quality is None:
                parser.error("--rescore requires --quality")
            if args.log.resolve() == args.rescore.resolve():
                parser.error("--log must differ from the existing results file")
            results = json.loads(args.rescore.read_text(encoding="utf-8"))
            if results.get("rules") != "simultaneous-coin-v2":
                raise ValueError("results use another game version")
            names = [row["name"] for row in results["standings"]]
            results["standings"] = standings_for(
                names, results["games"], results["paired_rounds"], quality)
        else:
            # The CLI is a local student tester. Official entry selection uses
            # an organizer-only hashed roster, not this folder/glob.
            bots = sorted((BASE / "bots").glob("*.py"))
            if len(bots) < 2:
                parser.error("the bots directory needs at least two .py files")
            print("Local tester only: do not judge untrusted submissions with this command.")
            results = run_tournament(bots, args.timeout, args.paired_rounds, args.seed,
                                     quality, workers=args.workers)
    except (OSError, RuntimeError, ValueError, KeyError, TypeError) as error:
        parser.error(str(error))
    for game in results["games"]:
        outcome = game["winner"] or "draw"
        print(f"{game['first']} (O) vs {game['second']} (X): {outcome} "
              f"({game['reason']}; {game['round_count']} rounds)")
    print(f"\nBand half-width = {results['band_half_width']:.3f} points/game "
          f"(bots within a band are statistically tied; quality orders them)")
    print("Rank  Band  Bot                      Points   W  D  L  Forf   Perf   Quality/20")
    for entry in results["standings"]:
        quality_display = (str(entry["quality_score"]) if entry["quality_score"] is not None
                           else "-")
        print(f"{entry['rank']:>4}  {entry['band']:>4}  {entry['name']:<24} "
              f"{entry['points']:>6.1f}  {entry['wins']:>1}  {entry['draws']:>1}  "
              f"{entry['losses']:>1}  {entry['forfeits']:>4}  {entry['performance']:>5.3f}  "
              f"{quality_display:>10}")
    args.log.write_text(json.dumps(results, indent=2) + "\n", encoding="utf-8")
    print(f"Referee seed (keep private until results are final): {results['tournament_seed']}")
    print(f"Full round and coin logs: {args.log}")


if __name__ == "__main__":
    main()
