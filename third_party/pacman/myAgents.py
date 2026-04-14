from game import Directions

class MyAgent:
    def __init__(self):
        self.score = 0
        self.steps = 1

    def getAction(self, state):
        legal = state.getLegalActions()
        if not legal:
            return Directions.STOP
        
        # Use a heuristic to guide movement towards the goal
        next_move = self.choose_next_move(state)
        
        return next_move

    def evaluate_successor(self, successor_state):
        score = successor_state.getScore()
        food_count = len(successor_state.getFood())
        ghost_positions = successor_state.getGhostPositions()
        num_ghosts = len(ghost_positions)
        
        # Add more complex logic to maximize score and survival while minimizing steps
        # For example:
        # 1. Move towards the closest food if available
        # 2. Avoid ghosts by moving away from them
        # 3. Use a heuristic to guide movement towards the goal
        
        return random.choice(legal)

    def choose_next_move(self, state):
        # Implement a more complex heuristic here
        # For example:
        # 1. Calculate the distance to the nearest food
        # 2. Avoid ghosts by moving away from them
        # 3. Use a weighted combination of these factors
        
        # Placeholder: Move towards the nearest food if available
        food_positions = state.getFood().asList()
        if food_positions:
            next_move = min(food_positions, key=lambda pos: state.distTo(pos))
        else:
            next_move = Directions.STOP
        
        return next_move