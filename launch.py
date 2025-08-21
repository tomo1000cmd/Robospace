import pygame
from environment import Environment
from robot import Robot
from agents import VehicleOperatingAgent, MonitoringLoggingAgent, ConfigurationAgent, CooperativeAgent, ForecastingAgent
from pathfinding import a_star, generate_coverage_path
from ui import Button, RobotControlPanel, InputBox
from task_manager import TaskManager
import time
import ast
# --- Constants ---
SCREEN_WIDTH, SCREEN_HEIGHT = 1200, 900
WHITE, BLACK, LIGHT_GREY = (255, 255, 255), (0, 0, 0), (220, 220, 220)
GREEN, RED, BLUE = (46, 204, 113), (231, 76, 60), (52, 152, 219)
ROBO1_COLOR, ROBO2_COLOR = (243, 156, 18), (52, 73, 94)
GRID_WIDTH, GRID_HEIGHT, CELL_SIZE = 40, 40, 20
ENV_X_OFFSET, ENV_Y_OFFSET = 50, 50

# --- Communication Channel ---
class CommChannel:
    def __init__(self):
        self._messages = []
    def publish(self, msg):
        self._messages.append(msg)
    def get_and_clear_messages(self):
        messages_to_send = list(self._messages)
        self._messages.clear()
        return messages_to_send

# --- Main Application ---
class App:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Autonomous Robot Simulation")
        self.clock = pygame.time.Clock()
        self.font_small = pygame.font.Font(None, 24)
        self.font_large = pygame.font.Font(None, 36)
        self.running = True
        self.selected_robot_id = 1
        self.channel = CommChannel()
        self.environment = Environment(GRID_WIDTH, GRID_HEIGHT)
        self.path_cache = {}
        self._create_robots_and_agents()
        self._create_ui_elements()

    def _create_robots_and_agents(self):
        self.robots = {
            1: Robot(1, (1, 1), ROBO1_COLOR, self.channel, self.environment, "Robo1", self),
            2: Robot(2, (38, 38), ROBO2_COLOR, self.channel, self.environment, "Robo2", self)
        }
        self.all_agents = []
        for rid, robot in self.robots.items():
            robot.voa = VehicleOperatingAgent(f"VOA{rid}", self.channel, rid, robot, self)
            robot.mla = MonitoringLoggingAgent(f"MLA{rid}", self.channel, rid)
            robot.agents = [robot.voa, robot.mla]
            self.all_agents.extend(robot.agents)
        
        self.task_manager = TaskManager(self.channel, list(self.robots.keys()), [room['center'] for room in self.environment.rooms])
        self.team_agents = [
            ConfigurationAgent("Config", self.channel),
            CooperativeAgent("Coop", self.channel, self),  # Pass App instance
            ForecastingAgent("Forecast", self.channel, self),  # Pass App instance
            self.task_manager
        ]
        self.all_agents.extend(self.team_agents)

    def _create_ui_elements(self):
        ui_x = ENV_X_OFFSET + GRID_WIDTH * CELL_SIZE + 50
        self.panels = {
            1: RobotControlPanel((ui_x, 50, 300, 380), self.robots[1], self.font_small, self.font_large, self.channel),
            2: RobotControlPanel((ui_x, 440, 300, 380), self.robots[2], self.font_small, self.font_large, self.channel)
        }
        self.task_input = InputBox((ui_x, 830, 200, 32), self.font_small)
        self.global_buttons = {
            "send_task": Button((ui_x + 210, 830, 90, 32), "Send Task", BLUE, self.font_small),
            "reset": Button((ui_x, 870, 300, 50), "Reset Simulation", RED, self.font_large),
        }

    def run(self):
        while self.running:
            self._handle_events()
            self._update_logic()
            self._draw()
            self.clock.tick(30)
        pygame.quit()

    def _handle_events(self):
        task_tuple = None
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            
            for panel in self.panels.values():
                panel.handle_event(event)
            task_tuple = self.task_input.handle_event(event)

            if event.type == pygame.MOUSEBUTTONDOWN:
                if self.panels[1].rect.collidepoint(event.pos):
                    self.selected_robot_id = 1
                elif self.panels[2].rect.collidepoint(event.pos):
                    self.selected_robot_id = 2
                self._handle_mouse_click(event.pos)

            for name, button in self.global_buttons.items():
                if button.handle_event(event):
                    if name == "send_task":
                        task_tuple = self.parse_task_from_input()
                    elif name == "reset":
                        self.__init__()
        
        if task_tuple:
            self._assign_tuple_task(task_tuple)
    
    def parse_task_from_input(self):
        try:
            return ast.literal_eval(self.task_input.text)
        except:
            self.task_input.text = "ERROR"
            return None

    def _assign_tuple_task(self, task_tuple):
        if not self.selected_robot_id or not isinstance(task_tuple, tuple) or len(task_tuple) != 2:
            return
        command, location = task_tuple
        
        if command == 'cover_room':
            room = next((r for r in self.environment.rooms if r['center'] == location), None)
            if room:
                task_id = f"task_{int(time.time())}_{self.selected_robot_id}"
                self.channel.publish({"to": self.selected_robot_id, "command": command, "task_id": task_id, "room_center": location})
        elif command == 'cover_multi_rooms':
            task_id = f"multi_task_{int(time.time())}_{self.selected_robot_id}"
            self.channel.publish({"to": self.selected_robot_id, "command": command, "task_id": task_id, "room_centers": location})
        elif command == 'go_to':
            if self.environment.is_valid_position(*location):
                task_id = f"task_{int(time.time())}_{self.selected_robot_id}"
                self.channel.publish({"to": self.selected_robot_id, "command": command, "task_id": task_id, "pos": location})

    def _handle_mouse_click(self, pos):
        grid_rect = pygame.Rect(ENV_X_OFFSET, ENV_Y_OFFSET, GRID_WIDTH * CELL_SIZE, GRID_HEIGHT * CELL_SIZE)
        if grid_rect.collidepoint(pos):
            grid_x = (pos[0] - ENV_X_OFFSET) // CELL_SIZE
            grid_y = (pos[1] - ENV_Y_OFFSET) // CELL_SIZE
            if pygame.mouse.get_pressed()[0] and self.selected_robot_id and self.environment.is_valid_position(grid_x, grid_y):
                task_id = f"task_{int(time.time())}_{self.selected_robot_id}"
                self.channel.publish({"to": self.selected_robot_id, "command": "go_to", "task_id": task_id, "pos": (grid_x, grid_y)})
            elif pygame.mouse.get_pressed()[2]:
                self.environment.obstacles.add((grid_x, grid_y))
                self.path_cache.clear()

    def _update_logic(self):
        messages = self.channel.get_and_clear_messages()
        for agent in self.all_agents:
            agent.process(messages)

    def _draw(self):
        self.screen.fill(WHITE)
        self.environment.draw(self.screen)
        for rid, robot in self.robots.items():
            robot.draw(self.screen, is_selected=(rid == self.selected_robot_id))
        for rid, panel in self.panels.items():
            panel.draw(self.screen, is_selected=(rid == self.selected_robot_id))
        self.task_input.draw(self.screen)
        for button in self.global_buttons.values():
            button.draw(self.screen)
        pygame.display.flip()

    def a_star(self, start, goal, environment, robot_positions=None, extra_obstacles=set(), path_cache=None):
        return a_star(start, goal, environment, robot_positions, extra_obstacles, path_cache)

    def generate_coverage_path(self, bounds):
        return generate_coverage_path(bounds, self.environment)

if __name__ == "__main__":
    app = App()
    app.run()