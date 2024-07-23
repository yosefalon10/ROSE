"""
This driver does not do any action.
"""
from rose.common import obstacles, actions  # NOQA

driver_name = "yosef"


def evaluate_action(obstacle, action):
    if obstacle == obstacles.NONE:
        return 10 if action == actions.NONE else 0
    elif obstacle == obstacles.PENGUIN:
        return 10 if action == actions.NONE else 0  # No PICKUP action
    elif obstacle == obstacles.WATER:
        return 4 if action == actions.BRAKE else -10
    elif obstacle == obstacles.CRACK:
        return 5 if action == actions.JUMP else -10
    elif obstacle in [obstacles.TRASH, obstacles.BIKE, obstacles.BARRIER]:
        return 0 if action in [actions.LEFT, actions.RIGHT] else -10
    return -10


# Simulate the move without modifying the original world object
def simulate_move(x, y, action):
    if action == actions.LEFT:
        x -= 1
    elif action == actions.RIGHT:
        x += 1
    elif action != actions.NONE:
        y -= 1
    return x, y


# Minimax algorithm to determine the best action
def minimax(world, x, y, depth, maximizing_player):
    # Terminal condition for recursion
    if depth == 0:
        try:
            obstacle = world.get((x, y - 1))
            print(f"Terminal condition: obstacle at ({x}, {y - 1}) is {obstacle}")
        except IndexError:
            obstacle = obstacles.NONE
        return evaluate_action(obstacle, actions.NONE)

    if maximizing_player:
        max_eval = float('-inf')
        for action in [actions.NONE, actions.BRAKE, actions.JUMP, actions.LEFT, actions.RIGHT]:
            try:
                new_x, new_y = simulate_move(x, y, action)
                obstacle = world.get((new_x, new_y - 1))
                print(f"Maximizing: obstacle at ({new_x}, {new_y - 1}) is {obstacle} for action {action}")
            except IndexError:
                obstacle = obstacles.NONE
            eval = evaluate_action(obstacle, action)
            print(f"Evaluation score for action {action}: {eval}")
            max_eval = max(max_eval, eval + minimax(world, new_x, new_y, depth - 1, False))
            print(f"Current max evaluation: {max_eval}")
        return max_eval
    else:
        min_eval = float('inf')
        for action in [actions.NONE, actions.BRAKE, actions.JUMP, actions.LEFT, actions.RIGHT]:
            try:
                new_x, new_y = simulate_move(x, y, action)
                obstacle = world.get((new_x, new_y - 1))
                print(f"Minimizing: obstacle at ({new_x}, {new_y - 1}) is {obstacle} for action {action}")
            except IndexError:
                obstacle = obstacles.NONE
            eval = evaluate_action(obstacle, action)
            print(f"Evaluation score for action {action}: {eval}")
            min_eval = min(min_eval, eval + minimax(world, new_x, new_y, depth - 1, True))
            print(f"Current min evaluation: {min_eval}")
        return min_eval


def return_direction_when_barrier(x, y, world):
    if x == 0 or x == 3:
        return actions.RIGHT
    if x == 2 or x == 5:
        return actions.LEFT
    rightobstacle = world.get((x + 1, y - 2))
    leftobstacle = world.get((x - 1, y - 2))
    if rightobstacle == obstacles.PENGUIN:
        return actions.RIGHT
    if leftobstacle == obstacles.PENGUIN:
        return actions.LEFT
    if rightobstacle == obstacles.CRACK:
        return actions.RIGHT
    if leftobstacle == obstacles.CRACK:
        return actions.LEFT
    if rightobstacle == obstacles.WATER:
        return actions.RIGHT
    if leftobstacle == obstacles.WATER:
        return actions.LEFT
    return actions.LEFT


def find_place_none(x, y, world):
    if x == 0 or x == 3:
        rightobstacle = world.get((x + 1, y - 2))
        if rightobstacle == obstacles.PENGUIN or rightobstacle == obstacles.CRACK or rightobstacle == obstacles.WATER:
            return actions.RIGHT
        return actions.NONE
    else:
        if x == 2 or x == 5:
            leftobstacle = world.get((x - 1, y - 2))
            if leftobstacle == obstacles.PENGUIN or leftobstacle == obstacles.CRACK or leftobstacle == obstacles.WATER:
                return actions.LEFT
            return actions.NONE
        else:
            rightobstacle = world.get((x + 1, y - 2))
            leftobstacle = world.get((x - 1, y - 2))
            if rightobstacle == obstacles.PENGUIN:
                return actions.RIGHT
            if leftobstacle == obstacles.PENGUIN:
                return actions.LEFT
            if rightobstacle == obstacles.CRACK:
                return actions.RIGHT
            if leftobstacle == obstacles.CRACK:
                return actions.LEFT
            if rightobstacle == obstacles.WATER:
                return actions.RIGHT
            if leftobstacle == obstacles.WATER:
                return actions.LEFT
            return actions.NONE


def drive(world):
    x = world.car.x
    y = world.car.y
    obstacle = world.get((x, y - 1))

    if obstacle == obstacles.PENGUIN:
        return actions.PICKUP
    if obstacle == obstacles.WATER:
        return actions.BRAKE
    if obstacle == obstacles.CRACK:
        return actions.JUMP
    if obstacle == obstacles.TRASH or obstacle == obstacles.BIKE or obstacle == obstacles.BARRIER:
        return return_direction_when_barrier(x, y, world)
    if obstacle == obstacles.NONE:
        return find_place_none(x, y, world)

    # If no specific action, use Minimax to determine the best action
    best_action = actions.NONE
    best_score = float('-inf')

    # Check each possible action and choose the one with the highest Minimax score
    for action in [actions.NONE, actions.BRAKE, actions.JUMP, actions.LEFT, actions.RIGHT]:
        try:
            new_x, new_y = simulate_move(x, y, action)
            obstacle = world.get((new_x, new_y - 1))
            print(f"Driving: obstacle at ({new_x}, {new_y - 1}) is {obstacle} for action {action}")
        except IndexError:
            obstacle = obstacles.NONE
        score = evaluate_action(obstacle, action) + minimax(world, new_x, new_y, 3, False)  # Depth of 3 for lookahead
        print(f"Total score for action {action}: {score}")
        if score > best_score:
            best_score = score
            best_action = action

    print(f"Best action decided: {best_action} with score {best_score}")
    return best_action
