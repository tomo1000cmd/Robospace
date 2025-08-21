import time
import math
from pathfinding import a_star

class Agent:
    def __init__(self, name, channel):
        self.name = name
        self.channel = channel
    def process(self, messages):
        raise NotImplementedError

class VehicleOperatingAgent(Agent):
    def __init__(self, name, channel, robot_id, robot_instance, app=None):
        super().__init__(name, channel)
        self.robot_id = robot_id
        self.robot = robot_instance
        self.app = app
        self.status = "idle"
        self.motion_status = "stopped"
        self.move_timer = 0
        self.move_interval = 0.2
        self.path = []
        self.mode = "autonomous"
        self.current_task_id = None
        self.distance_traveled = 0  # Track total distance traveled

    def process(self, messages):
        if self.motion_status == "moving" and self.path and time.time() - self.move_timer > self.move_interval:
            self.move_timer = time.time()
            self.move_along_path()

        for msg in messages:
            if msg.get('to') == self.robot_id:
                command = msg.get('command')
                if command == "go_to" and self.status == 'idle':
                    self.execute_go_to(msg, messages)
                elif command == "cover_room" and self.status == 'idle':
                    self.execute_cover_room(msg, messages)
                elif command == "cover_multi_rooms" and self.status == 'idle':
                    self.execute_cover_multi_rooms(msg, messages)
                elif command == "stop":
                    self.stop_all_actions()
                elif command == "start":
                    if self.path: self.motion_status = "moving"

        self.channel.publish({
            "from": self.robot_id, "type": "status", "status": self.status,
            "motion": self.motion_status, "pos": (self.robot.x, self.robot.y), 
            "path": self.path, "distance_traveled": self.distance_traveled
        })

    def execute_go_to(self, msg, messages):
        target_pos = msg.get('pos')
        dynamic_obs = self.get_dynamic_obstacles(messages)
        path = self.app.a_star((self.robot.x, self.robot.y), target_pos, self.robot.environment,
                               extra_obstacles=dynamic_obs, path_cache=self.app.path_cache)
        if path:
            self.path = path
            self.motion_status = "moving"
            self.status = "navigating"
            self.current_task_id = msg.get('task_id')

    def execute_cover_room(self, msg, messages):
        self.current_task_id = msg.get('task_id')
        room_center = msg.get('room_center')
        room = next((r for r in self.robot.environment.rooms if r['center'] == room_center), None)
        if not room: return

        self.status = "covering"
        coverage_path = self.app.generate_coverage_path(room['bounds'])
        if not coverage_path:
            self.status = 'idle'
            return

        dynamic_obs = self.get_dynamic_obstacles(messages)
        path_to_room = self.app.a_star((self.robot.x, self.robot.y), coverage_path[0], self.robot.environment,
                                       extra_obstacles=dynamic_obs, path_cache=self.app.path_cache)

        if path_to_room:
            self.path = path_to_room + coverage_path
            self.motion_status = "moving"
        else:
            self.status = "idle"

    def execute_cover_multi_rooms(self, msg, messages):
        self.current_task_id = msg.get('task_id')
        room_centers = msg.get('room_centers')
        if not room_centers: return

        self.status = "covering"
        full_path = []
        current_pos = (self.robot.x, self.robot.y)
        dynamic_obs = self.get_dynamic_obstacles(messages)

        for center in room_centers:
            room = next((r for r in self.robot.environment.rooms if r['center'] == center), None)
            if not room: continue
            coverage_path = self.app.generate_coverage_path(room['bounds'])
            if not coverage_path: continue

            path_to_room = self.app.a_star(current_pos, coverage_path[0], self.robot.environment,
                                           extra_obstacles=dynamic_obs, path_cache=self.app.path_cache)
            if path_to_room:
                full_path.extend(path_to_room + coverage_path)
                current_pos = coverage_path[-1]

        if full_path:
            self.path = full_path
            self.motion_status = "moving"
        else:
            self.status = "idle"

    def move_along_path(self):
        if self.path:
            prev_pos = (self.robot.x, self.robot.y)
            next_pos = self.path.pop(0)
            self.robot.x, self.robot.y = next_pos
            self.robot.visited.add(next_pos)
            # Calculate distance traveled (1 for cardinal, 1.414 for diagonal)
            dx, dy = next_pos[0] - prev_pos[0], next_pos[1] - prev_pos[1]
            distance = 1.414 if dx != 0 and dy != 0 else 1
            self.distance_traveled += distance
            total = len(self.robot.environment.cleanable)
            percent = int(len(self.robot.visited) / total * 100) if total > 0 else 0
            self.robot.special_stat = f"Coverage: {percent}%"

        if not self.path:
            self.motion_status = "stopped"
            if self.status != "idle":
                self.status = "idle"
                if self.current_task_id:
                    self.channel.publish({"type": "task_completed", "task_id": self.current_task_id, "robot_id": self.robot_id})
                    self.current_task_id = None

    def stop_all_actions(self):
        self.motion_status = "stopped"
        if self.status != "idle":
            self.status = "idle"
            if self.current_task_id:
                self.channel.publish({"type": "task_completed", "task_id": self.current_task_id, "robot_id": self.robot_id})
                self.current_task_id = None
        self.path = []

    def get_dynamic_obstacles(self, messages):
        dynamic_obs = set()
        for msg in messages:
            if msg.get('type') == "status" and msg.get('from') != self.robot_id:
                pos = msg['pos']
                for dx in [-1, 0, 1]:
                    for dy in [-1, 0, 1]:
                        dynamic_obs.add((pos[0] + dx, pos[1] + dy))
        return dynamic_obs

class MonitoringLoggingAgent(Agent):
    def __init__(self, name, channel, robot_id):
        super().__init__(name, channel)
        self.robot_id = robot_id
        self.logs = []
        self.task_history = []  # Track completed tasks
        self.log_limit = 5
        self.task_limit = 5

    def process(self, messages):
        for msg in messages:
            if msg.get('to') == self.robot_id and msg.get('command'):
                log_entry = f"{time.strftime('%H:%M:%S')} - Cmd: {msg['command']}"
                self.logs.append(log_entry)
            if msg.get('type') == "task_completed" and msg.get('robot_id') == self.robot_id:
                task_entry = f"{time.strftime('%H:%M:%S')} - Completed: {msg['task_id']}"
                self.task_history.append(task_entry)
        if len(self.logs) > self.log_limit:
            self.logs = self.logs[-self.log_limit:]
        if len(self.task_history) > self.task_limit:
            self.task_history = self.task_history[-self.task_limit:]

class ConfigurationAgent(Agent):
    def __init__(self, name, channel):
        super().__init__(name, channel)
        self.config = {"team_size": 2, "mission": "cover_rooms", "comms": "broadcast"}
    def process(self, messages): pass

class CooperativeAgent(Agent):
    def __init__(self, name, channel, app=None):
        super().__init__(name, channel)
        self.app = app
        self.robot_paths = {}  # Store paths of all robots

    def process(self, messages):
        # Update robot paths from status messages
        for msg in messages:
            if msg.get('type') == "status":
                robot_id = msg.get('from')
                self.robot_paths[robot_id] = msg.get('path', [])

        # Check for potential collisions and adjust paths
        for msg in messages:
            if msg.get('type') == "status":
                robot_id = msg.get('from')
                current_path = self.robot_paths.get(robot_id, [])
                if not current_path:
                    continue
                for other_id, other_path in self.robot_paths.items():
                    if other_id == robot_id or not other_path:
                        continue
                    # Check for path conflicts (same position at same step)
                    for i, (pos1, pos2) in enumerate(zip(current_path, other_path)):
                        if pos1 == pos2:
                            # Replan path for this robot to avoid collision
                            self.replan_path(robot_id, pos1, messages)
                            break

    def replan_path(self, robot_id, conflict_pos, messages):
        # Find the robot's current position and target
        for msg in messages:
            if msg.get('type') == "status" and msg.get('from') == robot_id:
                current_pos = msg.get('pos')
                target_pos = self.robot_paths[robot_id][-1] if self.robot_paths[robot_id] else current_pos
                # Create dynamic obstacles excluding the conflicting position
                dynamic_obs = set()
                for other_id, path in self.robot_paths.items():
                    if other_id != robot_id:
                        for pos in path:
                            if pos != conflict_pos:
                                dynamic_obs.add(pos)
                # Replan path
                new_path = a_star(current_pos, target_pos, self.app.robots[robot_id].environment,
                                 extra_obstacles=dynamic_obs, path_cache=self.app.path_cache)
                if new_path:
                    self.channel.publish({
                        "to": robot_id,
                        "command": "go_to",
                        "pos": target_pos,
                        "path": new_path
                    })
                break

class ForecastingAgent(Agent):
    def __init__(self, name, channel, app=None):
        super().__init__(name, channel)
        self.app = app
        self.robot_positions = {}
        self.task_estimates = {}  # task_id: estimated_completion_time

    def process(self, messages):
        # Update robot positions
        for msg in messages:
            if msg.get('type') == "status":
                self.robot_positions[msg.get('from')] = msg.get('pos')

        # Estimate task completion times and prioritize
        for msg in messages:
            if msg.get('to') and msg.get('command') in ["cover_room", "cover_multi_rooms"]:
                task_id = msg.get('task_id')
                robot_id = msg.get('to')
                room_centers = msg.get('room_centers', [msg.get('room_center')]) if msg.get('command') == "cover_multi_rooms" else [msg.get('room_center')]
                if not room_centers:
                    continue
                # Estimate time based on distance to room and coverage area
                total_time = 0
                current_pos = self.robot_positions.get(robot_id, (0, 0))
                for center in room_centers:
                    room = next((r for r in self.app.robots[robot_id].environment.rooms if r['center'] == center), None)
                    if not room:
                        continue
                    bounds = room['bounds']
                    x1, y1, x2, y2 = bounds
                    area = (x2 - x1) * (y2 - y1)
                    distance = math.sqrt((current_pos[0] - center[0])**2 + (current_pos[1] - center[1])**2)
                    # Assume 0.2s per cell movement, 1 cell/s for coverage
                    total_time += distance * 0.2 + area
                    current_pos = center
                self.task_estimates[task_id] = total_time

                # If task is too long (>100s), suggest splitting for multi-room tasks
                if msg.get('command') == "cover_multi_rooms" and total_time > 100 and len(room_centers) > 1:
                    self.channel.publish({
                        "to": robot_id,
                        "command": "cover_room",
                        "task_id": f"split_{task_id}",
                        "room_center": room_centers[0]
                    })
                    self.channel.publish({
                        "to": robot_id,
                        "command": "cover_multi_rooms",
                        "task_id": f"remaining_{task_id}",
                        "room_centers": room_centers[1:]
                    })