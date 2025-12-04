from typing import Iterable, Optional, List

import pygame as pg

from peng_ui.elements.base_element import BaseElement
from peng_ui.utils import RenderContext


class Container:
    def __init__(self):
        self._element_cache: Optional[List[BaseElement]] = None

    def iter_elements(self) -> Iterable[BaseElement]:
        """
        Iter over all elements in the container.
        :return: Iterable of BaseElement objects.
        """
        if self._element_cache is None:
            self._element_cache = [elem for elem in self.__dict__.values() if isinstance(elem, BaseElement)]

        yield from self._element_cache

    def handle_event(self, event: pg.event.Event):
        for elem in self.iter_elements():
            elem.handle_event(event)

    def render(self, screen: pg.Surface, render_context: RenderContext):
        for element in self.iter_elements():
            element.render(screen, render_context)
