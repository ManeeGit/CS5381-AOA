from game import Directions
import random

class MyAgent:
    """Human-feedback Gen-1 agent: avoids ghosts and moves toward food."""

    def getAction(self, state):
        legal = state.getLegalActions()
        if not legal:
            return Directions.STOP

        # Win immediately if any successor is a win state
        for action in legal:
            succ = state.generatePacmanSuccessor(action)
            if succ.isWin():
                return action

        # Filter out immediately losing moves
        safe = [a for a in legal if not state.generatePacmanSuccessor(a).isLose()]
        if not safe:
            return random.choice(legal)

        # Among safe moves, prefer the one with the highest score gain and lowest steps
        best_score = float('-inf')
        best_steps = float('inf')
        best = []
        for action in safe:
            succ = state.generatePacmanSuccessor(action)
            gain = succ.getScore() - state.getScore()
            steps = len(succ.getFood().asList())
            if gain > best_score or (gain == best_score and steps < best_steps):
                best_score = gain
                best_steps = steps
                best = [action]
            elif gain == best_score and steps == best_steps:
                best.append(action)

        return random.choice(best)