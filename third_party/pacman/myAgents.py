from game import Directions
import random

class MyAgent:
    def __init__(self):
        self.score = 0
        self.steps = 0

    def getAction(self, state):
        legal = state.getLegalActions()
        if not legal:
            return Directions.STOP
        best_action = None
        max_score = -float('inf')
        for action in legal:
            new_state = state.generateSuccessor(action)
            score = self.calculate_score(new_state)
            if score > max_score:
                max_score = score
                best_action = action
        self.steps += 1
        return best_action

    def calculate_score(self, state):
        # Implement your scoring logic here based on the game's rules
        # For example, you could count the number of pellets eaten or avoid obstacles
        pass