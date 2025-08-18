import pygame

class Robot:
    def __init__(self, robot_id, start_pos, color, channel, environment, type_label, app=None):
        self.id = robot_id
        self.x, self.y = start_pos
        self.color = color
        self.environment = environment
        self.type_label = type_label
        self.voa = None  # Set by App
        self.aa = None  # Set by App
        self.mla = None  # Set by App
        self.agents = []
        if self.type_label == "Barn Cleaner":
            self.special_stat = "Cleaned Area: 0%"
        else:
            self.special_stat = "Harvest Load: 0/100"

    def move(self, dx, dy):
        try:
            new_x, new_y = self.x + dx, self.y + dy
            if self.environment.is_valid_position(new_x, new_y):
                self.x = new_x
                self.y = new_y
            else:
                print(f"Invalid move to ({new_x}, {new_y}) for Robot {self.id}")
        except Exception as e:
            print(f"Error in Robot.move: {e}")

    def draw(self, surface, is_selected=False):
        try:
            rect = pygame.Rect(50 + self.x * 20, 50 + self.y * 20, 20, 20)
            if rect.x < 0 or rect.y < 0 or rect.x + rect.width > 1200 or rect.y + rect.height > 900:
                print(f"Invalid robot rect at ({rect.x}, {rect.y})")
                return
            pygame.draw.rect(surface, self.color, rect, border_radius=5)
            if is_selected:
                pygame.draw.rect(surface, (46, 204, 113), rect, 3, border_radius=5)
            if self.voa and self.voa.path:
                prev = (self.x, self.y)
                for p in self.voa.path:
                    if not self.environment.is_valid_position(*p):
                        print(f"Invalid path point {p}")
                        continue
                    center_prev = (50 + prev[0] * 20 + 10, 50 + prev[1] * 20 + 10)
                    center = (50 + p[0] * 20 + 10, 50 + p[1] * 20 + 10)
                    if any(c < 0 or c > max(1200, 900) for c in center_prev + center):
                        print(f"Invalid path line from {center_prev} to {center}")
                        continue
                    pygame.draw.line(surface, self.color, center_prev, center, 3)
                    prev = p
            if self.voa and self.voa.target_pos:
                tx, ty = self.voa.target_pos
                target_center = (50 + tx * 20 + 10, 50 + ty * 20 + 10)
                if target_center[0] < 0 or target_center[1] < 0 or target_center[0] > 1200 or target_center[1] > 900:
                    print(f"Invalid target center {target_center}")
                else:
                    pygame.draw.circle(surface, self.color, target_center, 7)
        except Exception as e:
            print(f"Error in Robot.draw: {e}")