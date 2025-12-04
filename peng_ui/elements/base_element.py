from abc import ABC, abstractmethod
from typing import final

import pygame as pg

from peng_ui.utils import RenderContext


class BaseElement(ABC):
    """
    Defines a base element class with different methods to implement functionality of ui elements.
    """
    def __init__(self, rect: pg.Rect):
        self.visible: bool = True
        self.is_hovered: bool = False
        self.rect: pg.Rect = rect
        self.is_clicked: bool = False

    @abstractmethod
    def handle_event(self, event: pg.event.Event):
        """
        Handle an event.
        :param event: The pygame event to handle
        """
        if event.type == pg.MOUSEMOTION:
            self.is_hovered = self.rect.collidepoint(event.pos)
        elif event.type == pg.MOUSEBUTTONUP:
            if self.is_hovered:
                self.is_clicked = True

    @abstractmethod
    def draw(self, screen: pg.Surface, render_context: RenderContext):
        """
        Draw the element to the given screen surface. Do not call this directly. Prefer render().

        :param screen: The screen surface to draw on.
        :param render_context: The render context to use for rendering.
        """
        pass

    def finalize(self):
        """
        Called at the end of a frame.
        """
        self.is_clicked = False

    @final
    def render(self, screen: pg.Surface, render_context: RenderContext):
        """
        Draw the element to the given screen surface.

        :param screen: The screen surface to draw on.
        :param render_context: The render context to use for rendering.
        """
        if self.visible:
            self.draw(screen, render_context)
        self.finalize()
