import heapq

def a_star(start, goal, environment, robot_positions=None, path_cache=None):
    try:
        if not (environment.is_valid_position(*start) and environment.is_valid_position(*goal)):
            print(f"Invalid start {start} or goal {goal}")
            return None
        if start == goal:
            return []

        cache_key = (start, goal)
        if path_cache is not None and cache_key in path_cache:
            return path_cache[cache_key]

        def heuristic(a, b):
            return ((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2) ** 0.5

        frontier = []
        heapq.heappush(frontier, (0, start))
        came_from = {start: None}
        cost_so_far = {start: 0}

        directions = [(0, 1), (0, -1), (1, 0), (-1, 0), (1, 1), (1, -1), (-1, 1), (-1, -1)]
        move_costs = {tuple(d): 1.414 if d[0] != 0 and d[1] != 0 else 1 for d in directions}

        while frontier:
            _, current = heapq.heappop(frontier)
            if current == goal:
                break
            for dx, dy in directions:
                next_pos = (current[0] + dx, current[1] + dy)
                if (environment.is_valid_position(*next_pos) and
                    (robot_positions is None or next_pos not in robot_positions)):
                    new_cost = cost_so_far[current] + move_costs[(dx, dy)]
                    if next_pos not in cost_so_far or new_cost < cost_so_far[next_pos]:
                        cost_so_far[next_pos] = new_cost
                        priority = new_cost + heuristic(next_pos, goal)
                        heapq.heappush(frontier, (priority, next_pos))
                        came_from[next_pos] = current

        if goal not in came_from:
            print(f"No path found from {start} to {goal}")
            return None

        path = []
        current = goal
        while current != start:
            path.append(current)
            current = came_from[current]
        path.reverse()

        if path_cache is not None:
            path_cache[cache_key] = path

        return path
    except Exception as e:
        print(f"Error in a_star: {e}")
        return None