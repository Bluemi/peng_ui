from typing import Optional

import pygame as pg

from peng_ui.elements.base_element import BaseElement
from peng_ui.utils import RenderContext, ColorType


class Button(BaseElement):
    def __init__(
            self, rect: pg.Rect, text: str = "",
            bg_color: ColorType = (180, 180, 180), hover_color: ColorType = (190, 190, 190),
            clicked_color: ColorType = (200, 200, 210), border_color: ColorType = (100, 100, 100),
            text_color: ColorType = (0, 0, 0)
    ):
        super().__init__()
        self.rect = rect
        self.text = text

        self.bg_color = bg_color
        self.hover_color = hover_color
        self.clicked_color = clicked_color
        self.border_color = border_color
        self.text_color = text_color
        self.border_width = 2

        self._is_hovered: bool = False
        self._is_clicked: bool = False
        self.text_surface: Optional[pg.Surface] = None

    def handle_event(self, event: pg.event.Event):
        super().handle_event(event)

        if event.type == pg.MOUSEMOTION:
            self._is_hovered = self.rect.collidepoint(event.pos)
        if self._is_hovered and event.type == pg.MOUSEBUTTONUP:
            self._is_clicked = True

    def clicked(self) -> bool:
        return self._is_clicked

    def finalize(self):
        self._is_clicked = False

    def draw(self, screen: pg.Surface, render_context: RenderContext):
        # Draw button background
        if self._is_hovered:
            color = self.clicked_color if pg.mouse.get_pressed()[0] else self.hover_color
        else:
            color = self.bg_color
        pg.draw.rect(screen, color, self.rect)

        # Draw border
        pg.draw.rect(screen, self.border_color, self.rect, self.border_width)

        # Render text
        if self.text:
            if self.text_surface is None:
                self.text_surface = render_context.font.render(self.text, True, self.text_color)
            text_rect = self.text_surface.get_rect(center=self.rect.center)
            screen.blit(self.text_surface, text_rect)
