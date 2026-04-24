"""Pacman agent template — used as the evolution seed.

This is the starting point for all three modes (no_evolution, random_mutation,
llm_guided).  It is intentionally a simple greedy agent so that evolutionary
improvement is clearly visible.
"""
from game import Directions
import random


class MyAgent:
    """Greedy baseline agent: prefers score-increasing moves, avoids losing."""

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
        safe = [a for a in legal
                if not state.generatePacmanSuccessor(a).isLose()]
        if not safe:
            return random.choice(legal)

        # Among safe moves, prefer the one with the highest score gain
        best_score = float('-inf')
        best = []
        for action in safe:
            succ = state.generatePacmanSuccessor(action)
            gain = succ.getScore() - state.getScore()
            if gain > best_score:
                best_score = gain
                best = [action]
            elif gain == best_score:
                best.append(action)

        return random.choice(best)
