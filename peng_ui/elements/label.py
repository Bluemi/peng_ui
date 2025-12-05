from typing import Optional

import pygame as pg

from peng_ui.elements.base_element import BaseElement
from peng_ui.utils import RenderContext, ColorType, Align


class Label(BaseElement):
    def __init__(
            self, rect: pg.Rect, text: str, text_color: ColorType = (200, 200, 200),
            bg_color: Optional[ColorType] = None, align: Align = Align.CENTER
    ):
        super().__init__(rect)
        self._text = text
        self.text_color = text_color
        self.bg_color = bg_color
        self._text_surface: Optional[pg.Surface] = None
        self.align = align

    def handle_event(self, event: pg.event.Event):
        super().handle_event(event)

    def set_text(self, text: str):
        self._text = text
        self._text_surface = None

    def draw(self, screen: pg.Surface, render_context: RenderContext):
        if self.bg_color:
            pg.draw.rect(screen, self.bg_color, self.rect)

        if self._text:
            if self._text_surface is None:
                self._text_surface = render_context.font.render(self._text, True, self.text_color)
            rect = self.align.align_in(self._text_surface.get_rect(), self.rect)
            screen.blit(self._text_surface, rect)
