#!/usr/bin/env python3

import warnings

import pygame

SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
CAPTION = "Pygame Basic Test"
TIMER_DURATION = 3.0

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)


class Viewer:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption(CAPTION)
        self.font = load_font()
        self.last_event_text = "No recent events..."
        self.running = True

    def run(self):
        while self.running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    print("--- Event: QUIT (Window closed by user) ---")
                    self.running = False
                elif event.type == pygame.KEYDOWN:
                    key_name = pygame.key.name(event.key)
                    print(f"--- Event: KEYDOWN --- Key: '{key_name}' (Code: {event.key})")
                    self.last_event_text = f"Key Down: {key_name}"
                elif event.type == pygame.KEYUP:
                    key_name = pygame.key.name(event.key)
                    print(f"--- Event: KEYUP --- Key: '{key_name}' (Code: {event.key})")
                    self.last_event_text = f"Key Up: {key_name}"
                elif event.type == pygame.MOUSEMOTION:
                    x, y = event.pos
                    rel_x, rel_y = event.rel
                    print(f"--- Event: MOUSEMOTION --- Pos: ({x}, {y}) | Relative Movement: ({rel_x}, {rel_y})")
                    self.last_event_text = f"Mouse Position: ({x}, {y})"
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    x, y = event.pos
                    button = event.button
                    button_names = {1: "Left Click", 2: "Middle Click", 3: "Right Click", 4: "Scroll Up", 5: "Scroll Down"}
                    button_name = button_names.get(button, f"Button {button}")

                    print(f"--- Event: MOUSEBUTTONDOWN --- {button_name} at ({x}, {y})")
                    self.last_event_text = f"Click: {button_name}"
                elif event.type == pygame.MOUSEBUTTONUP:
                    x, y = event.pos
                    button = event.button
                    button_names = {1: "Left Click", 2: "Middle Click",
                                    3: "Right Click"}  # Scroll events don't usually have an 'UP' counterpart
                    button_name = button_names.get(button, f"Button {button}")

                    # Filter out the scroll wheel events for release, as they are usually only DOWN events
                    if button <= 3:
                        print(f"--- Event: MOUSEBUTTONUP --- {button_name} released at ({x}, {y})")
                        self.last_event_text = f"Release: {button_name}"

            # Clear the screen
            self.screen.fill(BLACK)

            # Display the last event text
            draw_text(self.screen, self.last_event_text, GREEN, SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2, self.font)

            # Flip the display to make the changes visible
            pygame.display.flip()

        pygame.quit()


def load_font():
    try:
        font = pygame.font.Font(None, 36)  # Use default font, size 36
    except pygame.error:
        warnings.warn("Warning: Could not load default font. Text will not be rendered.")
        font = None
    return font


def draw_text(surface, text, color, x, y, font):
    """Renders and draws text onto the screen surface."""
    if font:
        text_surface = font.render(text, True, color)
        text_rect = text_surface.get_rect(center=(x, y))
        surface.blit(text_surface, text_rect)


# --- Main Game Loop ---

if __name__ == '__main__':
    viewer = Viewer()
    viewer.run()
