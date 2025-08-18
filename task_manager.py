import time
import random
import math

class Task:
    def __init__(self, task_id, task_type=None, type=None, location=None, duration=0, priority=1, target_robot=None, status="pending"):
        self.task_id = task_id
        self.type = task_type or type  # Accept 'type' as a fallback for 'task_type'
        self.location = location  # (x, y) tuple or None
        self.duration = duration  # Seconds to wait
        self.priority = priority  # Higher value = higher priority
        self.target_robot = target_robot  # Robot ID to take over, if applicable
        self.status = status  # Add status as a constructor parameter

    def __lt__(self, other):
        return self.priority > other.priority  # Higher priority first

    def to_dict(self):
        """Convert Task to a dictionary with consistent keys."""
        return {
            "task_id": self.task_id,
            "task_type": self.type,
            "location": self.location,
            "duration": self.duration,
            "priority": self.priority,
            "target_robot": self.target_robot,
            "status": self.status
        }

class TaskManager:
    def __init__(self, channel, robot_ids, room_centers):
        self.channel = channel
        self.robot_ids = robot_ids
        self.room_centers = room_centers  # List of (x, y) tuples from Environment
        self.task_queues = {robot_id: [] for robot_id in robot_ids}
        self.active_tasks = {}  # task_id: (robot_id, start_time)
        self.assigned_rooms = {}  # robot_id: room_center
        self.robot_positions = {robot_id: (0, 0) for robot_id in robot_ids}  # Initialize with (0, 0)
        self.last_task_time = 0
        self.task_interval = random.uniform(3.0, 5.0)  # Random delay between 3-5 seconds
        self.last_process_time = 0  # Track last process call to enforce delay

    def update_robot_positions(self, messages):
        """Update robot positions based on status messages."""
        for msg in messages:
            if msg.get('type') == "status":
                robot_id = msg.get('from')
                pos = msg.get('pos')
                if robot_id in self.robot_ids and pos:
                    self.robot_positions[robot_id] = pos

    def calculate_distance(self, pos1, pos2):
        """Calculate Euclidean distance between two positions, handling None."""
        if pos1 is None or pos2 is None:
            return float('inf')  # Return infinity if either position is None
        return math.sqrt((pos2[0] - pos1[0])**2 + (pos2[1] - pos1[1])**2)

    def generate_task(self):
        """Generate a unique task for each robot, avoiding same room assignments."""
        current_time = time.time()
        if current_time - self.last_task_time < self.task_interval:
            return None
        self.last_task_time = current_time

        available_rooms = self.room_centers.copy()
        for robot_id in self.robot_ids:
            if robot_id in self.assigned_rooms:
                if self.assigned_rooms[robot_id] in available_rooms:
                    available_rooms.remove(self.assigned_rooms[robot_id])

        if not available_rooms:
            available_rooms = self.room_centers  # Reset if all rooms are assigned

        tasks = []
        for robot_id in self.robot_ids:
            if not available_rooms:
                break
            current_pos = self.robot_positions.get(robot_id, (0, 0))
            # Prioritize rooms farther from current position to reduce traffic
            best_room = min(available_rooms, key=lambda room: self.calculate_distance(current_pos, room), default=available_rooms[0])
            task_type = random.choice(["move", "wait", "take_over"])
            duration = 2.0 if task_type == "wait" else 0
            priority = random.randint(1, 5)
            target_robot = random.choice(self.robot_ids) if task_type == "take_over" else None
            task_id = f"task_{int(current_time)}_{robot_id}"
            task = Task(task_id, task_type=task_type, location=best_room, duration=duration, priority=priority, target_robot=target_robot)
            tasks.append((robot_id, task))
            self.assigned_rooms[robot_id] = best_room
            available_rooms.remove(best_room)

        return tasks if tasks else None

    def assign_task(self, robot_id, task):
        """Assign a task to a specific robot."""
        if not task or task.status != "pending":
            return
        self.task_queues[robot_id].append(task)
        task.status = "assigned"
        self.channel.publish({"to": robot_id, "command": "new_task", "task": task.to_dict()})
        print(f"Assigned {task.type} task {task.task_id} to Robot {robot_id}")

    def process(self, messages):
        """Process task updates and manage task execution with enforced delay."""
        current_time = time.time()
        if current_time - self.last_process_time < 0.5:  # Minimum 0.5s between process calls
            return
        self.last_process_time = current_time

        self.update_robot_positions(messages)  # Update robot positions first
        for msg in messages:
            if msg.get('type') == "task_status":
                task_id = msg.get('task_id')
                status = msg.get('status')
                if task_id in self.active_tasks:
                    robot_id, _ = self.active_tasks[task_id]
                    if status == "completed":
                        del self.active_tasks[task_id]
                        self.task_queues[robot_id] = [t for t in self.task_queues[robot_id] if t.task_id != task_id]
                        if robot_id in self.assigned_rooms:
                            del self.assigned_rooms[robot_id]  # Free up the room
                        print(f"Task {task_id} completed by Robot {robot_id}")

        # Generate and assign new tasks with delay
        new_tasks = self.generate_task()
        if new_tasks:
            for robot_id, task in new_tasks:
                self.assign_task(robot_id, task)
                time.sleep(random.uniform(0.1, 0.5))  # Small delay between individual assignments

        # Check active tasks for completion or handoff
        for task_id, (robot_id, start_time) in list(self.active_tasks.items()):
            task = next((t for t in self.task_queues[robot_id] if t.task_id == task_id), None)
            if not task:
                continue
            if task.type == "wait" and current_time - start_time >= task.duration:
                task.status = "completed"
                self.channel.publish({"to": robot_id, "command": "task_update", "task_id": task_id, "status": "completed"})
            elif task.type == "take_over" and current_time - start_time >= 2.0:
                target_robot = task.target_robot
                if target_robot != robot_id and target_robot in self.robot_ids:
                    self.task_queues[target_robot].append(task)
                    self.channel.publish({"to": target_robot, "command": "new_task", "task": task.to_dict()})
                    self.task_queues[robot_id] = [t for t in self.task_queues[robot_id] if t.task_id != task_id]
                    del self.active_tasks[task_id]
                    print(f"Robot {robot_id} handed off {task_id} to Robot {target_robot}")

    def start_task(self, robot_id, task):
        """Start executing a task for a robot."""
        if task and task.status == "assigned":
            task.status = "in_progress"
            self.active_tasks[task.task_id] = (robot_id, time.time())
            if task.type == "move":
                self.channel.publish({"to": robot_id, "command": "go_to", "pos": task.location})
            elif task.type == "wait":
                self.channel.publish({"to": robot_id, "command": "wait", "duration": task.duration})
            elif task.type == "take_over":
                self.channel.publish({"to": robot_id, "command": "move_to_take_over", "pos": task.location})
            print(f"Robot {robot_id} started {task.type} task {task.task_id}")

if __name__ == "__main__":
    class MockChannel:
        def __init__(self):
            self.messages = []
        def publish(self, msg):
            self.messages.append(msg)
        def get_and_clear_messages(self):
            msgs = self.messages.copy()
            self.messages.clear()
            return msgs

    channel = MockChannel()
    mock_room_centers = [(5, 5), (15, 5), (25, 5), (5, 15), (15, 15), (25, 15), (5, 25), (35, 5), (35, 15), (30, 15), (35, 25)]
    task_manager = TaskManager(channel, [1, 2], mock_room_centers)
    for _ in range(5):
        task_manager.process([])
        for msg in channel.get_and_clear_messages():
            if msg.get('command') == "new_task":
                task_manager.start_task(msg['to'], Task(**msg['task']))
        time.sleep(1)