import time
import math

class Task:
    def __init__(self, task_id, task_type, location):
        self.task_id = task_id
        self.type = task_type
        self.location = location

class TaskManager:
    def __init__(self, channel, robot_ids, room_centers):
        self.channel = channel
        self.robot_ids = robot_ids
        self.room_centers = room_centers
        self.robot_status = {robot_id: "idle" for robot_id in robot_ids}
        self.robot_positions = {robot_id: (0, 0) for robot_id in robot_ids}
        self.assigned_rooms = {}  # room_center: robot_id

    def process(self, messages):
        self.update_robot_states(messages)
        self.assign_new_tasks()

    def update_robot_states(self, messages):
        for msg in messages:
            if msg.get('type') == "status":
                robot_id = msg.get('from')
                if robot_id in self.robot_ids:
                    self.robot_positions[robot_id] = msg.get('pos')
                    if msg.get('status') == 'idle' and self.robot_status[robot_id] == 'busy':
                        self.robot_status[robot_id] = 'idle'
                        # Free up the room associated with this robot
                        for room, r_id in list(self.assigned_rooms.items()):
                            if r_id == robot_id:
                                del self.assigned_rooms[room]
                                print(f"[TaskManager] Robot {robot_id} is idle. Room at {room} is now free.")
            
            elif msg.get('type') == 'task_completed':
                robot_id = msg.get('robot_id')
                if robot_id in self.robot_ids:
                    self.robot_status[robot_id] = "idle"


    def assign_new_tasks(self):
        available_rooms = [room for room in self.room_centers if room not in self.assigned_rooms]
        idle_robots = [rid for rid, status in self.robot_status.items() if status == 'idle']

        if not available_rooms or not idle_robots:
            return

        for robot_id in idle_robots:
            if not available_rooms: break

            robot_pos = self.robot_positions[robot_id]
            closest_room = min(available_rooms, key=lambda room: math.sqrt((room[0] - robot_pos[0])**2 + (room[1] - robot_pos[1])**2))
            
            available_rooms.remove(closest_room)
            self.assigned_rooms[closest_room] = robot_id
            self.robot_status[robot_id] = 'busy'
            
            task_id = f"task_{int(time.time())}_{robot_id}"
            
            self.channel.publish({
                "to": robot_id,
                "command": "cover_room",
                "task_id": task_id,
                "room_center": closest_room
            })
            print(f"[TaskManager] Assigned task {task_id} (Cover room at {closest_room}) to Robot {robot_id}")