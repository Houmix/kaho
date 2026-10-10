"""Programme complet des 10 thèmes ETG : leçons rédigées et banque de questions (voir curriculum_1 / curriculum_2)."""
import hashlib
import random

from .curriculum_1 import DATA as _D1
from .curriculum_2 import DATA as _D2

PROGRAMME = {**_D1, **_D2}


def shuffled_choices(text, choices, correct):
    """Mélange déterministe des propositions (la bonne réponse n'est pas toujours en première position)."""
    if [c.lower() for c in choices] == ['vrai', 'faux']:
        return list(zip(choices, [i in correct for i in range(2)]))
    order = list(range(len(choices)))
    random.Random(int(hashlib.md5(text.encode()).hexdigest(), 16)).shuffle(order)
    return [(choices[i], i in correct) for i in order]
