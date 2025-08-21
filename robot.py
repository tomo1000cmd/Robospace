import pygame

class Robot:
    def __init__(self, robot_id, start_pos, color, channel, environment, type_label, app=None):
        self.id = robot_id
        self.x, self.y = start_pos
        self.color = color
        self.environment = environment
        self.type_label = type_label
        self.voa = None
        self.mla = None
        self.agents = []
        self.special_stat = "Coverage: 0%"
        self.visited = set()

    def draw(self, surface, is_selected=False):
        rect = pygame.Rect(50 + self.x * 20, 50 + self.y * 20, 20, 20)
        pygame.draw.rect(surface, self.color, rect, border_radius=5)
        if is_selected:
            pygame.draw.rect(surface, (46, 204, 113), rect, 3, border_radius=5)
        
        if self.voa and self.voa.path:
            path_points = [(50 + p[0] * 20 + 10, 50 + p[1] * 20 + 10) for p in [(self.x, self.y)] + self.voa.path]
            if len(path_points) > 1:
                pygame.draw.lines(surface, self.color, False, path_points, 3)