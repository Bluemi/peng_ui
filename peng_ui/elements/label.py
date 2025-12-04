from typing import Optional

import pygame as pg

from peng_ui.elements.base_element import BaseElement
from peng_ui.utils import RenderContext, ColorType


class Label(BaseElement):
    def __init__(
            self, rect: pg.Rect, text: str, text_color: ColorType = (200, 200, 200),
            bg_color: Optional[ColorType] = None
    ):
        super().__init__(rect)
        self.text = text
        self.text_color = text_color
        self.bg_color = bg_color
        self.text_surface: Optional[pg.Surface] = None

    def handle_event(self, event: pg.event.Event):
        super().handle_event(event)

    def draw(self, screen: pg.Surface, render_context: RenderContext):
        if self.bg_color:
            pg.draw.rect(screen, self.bg_color, self.rect)

        if self.text:
            if self.text_surface is None:
                self.text_surface = render_context.font.render(self.text, True, self.text_color)
                self.rect = self.text_surface.get_rect(center=self.rect.center)
            screen.blit(self.text_surface, self.rect)
