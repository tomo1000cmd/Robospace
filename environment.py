import pygame
from house_layout import ROOMS, DOORS

class Environment:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.grid = [[0 for _ in range(width)] for _ in range(height)]
        self.obstacles = set()
        self.rooms = []
        self._add_obstacles()

    def _add_obstacles(self):
        door_positions = {door["pos"] for door in DOORS}
        for room_name, room_data in ROOMS.items():
            x1, x2 = room_data["x_range"]
            y1, y2 = room_data["y_range"]
            room = {"bounds": (x1, y1, x2, y2), "center": ((x1 + x2) // 2, (y1 + y2) // 2)}
            self.rooms.append(room)
            for x in range(x1, x2 + 1):
                if (x, y1) not in door_positions and (x, y1) not in [(1, 1), (self.width - 2, self.height - 2)]:
                    self.obstacles.add((x, y1))
                if (x, y2) not in door_positions and (x, y2) not in [(1, 1), (self.width - 2, self.height - 2)]:
                    self.obstacles.add((x, y2))
            for y in range(y1, y2 + 1):
                if (x1, y) not in door_positions and (x1, y) not in [(1, 1), (self.width - 2, self.height - 2)]:
                    self.obstacles.add((x1, y))
                if (x2, y) not in door_positions and (x2, y) not in [(1, 1), (self.width - 2, self.height - 2)]:
                    self.obstacles.add((x2, y))

    def _add_wall(self, start_x, start_y, length, horizontal=True):
        for i in range(length):
            if horizontal:
                pos = (start_x + i, start_y)
            else:
                pos = (start_x, start_y + i)
            if 0 <= pos[0] < self.width and 0 <= pos[1] < self.height and pos not in [(1, 1), (self.width - 2, self.height - 2)]:
                self.obstacles.add(pos)

    def is_valid_position(self, x, y):
        try:
            if not (0 <= x < self.width and 0 <= y < self.height):
                return False
            if (x, y) in self.obstacles:
                return False
            return True
        except Exception as e:
            print(f"Error in is_valid_position: {e}")
            return False

    def draw(self, surface):
        try:
            grid_surface = pygame.Surface((self.width * 20, self.height * 20))
            grid_surface.fill((255, 255, 255))
            for y in range(self.height):
                for x in range(self.width):
                    rect = pygame.Rect(x * 20, y * 20, 20, 20)
                    if (x, y) in self.obstacles:
                        pygame.draw.rect(grid_surface, (127, 140, 141), rect)
                    else:
                        pygame.draw.rect(grid_surface, (220, 220, 220), rect, 1)
            surface.blit(grid_surface, (50, 50))
        except Exception as e:
            print(f"Error in Environment.draw: {e}")