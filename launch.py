import pygame
from environment import Environment
from robot import Robot
from agents import VehicleOperatingAgent, AnomalyAgent, MonitoringLoggingAgent, ConfigurationAgent, CooperativeAgent, ForecastingAgent
from pathfinding import a_star
from ui import Button, RobotControlPanel

# --- Constants ---
SCREEN_WIDTH, SCREEN_HEIGHT = 1200, 900
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
LIGHT_GREY = (220, 220, 220)
GREEN = (46, 204, 113)
RED = (231, 76, 60)
BLUE = (52, 152, 219)
ROBOT_1_COLOR = (243, 156, 18)  # Orange for Barn Cleaner
ROBOT_2_COLOR = (52, 73, 94)    # Dark Blue for Chaser Bin
OBSTACLE_COLOR = (127, 140, 141)
SELECTION_COLOR = (46, 204, 113)
PATH_COLOR = (0, 0, 255, 128)

# --- Environment Configuration ---
GRID_SIZE = 20
CELL_SIZE = 20
GRID_WIDTH = 40
GRID_HEIGHT = 40
ENV_X_OFFSET, ENV_Y_OFFSET = 50, 50

# --- Communication Channel ---
class CommChannel:
    def __init__(self):
        self._messages = []

    def publish(self, msg):
        self._messages.append(msg)

    def get_and_clear_messages(self):
        if not self._messages:
            return []
        messages_to_send = list(self._messages)
        self._messages.clear()
        return messages_to_send

# --- Main Application ---
class App:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Robot Simulation with 2D Environment")
        self.clock = pygame.time.Clock()
        self.font_small = pygame.font.Font(None, 24)
        self.font_medium = pygame.font.Font(None, 28)
        self.font_large = pygame.font.Font(None, 36)
        self.running = True
        self.forecast = "Awaiting forecast..."
        self.selected_robot_id = None
        self.channel = CommChannel()
        self.environment = Environment(GRID_WIDTH, GRID_HEIGHT)
        self.path_cache = {}
        self._create_robots_and_agents()
        self._create_ui_elements()
        self.channel.publish({"type": "request_config"})

    def _create_robots_and_agents(self):
        self.robot1 = Robot(1, (1, 1), ROBOT_1_COLOR, self.channel, self.environment, "Barn Cleaner", self)
        self.robot2 = Robot(2, (38, 38), ROBOT_2_COLOR, self.channel, self.environment, "Chaser Bin", self)
        self.robots = {1: self.robot1, 2: self.robot2}
        self.robot1.voa = VehicleOperatingAgent(f"VOA{self.robot1.id}", self.channel, self.robot1.id, self.robot1, self)
        self.robot1.aa = AnomalyAgent(f"AA{self.robot1.id}", self.channel, self.robot1.id)
        self.robot1.mla = MonitoringLoggingAgent(f"MLA{self.robot1.id}", self.channel, self.robot1.id)
        self.robot2.voa = VehicleOperatingAgent(f"VOA{self.robot2.id}", self.channel, self.robot2.id, self.robot2, self)
        self.robot2.aa = AnomalyAgent(f"AA{self.robot2.id}", self.channel, self.robot2.id)
        self.robot2.mla = MonitoringLoggingAgent(f"MLA{self.robot2.id}", self.channel, self.robot2.id)
        self.robot1.agents = [self.robot1.voa, self.robot1.aa, self.robot1.mla]
        self.robot2.agents = [self.robot2.voa, self.robot2.aa, self.robot2.mla]
        self.config_a = ConfigurationAgent("ConfigAgent", self.channel)
        self.coop_a = CooperativeAgent("CoopAgent", self.channel)
        self.forecast_a = ForecastingAgent("ForecastAgent", self.channel)
        self.team_agents = [self.config_a, self.coop_a, self.forecast_a]
        self.all_agents = self.robot1.agents + self.robot2.agents + self.team_agents

    def _create_ui_elements(self):
        ui_x_offset = ENV_X_OFFSET + GRID_WIDTH * CELL_SIZE + 50
        panel_width, panel_height = 300, 400
        self.robot1_panel = RobotControlPanel((ui_x_offset, 50, panel_width, panel_height), self.robot1, self.font_small, self.font_large, self.channel)
        self.robot2_panel = RobotControlPanel((ui_x_offset, 460, panel_width, panel_height), self.robot2, self.font_small, self.font_large, self.channel)
        self.panels = {1: self.robot1_panel, 2: self.robot2_panel}
        self.global_buttons = {
            "stop_all": Button((ui_x_offset, 870, 150, 50), "Stop All", RED, self.font_medium),
            "reset": Button((ui_x_offset + 160, 870, 150, 50), "Reset", BLUE, self.font_medium),
        }

    def run(self):
        while self.running:
            self._handle_events()
            self._update_logic()
            self._draw()
            self.clock.tick(30)
        pygame.quit()

    def _handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            for panel in self.panels.values():
                if panel.handle_event(event):
                    break
            for name, button in self.global_buttons.items():
                if button.handle_event(event):
                    self._handle_global_button_press(name)
            if event.type == pygame.MOUSEBUTTONDOWN:
                self._handle_mouse_click(event.pos)

    def _handle_mouse_click(self, pos):
        for robot_id, panel in self.panels.items():
            if panel.rect.collidepoint(pos):
                self.selected_robot_id = robot_id
                print(f"Selected {panel.robot.type_label} (Robot {robot_id})")
                return
        grid_rect = pygame.Rect(ENV_X_OFFSET, ENV_Y_OFFSET, GRID_WIDTH * CELL_SIZE, GRID_HEIGHT * CELL_SIZE)
        if grid_rect.collidepoint(pos):
            grid_x = (pos[0] - ENV_X_OFFSET) // CELL_SIZE
            grid_y = (pos[1] - ENV_Y_OFFSET) // CELL_SIZE
            if pygame.mouse.get_pressed()[0] and self.selected_robot_id and self.environment.is_valid_position(grid_x, grid_y):
                robot_positions = {(r.x, r.y) for r_id, r in self.robots.items() if r_id != self.selected_robot_id}
                print(f"Commanding {self.selected_robot_id} to go to ({grid_x}, {grid_y})")
                self.channel.publish({"to": self.selected_robot_id, "command": "go_to", "pos": (grid_x, grid_y), "robot_positions": robot_positions})
            elif pygame.mouse.get_pressed()[2]:
                if (grid_x, grid_y) not in {(r.x, r.y) for r in self.robots.values()}:
                    self.environment.obstacles.add((grid_x, grid_y))
                    self.path_cache.clear()
                    print(f"Added obstacle at ({grid_x}, {grid_y})")

    def _handle_global_button_press(self, name):
        if name == "stop_all":
            self.channel.publish({"to": 1, "command": "stop"})
            self.channel.publish({"to": 2, "command": "stop"})
        elif name == "reset":
            self.environment.obstacles.clear()
            self.environment._add_obstacles()
            self.path_cache.clear()
            self.robot1.x, self.robot1.y = (1, 1)
            self.robot2.x, self.robot2.y = (38, 38)
            self.channel.publish({"to": 1, "command": "stop"})
            self.channel.publish({"to": 2, "command": "stop"})
            print("Environment and robots reset")

    def _update_logic(self):
        messages = self.channel.get_and_clear_messages()
        for msg in messages:
            if msg.get('type') == "forecast":
                self.forecast = msg['data']
        for agent in self.all_agents:
            agent.process(messages)

    def _draw(self):
        self.screen.fill(WHITE)
        self.environment.draw(self.screen)
        for robot_id, robot in self.robots.items():
            robot.draw(self.screen, is_selected=(robot_id == self.selected_robot_id))
        for panel in self.panels.values():
            panel.draw(self.screen, is_selected=(self.selected_robot_id and self.panels[self.selected_robot_id] == panel))
        for button in self.global_buttons.values():
            button.draw(self.screen)
        info_pos = (50, 850)
        if all(0 <= c <= max(SCREEN_WIDTH, SCREEN_HEIGHT) for c in info_pos):
            info_surf = self.font_small.render(f"Config: {self.config_a.config}", True, BLACK)
            self.screen.blit(info_surf, info_pos)
            forecast_pos = (50, 870)
            if all(0 <= c <= max(SCREEN_WIDTH, SCREEN_HEIGHT) for c in forecast_pos):
                forecast_surf = self.font_small.render(f"Forecast: {self.forecast}", True, BLACK)
                self.screen.blit(forecast_surf, forecast_pos)
        pygame.display.flip()

    def a_star(self, start, goal, environment, robot_positions=None, path_cache=None):
        return a_star(start, goal, environment, robot_positions, path_cache)

if __name__ == "__main__":
    app = App()
    app.run()