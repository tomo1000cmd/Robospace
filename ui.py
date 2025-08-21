import pygame
import ast

class Button:
    def __init__(self, rect, text, bg_color, font, text_color=(0, 0, 0)):
        self.rect = pygame.Rect(rect)
        self.text = text
        self.bg_color = bg_color
        self.font = font
        self.rendered_text = self.font.render(self.text, True, text_color)
        self.text_rect = self.rendered_text.get_rect(center=self.rect.center)
        self.is_hovered = False

    def draw(self, surface):
        color = tuple(c * 0.9 for c in self.bg_color) if self.is_hovered else self.bg_color
        pygame.draw.rect(surface, color, self.rect, border_radius=8)
        surface.blit(self.rendered_text, self.text_rect)

    def handle_event(self, event):
        if event.type == pygame.MOUSEMOTION:
            self.is_hovered = self.rect.collidepoint(event.pos)
        if event.type == pygame.MOUSEBUTTONDOWN and self.rect.collidepoint(event.pos):
            return True
        return False

class RobotControlPanel:
    def __init__(self, rect, robot, font, title_font, channel):
        self.rect = pygame.Rect(rect)
        self.robot = robot
        self.font = font
        self.title_font = title_font
        self.channel = channel
        self.buttons = {
            "start": Button((self.rect.x + 10, self.rect.y + 50, 135, 40), "Start Moving", (46, 204, 113), self.font),
            "stop": Button((self.rect.x + 155, self.rect.y + 50, 135, 40), "Stop", (231, 76, 60), self.font),
        }

    def draw(self, surface, is_selected=False):
        pygame.draw.rect(surface, (220, 220, 220), self.rect, border_radius=10)
        border_color = (46, 204, 113) if is_selected else (0, 0, 0)
        pygame.draw.rect(surface, border_color, self.rect, width=3 if is_selected else 2, border_radius=10)
        
        title_surf = self.title_font.render(self.robot.type_label, True, (0, 0, 0))
        surface.blit(title_surf, (self.rect.x + 15, self.rect.y + 10))

        texts = [
            f"Status: {self.robot.voa.status}",
            f"Motion: {self.robot.voa.motion_status}",
            f"Position: ({self.robot.x}, {self.robot.y})",
            f"Mode: {self.robot.voa.mode}",
            self.robot.special_stat,
            f"Distance Traveled: {self.robot.voa.distance_traveled:.1f} units",
            f"Tasks Completed: {len(self.robot.mla.task_history)}"
        ]
        for i, text in enumerate(texts):
            surface.blit(self.font.render(text, True, (0, 0, 0)), (self.rect.x + 15, self.rect.y + 100 + i * 25))

        logs_title_surf = self.font.render("Logs:", True, (0, 0, 0))
        surface.blit(logs_title_surf, (self.rect.x + 15, self.rect.y + 275))
        for i, log in enumerate(self.robot.mla.logs):
            surface.blit(self.font.render(log[:50], True, (0, 0, 0)), (self.rect.x + 20, self.rect.y + 300 + i * 25))

        tasks_title_surf = self.font.render("Task History:", True, (0, 0, 0))
        surface.blit(tasks_title_surf, (self.rect.x + 15, self.rect.y + 425))
        for i, task in enumerate(self.robot.mla.task_history):
            surface.blit(self.font.render(task[:50], True, (0, 0, 0)), (self.rect.x + 20, self.rect.y + 450 + i * 25))

        for button in self.buttons.values():
            button.draw(surface)

    def handle_event(self, event):
        for name, button in self.buttons.items():
            if button.handle_event(event):
                if name == "start": self.channel.publish({"to": self.robot.id, "command": "start"})
                elif name == "stop": self.channel.publish({"to": self.robot.id, "command": "stop"})
                return True
        return False

class InputBox:
    def __init__(self, rect, font):
        self.rect = pygame.Rect(rect)
        self.font = font
        self.text = ""
        self.active = False
        self.color_inactive = (200, 200, 200)
        self.color_active = (100, 100, 200)
        self.color = self.color_inactive

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            self.active = self.rect.collidepoint(event.pos)
            self.color = self.color_active if self.active else self.color_inactive
        if event.type == pygame.KEYDOWN and self.active:
            if event.key == pygame.K_RETURN:
                try:
                    parsed_task = ast.literal_eval(self.text)
                    if isinstance(parsed_task, tuple):
                        self.text = ""
                        return parsed_task
                except (ValueError, SyntaxError):
                    self.text = "ERROR: Invalid Format"
            elif event.key == pygame.K_BACKSPACE:
                self.text = self.text[:-1]
            else:
                self.text += event.unicode
        return None

    def draw(self, surface):
        pygame.draw.rect(surface, self.color, self.rect, 2, border_radius=5)
        text_surface = self.font.render(self.text, True, (0, 0, 0))
        surface.blit(text_surface, (self.rect.x + 5, self.rect.y + 5))