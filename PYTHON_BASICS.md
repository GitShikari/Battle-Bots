# Python basics for Battle Bots

This page is for anyone who is new to Python (or new to classes). You only need
a little to take part. Everything here is illustrated by
[`example-bot.py`](example-bot.py), which you can copy and edit.

## Variables, lists, and indexing

```python
x = 5                      # a variable holds a value
row = [0, 0, 0]            # a list holds several values
print(row[0])              # indexing starts at 0, so this prints 0
print(len(row))            # len() is the number of items: 3
```

## Functions

A function is a reusable block of code.

```python
def double(n):
    return n * 2

print(double(4))           # 8
```

## Classes and objects (the part that confuses people)

A **class** is a *blueprint*. An **object** is one thing built from that
blueprint. Your bot is an object built from a class called `Player`.

```python
class Dog:
    def __init__(self, name):   # runs when the object is created
        self.name = name        # `self` is THIS dog
    def speak(self):
        return self.name + " says woof"

d = Dog("Rex")                  # creating the object runs __init__("Rex")
print(d.speak())                # "Rex says woof"
```

- `self` means "this particular object". Inside a class you write `self.name`
  to read or set this object's data.
- `__init__` (two underscores each side) is the setup method. It runs
  automatically when you write `Dog("Rex")`.
- A **method** is a function inside a class. It always takes `self` first when
  you define it, but you do **not** pass `self` when you call it: `d.speak()`.
- **Inheritance** is when one class builds on another, e.g.
  `class Player(Thread):`. You do not need it here: a plain `class Player:` with
  the methods below is all the runner asks for.

## The Player skeleton you must provide

```python
from Action import Action

class Player:
    def __init__(self, gamestate):
        self.gamestate = gamestate      # remember the board
        self.action = Action(-1)        # placeholder move

    def run(self):
        self.act(self.gamestate)        # the runner calls this

    def act(self, gamestate):
        empty = [i for i in range(9) if gamestate.pieces[i] == 0]
        self.action = Action(empty[0])  # replace with your choice
```

The runner creates `Player(gamestate)`, calls `run()`, and then reads
`self.action`. That is the whole interface.

## Handy building blocks

```python
[i for i in range(9) if board[i] == 0]   # list of empty squares
board.copy()                             # a copy you can safely edit
for i in range(9): ...                   # a loop
if x > y: ...                            # a condition
import random                            # standard library
random.choice(moves)                     # pick one at random
max(scores)                              # largest value
sorted(moves)                            # a sorted list
```

## Rules for your submission

- One file, named `teamname_bot.py`, defining `class Player`.
- Use only the Python standard library (no extra packages to install).
- Return a square from 0 to 8 that was empty at the start of the round.
- Finish within the time limit shown in the README, or the game is forfeited.

If in doubt, copy `example-bot.py`, run it, and change one thing at a time.
