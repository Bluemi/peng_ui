from typing import Tuple, Optional, List, Union, Iterable

import pygame as pg

from peng_ui.elements.base_element import BaseElement
from peng_ui.container import Container
from peng_ui.utils import RenderContext


class Viewer:
    def __init__(self, screen_size: Tuple[int, int] = (800, 600), title: str = "Window"):
        pg.init()
        self.screen = pg.display.set_mode(screen_size)
        pg.scrap.init()
        pg.display.set_caption(title)
        self.running = True
        self.render_context = RenderContext.default()
        self._element_cache: Optional[List[Union[Container, BaseElement]]] = None

    def run(self):
        while self.running:
            self.handle_events()
            self.tick()
            self.render()

        pg.quit()

    def iter_elements(self) -> Iterable[Union[BaseElement, Container]]:
        """
        Iter over all elements in the container.
        :return: Iterable of BaseElement objects.
        """
        if self._element_cache is None:
            self._element_cache = [elem for elem in self.__dict__.values() if isinstance(elem, (BaseElement, Container))]

        yield from self._element_cache

    def handle_events(self):
        for event in pg.event.get():
            if event.type == pg.QUIT:
                self.running = False
                break
            for elem in self.iter_elements():
                elem.handle_event(event)

    def tick(self):
        pass

    def render(self):
        self.screen.fill(0)
        for elem in self.iter_elements():
            elem.render(self.screen, self.render_context)
        pg.display.flip()
