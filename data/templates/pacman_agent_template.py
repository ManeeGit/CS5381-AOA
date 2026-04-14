from game import Directions
import random


class MyAgent:
    def getAction(self, state):
        legal = state.getLegalActions()
        if not legal:
            return Directions.STOP
        return random.choice(legal)
