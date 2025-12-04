#!/usr/bin/env python3

import warnings

import pygame as pg

from peng_ui.elements.text_field import TextField
from peng_ui.elements.edit_field import EditField
from peng_ui.elements.label import Label
from peng_ui.elements.button import Button
from peng_ui.utils import RenderContext

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
        pg.init()
        self.screen = pg.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pg.scrap.init()
        pg.display.set_caption(CAPTION)
        self.font = load_font()
        self.last_event_text = ""
        self.running = True
        self.render_context = RenderContext.default()

        self.button = Button(pg.Rect(50, 50, 120, 40), "hello")
        self.label = Label(pg.Rect(50, 100, 120, 40), "hello")
        self.edit_field = EditField(pg.Rect(200, 50, 220, 40), "hello")
        self.text_field = TextField(pg.Rect(200, 100, 220, 140), "hello")

    def run(self):
        while self.running:
            self.handle_events()
            self.tick()
            self.render()

        pg.quit()

    def handle_events(self):
        for event in pg.event.get():
            if event.type == pg.QUIT:
                self.running = False
                break
            self.button.handle_event(event)
            self.label.handle_event(event)
            self.edit_field.handle_event(event)
            self.text_field.handle_event(event)

    def tick(self):
        if self.button.is_clicked:
            print('button clicked')
        if self.label.is_clicked:
            print('label clicked')

    def render(self):
        self.screen.fill(BLACK)
        draw_text(self.screen, self.last_event_text, GREEN, SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2, self.font)
        self.button.render(self.screen, self.render_context)
        self.label.render(self.screen, self.render_context)
        self.edit_field.render(self.screen, self.render_context)
        self.text_field.render(self.screen, self.render_context)
        pg.display.flip()


def load_font():
    try:
        font = pg.font.Font(None, 36)
    except pg.error:
        warnings.warn("Warning: Could not load default font. Text will not be rendered.")
        font = None
    return font


def draw_text(surface, text, color, x, y, font):
    """Renders and draws text onto the screen surface."""
    if font:
        text_surface = font.render(text, True, color)
        text_rect = text_surface.get_rect(center=(x, y))
        surface.blit(text_surface, text_rect)


if __name__ == '__main__':
    viewer = Viewer()
    viewer.run()
