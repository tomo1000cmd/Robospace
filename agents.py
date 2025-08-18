import time
import random

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
        self.target_pos = None
        self.path = []
        self.autonomy_timer = 0
        self.autonomy_interval = 5.0
        self.mode = "manual"

    def autonomous_patrol(self, robot_positions=None, path_cache=None):
        try:
            if self.mode == "autonomous" and self.status == "idle" and self.motion_status == "stopped" and time.time() - self.autonomy_timer > self.autonomy_interval:
                self.autonomy_timer = time.time()
                if not hasattr(self, 'current_room_index'):
                    self.current_room_index = 0
                room_centers = [room['center'] for room in self.robot.environment.rooms]
                self.target_pos = room_centers[self.current_room_index]
                if (self.target_pos != (self.robot.x, self.robot.y) and
                    self.robot.environment.is_valid_position(*self.target_pos) and
                    (robot_positions is None or self.target_pos not in robot_positions)):
                    path = self.app.a_star((self.robot.x, self.robot.y), self.target_pos, self.robot.environment,
                                          robot_positions=robot_positions, path_cache=path_cache)
                    if path:
                        self.path = path
                        self.motion_status = "moving"
                        self.status = "patrolling"
                        self.robot.special_stat = f"{'Cleaned Area' if self.robot.type_label == 'Barn Cleaner' else 'Harvest Load'}: {random.randint(0, 100)}%"
                        self.current_room_index = (self.current_room_index + 1) % len(room_centers)
                    else:
                        self.target_pos = None
                        self.current_room_index = (self.current_room_index + 1) % len(room_centers)
                else:
                    self.target_pos = None
                    self.current_room_index = (self.current_room_index + 1) % len(room_centers)
        except Exception as e:
            print(f"Error in autonomous_patrol: {e}")

    def process(self, messages):
        try:
            current_time = time.time()
            if self.motion_status == "moving" and self.path and current_time - self.move_timer > self.move_interval:
                self.move_timer = current_time
                self.move_along_path()

            robot_positions = self.get_other_robot_positions(messages)
            if self.mode == "autonomous":
                self.autonomous_patrol(robot_positions=robot_positions, path_cache=self.app.path_cache)

            for msg in messages:
                if msg.get('to') == self.robot_id:
                    command = msg.get('command')
                    if command == "go_to":
                        self.target_pos = msg.get('pos')
                        robot_positions = msg.get('robot_positions', set())
                        if self.target_pos and self.robot.environment.is_valid_position(*self.target_pos):
                            path = self.app.a_star((self.robot.x, self.robot.y), self.target_pos, self.robot.environment,
                                                  robot_positions=robot_positions, path_cache=self.app.path_cache)
                            if path:
                                self.path = path
                                self.motion_status = "moving"
                                self.status = "navigating"
                            else:
                                self.target_pos = None
                    elif command == "start":
                        if self.mode == "manual" and not self.path:
                            self.motion_status = "moving"
                        elif self.mode == "autonomous":
                            self.status = "patrolling"
                    elif command == "stop":
                        self.motion_status = "stopped"
                        self.target_pos = None
                        self.path = []
                    elif command == "toggle_mode":
                        self.mode = "autonomous" if self.mode == "manual" else "manual"
                        print(f"[{self.name}] Mode switched to {self.mode}")

            self.channel.publish({
                "from": self.robot_id, "type": "status", "status": self.status,
                "motion": self.motion_status, "pos": (self.robot.x, self.robot.y), "mode": self.mode
            })
        except Exception as e:
            print(f"Error in VehicleOperatingAgent.process: {e}")

    def get_other_robot_positions(self, messages):
        try:
            positions = set()
            for msg in messages:
                if msg.get('type') == "status" and msg.get('from') != self.robot_id:
                    positions.add(msg['pos'])
            return positions
        except Exception as e:
            print(f"Error in get_other_robot_positions: {e}")
            return set()

    def move_along_path(self):
        try:
            if self.path:
                next_pos = self.path.pop(0)
                self.robot.x, self.robot.y = next_pos
                if self.robot.type_label == "Barn Cleaner":
                    self.robot.special_stat = f"Cleaned Area: {random.randint(0, 100)}%"
                else:
                    self.robot.special_stat = f"Harvest Load: {random.randint(0, 100)}/100"
            if not self.path:
                self.target_pos = None
                self.motion_status = "stopped"
                self.status = "idle"
        except Exception as e:
            print(f"Error in move_along_path: {e}")
            self.motion_status = "stopped"
            self.target_pos = None
            self.path = []

class AnomalyAgent(Agent):
    def __init__(self, name, channel, robot_id):
        super().__init__(name, channel)
        self.robot_id = robot_id

    def process(self, messages):
        pass

    def trigger_anomaly(self, issue="battery_low"):
        try:
            self.channel.publish({"from": self.robot_id, "type": "anomaly", "issue": issue})
        except Exception as e:
            print(f"Error in trigger_anomaly: {e}")

class MonitoringLoggingAgent(Agent):
    def __init__(self, name, channel, robot_id):
        super().__init__(name, channel)
        self.robot_id = robot_id
        self.logs = []
        self.log_limit = 5

    def process(self, messages):
        try:
            for msg in messages:
                if msg.get('from') == self.robot_id or msg.get('to') == self.robot_id:
                    log_entry = f"{time.strftime('%H:%M:%S')} - {msg}"
                    self.logs.append(log_entry)
            if len(self.logs) > self.log_limit:
                self.logs = self.logs[-self.log_limit:]
        except Exception as e:
            print(f"Error in MonitoringLoggingAgent.process: {e}")

class ConfigurationAgent(Agent):
    def __init__(self, name, channel):
        super().__init__(name, channel)
        self.config = {"team_size": 2, "mission": "clean_grid", "comms": "broadcast"}

    def process(self, messages):
        try:
            for msg in messages:
                if msg.get('type') == "request_config":
                    self.channel.publish({"type": "config", "data": self.config})
        except Exception as e:
            print(f"Error in ConfigurationAgent.process: {e}")

class CooperativeAgent(Agent):
    def __init__(self, name, channel):
        super().__init__(name, channel)
        self.fleet_data = {}

    def process(self, messages):
        try:
            for msg in messages:
                if msg.get('type') == "status":
                    self.fleet_data[msg['from']] = {'status': msg['status'], 'motion': msg['motion'], 'pos': msg['pos']}
                elif msg.get('type') == "anomaly":
                    anomaly_robot_id = msg['from']
                    other_robot_ids = [r_id for r_id in self.fleet_data if r_id != anomaly_robot_id]
                    if other_robot_ids:
                        target_robot_id = other_robot_ids[0]
                        anomaly_pos = self.fleet_data.get(anomaly_robot_id, {}).get('pos', (15, 15))
                        self.channel.publish({"to": target_robot_id, "command": "take_over_task", "pos": anomaly_pos})
        except Exception as e:
            print(f"Error in CooperativeAgent.process: {e}")

class ForecastingAgent(Agent):
    def __init__(self, name, channel):
        super().__init__(name, channel)
        self.last_forecast_time = 0
        self.forecast_interval = 10

    def process(self, messages):
        try:
            current_time = time.time()
            if current_time - self.last_forecast_time > self.forecast_interval:
                self.last_forecast_time = current_time
                self.channel.publish({"type": "forecast", "data": "ETA: 15 mins"})
        except Exception as e:
            print(f"Error in ForecastingAgent.process: {e}")