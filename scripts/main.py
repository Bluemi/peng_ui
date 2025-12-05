#!/usr/bin/env python3

import pygame as pg

from peng_ui.elements import TextField, EditField, Label, Button
from peng_ui.viewer import Viewer

class MyViewer(Viewer):
    def __init__(self):
        super().__init__(screen_size=(800, 600))
        self.button = Button(pg.Rect(50, 50, 120, 40), "Click Me!")
        self.label = Label(pg.Rect(50, 100, 120, 40), "This is text :)")
        self.edit_field = EditField(pg.Rect(200, 50, 220, 40), "Edit me...")
        self.text_field = TextField(pg.Rect(200, 100, 520, 440), "This is a long text :).\nIt supports multi-lines, copy-paste, selection, ...")

    def tick(self):
        if self.button.is_clicked:
            self.text_field.set_text(self.edit_field.text)
        if self.label.is_clicked:
            print('label clicked')


if __name__ == '__main__':
    viewer = MyViewer()
    viewer.run()
