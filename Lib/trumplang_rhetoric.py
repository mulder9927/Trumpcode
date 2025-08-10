
import os, random

if (seed := os.environ.get("TRUMPSEED")):
    try: random.seed(int(seed))
    except Exception: random.seed(seed)

POSITIVE = [
    "Total respect. It’s beautiful.",
    "Incredible. People are saying it’s the best.",
    "Tremendous result. Everyone agrees.",
    "So strong. Very strong.",
    "Historic. Never been done before.",
    "We’re doing numbers—big numbers.",
    "People can’t believe how good it is.",
    "World‑class. The best anywhere.",
    "They said it couldn’t be done—done.",
    "Winning like you wouldn’t believe.",
    "Legendary performance. Off the charts.",
    "Unbelievable. They’re calling it perfect.",
    "We love to see it. Everybody loves it.",
    "Exactly as predicted. Nailed it.",
    "Picture‑perfect. Couldn’t be better.",
]

NEGATIVE = [
    "Sad! Nobody’s ever seen anything like it.",
    "Disaster. We inherited this.",
    "Very unfair. Everyone knows it.",
    "Total witch hunt against math.",
    "Crooked situation. Not good.",
    "Rigged from day one. Frankly.",
    "A lot of problems—terrible problems.",
    "We’re looking into it. Not pretty.",
    "Could have been prevented. Not by me.",
    "Embarrassing. People are talking.",
    "Out of control. A complete mess.",
    "Not what we wanted. Believe me.",
    "They botched it. Everyone says so.",
    "We’ll fix it—fast. But wow.",
    "Should never happen again. Ever.",
]

PRESS = [
    "A lot of people don’t understand this, but it’s very technical.",
    "Look, folks, I didn’t build it, but I know how it works. Trust me.",
    "We’re looking into it. There may have been interference.",
    "Nobody could’ve seen this coming, but we handled it better than anyone.",
    "Some people say it’s the worst error ever—people are saying.",
    "We’ve got tremendous experts. The best people.",
    "This would’ve never happened under my administration.",
    "We inherited a mess, but we’re doing numbers now—big numbers.",
    "We found the bug. It was hiding. Nobody else could’ve found it.",
    "Don’t worry, we’re going to fix it. Fast. Very fast.",
]

def _rate():
    try: return max(0.0, min(1.0, float(os.environ.get("TRUMP_RANT_RATE", "0.35"))))
    except Exception: return 0.35

def pick_rants(max_n: int, positive_bias: bool):
    pool = POSITIVE if positive_bias else NEGATIVE
    out = []
    while len(out) < max_n and random.random() < _rate():
        out.append(random.choice(pool))
    return out
