class Action:
    """Choose one square empty at the START of this simultaneous round (0–8)."""

    def __init__(self, move: int) -> None:
        self.move = move
