from game import Directions
import random

class MyAgent:
    def getAction(self, state):
        legal = state.getLegalActions()
        return random.choice(legal) if legal else Directions.STOP
