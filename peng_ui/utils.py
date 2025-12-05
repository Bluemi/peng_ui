import warnings
from typing import Union, Tuple

import pygame as pg


ColorType = Union[Tuple[int, int, int], pg.Color]


class RenderContext:
    def __init__(self, font: pg.font.Font):
        self.font = font
        self.mouse_pressed = False

    @staticmethod
    def default():
        font = load_font()
        return RenderContext(font)


def load_font():
    """
    Helper function to load the default font.
    :return: The font to use
    """
    try:
        font = pg.font.Font(None, 36)
    except pg.error:
        warnings.warn("Warning: Could not load default font. Text will not be rendered.")
        font = None
    return font


def clamp(n, minn, maxn):
    return max(min(maxn, n), minn)
