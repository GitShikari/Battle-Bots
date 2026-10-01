"""Protocol worker: run exactly one move in a fresh Python process."""

from contextlib import redirect_stderr, redirect_stdout
import importlib.util
import json
import os
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from GameState import GameState


def main():
    try:
        raw = sys.stdin.buffer.read(4097)
        if len(raw) > 4096:
            raise ValueError("move request is too large")
        request = json.loads(raw)
        view = GameState()
        view.pieces = request["pieces"]
        view.round_number = request["round_number"]
        random.seed(int(request["bot_seed"], 16))

        # Python-level output from a contestant must not masquerade as our reply.
        with open(os.devnull, "w") as sink, redirect_stdout(sink), redirect_stderr(sink):
            spec = importlib.util.spec_from_file_location("contestant_bot", sys.argv[1])
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            player = module.Player(view)
            player.run()  # Thread-based examples call act(view) here.
            move = player.action.move
            if type(move) is not int:
                raise ValueError("action.move must be an integer square from 0 to 8")
        result = {"move": move}
    except BaseException as error:
        result = {"error": f"{type(error).__name__}: {error}"[:300]}
    print(json.dumps(result), flush=True)


if __name__ == "__main__":
    main()
