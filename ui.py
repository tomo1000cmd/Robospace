import pygame

class Button:
    def __init__(self, rect, text, bg_color, font, text_color=(0, 0, 0)):
        self.rect = pygame.Rect(rect)
        self.text = text
        self.bg_color = bg_color
        self.font = font
        try:
            self.rendered_text = self.font.render(self.text, True, text_color)
            self.text_rect = self.rendered_text.get_rect(center=self.rect.center)
        except Exception as e:
            print(f"Error in Button.__init__: {e}")
            self.rendered_text = None
            self.text_rect = self.rect
        self.is_hovered = False

    def draw(self, surface):
        try:
            if self.rendered_text is None:
                return
            if self.rect.x < 0 or self.rect.y < 0 or self.rect.x + self.rect.width > 1200 or self.rect.y + self.rect.height > 900:
                print(f"Invalid button rect at ({self.rect.x}, {self.rect.y})")
                return
            color = tuple(c * 0.9 for c in self.bg_color) if self.is_hovered else self.bg_color
            pygame.draw.rect(surface, color, self.rect, border_radius=8)
            surface.blit(self.rendered_text, self.text_rect)
        except Exception as e:
            print(f"Error in Button.draw: {e}")

    def handle_event(self, event):
        try:
            if event.type == pygame.MOUSEMOTION:
                self.is_hovered = self.rect.collidepoint(event.pos)
            if event.type == pygame.MOUSEBUTTONDOWN and self.rect.collidepoint(event.pos):
                return True
            return False
        except Exception as e:
            print(f"Error in Button.handle_event: {e}")
            return False

class RobotControlPanel:
    def __init__(self, rect, robot, font, title_font, channel):
        self.rect = pygame.Rect(rect)
        self.robot = robot
        self.font = font
        self.title_font = title_font
        self.channel = channel
        self.buttons = {
            "start": Button((self.rect.x + 10, self.rect.y + 50, 100, 40), "Start", (46, 204, 113), self.font),
            "stop": Button((self.rect.x + 120, self.rect.y + 50, 100, 40), "Stop", (231, 76, 60), self.font),
            "toggle_mode": Button((self.rect.x + 230, self.rect.y + 50, 100, 40), "Mode: Manual", (52, 152, 219), self.font),
        }
        self.log_limit = 5

    def draw(self, surface, is_selected=False):
        try:
            if self.rect.x < 0 or self.rect.y < 0 or self.rect.x + self.rect.width > 1200 or self.rect.y + self.rect.height > 900:
                print(f"Invalid RobotControlPanel rect at ({self.rect.x}, {self.rect.y})")
                return
            pygame.draw.rect(surface, (220, 220, 220), self.rect, border_radius=10)
            border_color = (46, 204, 113) if is_selected else (0, 0, 0)
            pygame.draw.rect(surface, border_color, self.rect, width=3 if is_selected else 2, border_radius=10)
            title_surf = self.title_font.render(self.robot.type_label, True, (0, 0, 0))
            surface.blit(title_surf, (self.rect.x + 15, self.rect.y + 10))

            status_text = f"Status: {self.robot.voa.status}"
            motion_text = f"Motion: {self.robot.voa.motion_status}"
            pos_text = f"Position: ({self.robot.x}, {self.robot.y})"
            mode_text = f"Mode: {self.robot.voa.mode}"
            special_text = self.robot.special_stat
            texts = [status_text, motion_text, pos_text, mode_text, special_text]
            for i, text in enumerate(texts):
                text_pos = (self.rect.x + 15, self.rect.y + 100 + i * 25)
                if text_pos[0] < 0 or text_pos[1] < 0 or text_pos[0] > 1200 or text_pos[1] > 900:
                    print(f"Invalid text position {text_pos} for '{text}'")
                    continue
                surface.blit(self.font.render(text, True, (0, 0, 0)), text_pos)

            logs_title_surf = self.font.render("Logs:", True, (0, 0, 0))
            logs_title_pos = (self.rect.x + 15, self.rect.y + 225)
            if logs_title_pos[0] < 0 or logs_title_pos[1] < 0 or logs_title_pos[0] > 1200 or logs_title_pos[1] > 900:
                print(f"Invalid logs title position {logs_title_pos}")
            else:
                surface.blit(logs_title_surf, logs_title_pos)
            for i, log in enumerate(self.robot.mla.logs):
                log_pos = (self.rect.x + 20, self.rect.y + 250 + i * 25)
                if log_pos[0] < 0 or log_pos[1] < 0 or log_pos[0] > 1200 or log_pos[1] > 900:
                    print(f"Invalid log position {log_pos} for log {i}")
                    continue
                surface.blit(self.font.render(log[:50], True, (0, 0, 0)), log_pos)

            for button in self.buttons.values():
                button.draw(surface)
                if button == self.buttons["toggle_mode"]:
                    mode_text = "Mode: Autonomous" if self.robot.voa.mode == "manual" else "Mode: Manual"
                    button.rendered_text = self.font.render(mode_text, True, (0, 0, 0))
                    button.text_rect = button.rendered_text.get_rect(center=button.rect.center)
        except Exception as e:
            print(f"Error in RobotControlPanel.draw: {e}")

    def handle_event(self, event):
        try:
            for name, button in self.buttons.items():
                if button.handle_event(event):
                    self._handle_button_press(name)
                    return True
            return False
        except Exception as e:
            print(f"Error in RobotControlPanel.handle_event: {e}")
            return False

    def _handle_button_press(self, name):
        try:
            if name == "start":
                self.channel.publish({"to": self.robot.id, "command": "start"})
            elif name == "stop":
                self.channel.publish({"to": self.robot.id, "command": "stop"})
            elif name == "toggle_mode":
                self.channel.publish({"to": self.robot.id, "command": "toggle_mode"})
        except Exception as e:
            print(f"Error in RobotControlPanel._handle_button_press: {e}")