from typing import Optional, Tuple, List, Union, Iterable

import pygame as pg

from peng_ui.elements.base_element import BaseElement
from peng_ui.utils import RenderContext, ColorType, load_font

SCRAP_TEXT = 'text/plain;charset=utf-8'


'''
Consider the following paragraphs
paragraphs = [
    "123", "456"
]
cursor at the start of the first paragraph _123: Cursor(x, 0, 0)
cursor at the start of the first paragraph 123_: Cursor(x, 3, 0)
the length of a paragraph is the string length + 1.
'''
class Cursor:
    def __init__(self, line_index: int, paragraph_index: int, char_index: int):
        self.line_index = line_index
        self.paragraph_index = paragraph_index
        self.char_index = char_index

    @staticmethod
    def from_tuple(paragraph_index: int, char_index: int):
        return Cursor(-1, paragraph_index, char_index)

    def copy(self) -> 'Cursor':
        return Cursor(self.line_index, self.paragraph_index, self.char_index)

    def __repr__(self):
        return f'Cursor({self.line_index}, {self.paragraph_index}, {self.char_index})'

    def __eq__(self, other):
        return self.line_index == other.line_index and self.paragraph_index == other.paragraph_index and self.char_index == other.char_index

    def __ne__(self, other):
        return not self.__eq__(other)

    def __lt__(self, other):
        if self.line_index == other.line_index:
            if self.paragraph_index == other.paragraph_index:
                return self.char_index < other.char_index
            else:
                return self.paragraph_index < other.paragraph_index
        else:
            return self.line_index < other.line_index

    def __gt__(self, other):
        return self.__ne__(other) and not self.__lt__(other)


CursorOrTuple = Union[Cursor, Tuple[int, int]]


class Line:
    """
    Represents a line in a text field. Can contain multiple paragraphs that are automatically wrapped.
    Each manual enter from the user will create a new Line object. Each line that is longer than the width of the
    TextField will create a new paragraph.
    """
    def __init__(self, text: Union[str, List[str]] = ''):
        if isinstance(text, str):
            text = [text]
        self.paragraphs: List[str] = text

    def __repr__(self):
        # return f'Line({len(self.paragraphs)} paragraphs, {self.num_chars()} chars)'
        return str(self.paragraphs)

    def get_line_char_index(self, paragraph_index: int, char_index: int) -> int:
        """
        Returns the character index, if all paragraphs would be in a single string.
        """
        return sum(len(p) + 1 for p in self.paragraphs[:paragraph_index]) + char_index

    def auto_wrap_and_norm_cursor(self, font: pg.font.Font, max_width: int, cursor: Cursor):
        """
        Wraps the line to fit within the given max width.

        :param font: The font to use for wrapping.
        :param max_width: The maximum width to wrap the line to.
        :param cursor: A cursor object, that will be handled correctly, if wrapping occurs at the cursor position. It is
            assumed, that the cursor points to the current line.
        :returns: The given cursor. If a wrap happens the returned cursor will point to the same character possibly in
            a different paragraph.
        """
        line_char_index = self.get_line_char_index(cursor.paragraph_index, cursor.char_index)
        self.auto_wrap(font, max_width)
        new_cursor = Cursor(cursor.line_index, cursor.paragraph_index, line_char_index)
        new_cursor.paragraph_index, new_cursor.char_index = self.get_paragraph_char_index(line_char_index)
        return new_cursor

    def get_paragraph_char_index(self, line_char_index: int) -> Tuple[int, int]:
        cum_char_sum = 0
        for i, p in enumerate(self.paragraphs):
            p_chars = len(p) + 1  # every paragraph ends with a virtual extra character
            if line_char_index < cum_char_sum + p_chars:
                return i, line_char_index - cum_char_sum
            cum_char_sum += p_chars  # TODO: +1?
        return len(self.paragraphs) - 1, 0

    def word_list(self) -> List[str]:
        word_list = []
        for p in self.paragraphs:
            word_list.extend(p.split(' '))
        return word_list

    def auto_wrap(self, font: pg.font.Font, max_width: int):
        words = self.word_list()
        current_line = ''
        new_paragraphs = []

        for word in words:
            # Test if adding this word would exceed max width
            test_line = current_line + (" " if current_line else "") + word
            test_width = font.size(test_line)[0]

            if test_width <= max_width:
                # Word fits on current line
                current_line = test_line
            else:
                # Word doesn't fit
                if current_line:
                    # Save current line and start new one
                    new_paragraphs.append(current_line)
                    current_line = word
                else:
                    # Single word is too long, force it on its own line
                    new_paragraphs.append(word)
                    current_line = ""

        # Add the last line of this paragraph
        if current_line:
            new_paragraphs.append(current_line)

        self.paragraphs = new_paragraphs
        self.ensure_paragraph()

    def num_paragraphs(self) -> int:
        return len(self.paragraphs)

    def num_chars(self) -> int:
        """
        Returns the number of characters in the line. Each automatic wrap counts as one character.
        """
        return sum(len(p) for p in self.paragraphs) + len(self.paragraphs) - 1

    def split(self, paragraph_index: int, split_index: int) -> Tuple['Line', 'Line']:
        """
        Splits the current line at the given paragraph and character index. Returns the two resulting lines.
        """
        left_paragraphs = self.paragraphs[:paragraph_index]
        right_paragraphs = self.paragraphs[paragraph_index+1:]
        middle_paragraph = self.paragraphs[paragraph_index]
        left_part = ' ' + middle_paragraph[:split_index]
        right_part = middle_paragraph[split_index:] + ' '
        left_paragraphs.append(left_part)
        right_paragraphs.insert(0, right_part)
        return Line(''.join(left_paragraphs)), Line(''.join(right_paragraphs))

    @staticmethod
    def _remove_from_paragraph(paragraph: str, start: int, end: int) -> str:
        return paragraph[:start] + paragraph[end:]

    def delete(self, start: CursorOrTuple, end: CursorOrTuple):
        if isinstance(start, tuple):
            start = Cursor.from_tuple(*start)
        if isinstance(end, tuple):
            end = Cursor.from_tuple(*end)

        if start.paragraph_index == end.paragraph_index:
            p = self.paragraphs[start.paragraph_index]
            self.paragraphs[start.paragraph_index] = p[:start.char_index] + p[end.char_index:]
            self.ensure_paragraph()
            return
        before_start = self.paragraphs[:start.paragraph_index]
        last_after_start = self.paragraphs[start.paragraph_index]
        first_before_end = self.paragraphs[end.paragraph_index]
        after_end = []
        if end.paragraph_index+1 < len(self.paragraphs):
            after_end = self.paragraphs[end.paragraph_index+1:]

        new_paragraphs = before_start
        middle_paragraph = last_after_start[:start.char_index] + first_before_end[end.char_index:]
        if middle_paragraph:
            new_paragraphs.append(middle_paragraph)
        new_paragraphs.extend(after_end)
        self.paragraphs = new_paragraphs
        self.ensure_paragraph()

    def ensure_paragraph(self):
        if not self.paragraphs:
            self.paragraphs = ['']

    def end(self) -> Tuple[int, int]:
        paragraph_index = len(self.paragraphs) - 1
        char_index = len(self.paragraphs[-1])
        return paragraph_index, char_index




class TextField(BaseElement):
    def __init__(
            self, rect: pg.Rect, text: str = "", placeholder: str = "",
            bg_color: ColorType = (40, 40, 40), hover_color: ColorType = (60, 60, 60),
            clicked_color: ColorType = (90, 90, 100), border_color: ColorType = (140, 140, 140),
            text_color: ColorType = (200, 200, 200)
    ):
        super().__init__(rect)
        self.lines: List[Line] = [Line(t) for t in text.split('\n')]
        self.placeholder = placeholder

        self.bg_color = bg_color
        self.hover_color = hover_color
        self.clicked_color = clicked_color
        self.border_color = border_color
        self.text_color = text_color
        self.border_width = 2
        self.padding = 5

        self.cursor: Cursor = self.end_cursor()
        self.selection_start: Optional[Cursor] = None  # Start of text selection
        self.is_focused: bool = False  # Whether the field is focused
        self.mouse_down: bool = False  # For tracking drag selection
        self.scroll_offset: int = 0  # Vertical scroll offset (in lines)

        self.font = load_font()
        self.line_height = self.font.get_height() if self.font else 20

        self._wrap_text()

    def end_cursor(self) -> Cursor:
        if not self.lines:
            return Cursor(0, 0, 0)
        line = self.lines[-1]
        line_index = len(self.lines) - 1
        if not line.paragraphs:
            return Cursor(line_index, 0, 0)
        paragraph = line.paragraphs[-1]
        paragraph_index = len(line.paragraphs)-1
        return Cursor(line_index, paragraph_index, len(paragraph))

    def _wrap_text(self):
        """
        Wrap text to fit within max_width, breaking at word boundaries.
        """
        max_width = self.rect.width - 2 * self.padding
        for line_index, line in enumerate(self.lines):
            if line_index == self.cursor.line_index:
                self.cursor = line.auto_wrap_and_norm_cursor(self.font, max_width, self.cursor)
            else:
                line.auto_wrap(self.font, max_width)

    def _cursor_from_mouse_pos(self, mouse_pos: Tuple[int, int]) -> Optional[Cursor]:
        """Calculate the character index in text based on mouse position."""
        if not self.rect.collidepoint(*mouse_pos):
            return self.end_cursor()

        if not self.lines:
            return Cursor(0, 0, 0)

        rel_x = mouse_pos[0] - self.rect.x - self.padding
        rel_y = mouse_pos[1] - self.rect.y - self.padding

        # Calculate line index based on Y position and scroll
        line_par = self._get_line_and_paragraph_by_y(rel_y)
        if line_par is None:
            return self.end_cursor()
        line_index, paragraph_index = line_par

        line = self.lines[line_index]
        paragraph = line.paragraphs[paragraph_index]

        # Find which paragraph the click is in based on X position
        for num_chars in range(len(paragraph) + 1):
            text = paragraph[:num_chars]
            paragraph_width = self.font.size(text)[0]
            if paragraph_width > rel_x:
                # TODO: num_chars + 1?
                return Cursor(line_index, paragraph_index, num_chars)

        # If click is past all paragraphs, return end of last paragraph
        return Cursor(line_index, paragraph_index, len(paragraph))

    def _get_view_line_pos(self, cursor: Cursor) -> int:
        view_line_pos = 0
        for line in self.lines[:cursor.line_index]:
            view_line_pos += line.num_paragraphs()
        return view_line_pos + cursor.paragraph_index

    def _get_num_paragraphs(self) -> int:
        return sum(l.num_paragraphs() for l in self.lines)

    def _get_line_and_paragraph_by_y(self, ypos: int) -> Optional[Tuple[int, int]]:
        view_line_index = self.scroll_offset + ypos // self.line_height

        start_line_index = 0
        for line_index, line in enumerate(self.lines):
            end_line_index = start_line_index + line.num_paragraphs()
            if view_line_index < end_line_index:
                paragraph_index = view_line_index - start_line_index
                return line_index, paragraph_index
            start_line_index = end_line_index

        # out of region
        return None

    def handle_event(self, event: pg.event.Event):
        super().handle_event(event)

        # Handle mouse button down - start selection
        if event.type == pg.MOUSEBUTTONDOWN and event.button == 1:
            if self.is_hovered:
                self.is_focused = True
                cursor = self._cursor_from_mouse_pos(event.pos)
                if cursor is not None:
                    self.cursor = cursor
                self.selection_start = self.cursor
                self.mouse_down = True
            else:
                self.is_focused = False
                self.selection_start = None

        # Handle mouse drag - update selection
        if event.type == pg.MOUSEMOTION:
            if self.mouse_down and pg.mouse.get_pressed()[0]:
                if self.is_hovered or self.is_focused:
                    cursor = self._cursor_from_mouse_pos(event.pos)
                    if cursor is not None:
                        self.cursor = cursor

        # Handle mouse button up - finish selection
        if event.type == pg.MOUSEBUTTONUP and event.button == 1:
            if self.mouse_down:
                if self.selection_start == self.cursor:
                    self.selection_start = None
            self.mouse_down = False

        # Handle scroll wheel
        if event.type == pg.MOUSEWHEEL and self.is_hovered:
            self.scroll_offset = max(0, self.scroll_offset - event.y)
            self._clamp_scroll()

        # Handle keyboard input only if focused
        if self.is_focused:
            if event.type == pg.KEYDOWN:
                ctrl_pressed = bool(event.mod & pg.KMOD_CTRL)
                shift_pressed = bool(event.mod & pg.KMOD_SHIFT)

                if event.key == pg.K_RETURN:
                    self._create_newline()
                elif event.key == pg.K_BACKSPACE:
                    self._delete_direction(-1, ctrl_pressed)
                elif event.key == pg.K_DELETE:
                    self._delete_direction(1, ctrl_pressed)
                elif event.key == pg.K_LEFT:
                    self._move_my_cursor(-1, ctrl_pressed, shift_pressed)
                elif event.key == pg.K_RIGHT:
                    self._move_my_cursor(1, ctrl_pressed, shift_pressed)
                elif event.key == pg.K_UP:
                    self._move_my_cursor_vertical(-1, shift_pressed)
                elif event.key == pg.K_DOWN:
                    self._move_my_cursor_vertical(1, shift_pressed)
                elif event.key == pg.K_HOME:
                    self._move_cursor_home(shift_pressed, ctrl_pressed)
                elif event.key == pg.K_END:
                    self._move_cursor_end(shift_pressed, ctrl_pressed)
                elif event.key == pg.K_a and ctrl_pressed:
                    self._select_all()
                elif event.key == pg.K_c and ctrl_pressed:
                    self._copy_to_clipboard()
                elif event.key == pg.K_v and ctrl_pressed:
                    self._paste_from_clipboard()
                elif event.key == pg.K_x and ctrl_pressed:
                    self._cut_to_clipboard()
                elif event.unicode and event.unicode.isprintable():
                    self._insert_text(event.unicode)

    def _get_line(self, cursor: Cursor) -> Line:
        return self.lines[cursor.line_index]

    def _get_paragraph(self, cursor: Union[Cursor, Tuple[int, int]]) -> str:
        if isinstance(cursor, Cursor):
            return self._get_line(cursor).paragraphs[cursor.paragraph_index]
        elif isinstance(cursor, tuple):
            return self.lines[cursor[0]].paragraphs[cursor[1]]
        else:
            raise ValueError(f"Invalid cursor type: {type(cursor)}")

    def _create_newline(self):
        """Split a line into two."""
        line_index = self.cursor.line_index
        orig_line = self.lines[line_index]
        left_line, right_line = orig_line.split(self.cursor.paragraph_index, self.cursor.char_index)

        max_width = self.rect.width - 2 * self.padding
        left_line.auto_wrap(self.font, max_width)
        right_line.auto_wrap(self.font, max_width)

        self.lines[line_index] = left_line
        self.lines.insert(line_index + 1, right_line)

        self.cursor = Cursor(line_index + 1, 0, 0)

    @staticmethod
    def _next_char_index(paragraph: str, char_index: int, direction: int, jump_words: bool) -> int:
        """Return the index of the next character in the given paragraph."""
        if not jump_words:
            return char_index + direction

        if direction > 0:
            if char_index == len(paragraph):
                return len(paragraph) + 1
            new_index = paragraph.find(' ', char_index+1)
            if new_index == -1:
                return len(paragraph)
            return new_index
        elif direction < 0:
            if char_index == 0:
                return -1
            new_index = paragraph.rfind(' ', 0, char_index)
            if new_index == -1:
                return 0
            return new_index
        else:
            raise ValueError("Invalid direction")

    def _move_my_cursor(self, direction: int, jump_words: bool = False, select: bool = False):
        """Move the cursor in the direction given by the given direction."""
        self._save_selection_start(select)
        self._move_cursor(self.cursor, direction, jump_words)
        self._update_scroll()

    def _move_cursor(self, cursor: Cursor, direction: int, jump_words: bool = False):
        """
        Modifies the given cursor moving in the given direction (-1 or 1).
        If jump_words is True, the cursor will jump over words.
        """
        wrap_back = False
        wrap_forward = False
        new_line_index = cursor.line_index
        new_paragraph_index = cursor.paragraph_index
        new_char_index = TextField._next_char_index(
            self._get_paragraph(cursor), cursor.char_index, direction, jump_words
        )
        if new_char_index < 0 or new_char_index > len(self._get_paragraph(cursor)):
            wrap_back = new_char_index < 0
            wrap_forward = new_char_index > len(self._get_paragraph(cursor))
            new_paragraph_index = cursor.paragraph_index + direction
            current_line = self._get_line(cursor)
            if new_paragraph_index < 0 or new_paragraph_index >= current_line.num_paragraphs():
                new_line_index = cursor.line_index + direction
                if new_line_index < 0 or new_line_index >= len(self.lines):
                    return
                if new_paragraph_index < 0:
                    new_paragraph_index = self.lines[new_line_index].num_paragraphs() - 1
                elif new_paragraph_index >= current_line.num_paragraphs():
                    new_paragraph_index = 0
        if wrap_forward:
            new_char_index = 0
        if wrap_back:
            new_char_index = len(self._get_paragraph((new_line_index, new_paragraph_index)))

        cursor.line_index = new_line_index
        cursor.paragraph_index = new_paragraph_index
        cursor.char_index = new_char_index

    def _update_scroll(self):
        """Update scroll offset to keep cursor visible."""
        visible_height = self.rect.height - 2 * self.padding
        visible_lines = max(1, int(visible_height / self.line_height))

        cursor_line = self._get_view_line_pos(self.cursor)

        # Scroll down if cursor is below visible area
        if cursor_line >= self.scroll_offset + visible_lines:
            self.scroll_offset = cursor_line - visible_lines + 1

        # Scroll up if cursor is above visible area
        if cursor_line < self.scroll_offset:
            self.scroll_offset = cursor_line

        self._clamp_scroll()

    def _clamp_scroll(self):
        """Ensure scroll offset is within valid bounds."""
        visible_height = self.rect.height - 2 * self.padding
        visible_lines = max(1, int(visible_height / self.line_height))

        max_scroll = max(0, self._get_num_paragraphs() - visible_lines)
        self.scroll_offset = max(0, min(self.scroll_offset, max_scroll))

    def _insert_text(self, char: str):
        """Insert a character at the cursor position."""
        self._delete_selection()

        # insert text
        paragraph = self._get_paragraph(self.cursor)
        paragraph = paragraph[:self.cursor.char_index] + char + paragraph[self.cursor.char_index:]
        line = self.lines[self.cursor.line_index]
        line.paragraphs[self.cursor.paragraph_index] = paragraph

        # wrap line
        self._wrap_text()

        # handle cursor
        self.cursor.char_index += len(char)
        self.selection_start = None
        self._update_scroll()

    def _move_my_cursor_vertical(self, direction: int, select: bool = False):
        """Move the cursor vertically in the direction given by the given direction."""
        self._save_selection_start(select)
        self.cursor = self._move_cursor_vertical(self.cursor, direction)
        self._update_scroll()

    def _move_cursor_vertical(self, cursor: Cursor, direction: int) -> Cursor:
        new_paragraph_index = cursor.paragraph_index + direction
        new_line_index = cursor.line_index
        new_char_index = cursor.char_index

        if new_paragraph_index < 0 or new_paragraph_index >= self._get_line(cursor).num_paragraphs():
            new_line_index += direction
            if new_line_index < 0:
                new_line_index = 0
                new_paragraph_index = 0
                new_char_index = 0
            elif new_line_index >= len(self.lines):
                new_line_index = len(self.lines) - 1
                new_paragraph_index = self.lines[new_line_index].num_paragraphs() - 1
                new_char_index = len(self._get_paragraph((new_line_index, new_paragraph_index)))
            else:
                if new_paragraph_index < 0:
                    new_paragraph_index = self.lines[new_line_index].num_paragraphs() - 1
                elif new_paragraph_index >= self._get_line(cursor).num_paragraphs():
                    new_paragraph_index = 0

        return self._clamp_cursor(Cursor(new_line_index, new_paragraph_index, new_char_index))


    def _move_cursor_home(self, select: bool, ctrl_pressed: bool):
        """Move cursor to start of line or start of text."""
        self._save_selection_start(select)

        if ctrl_pressed:
            # Move to start of text
            self.cursor = Cursor(0, 0, 0)
        else:
            # Move to start of current wrapped line
            self.cursor.char_index = 0

        self._update_scroll()

    def _save_selection_start(self, select: bool):
        if select:
            if self.selection_start is None:
                self.selection_start = self.cursor.copy()
        else:
            self.selection_start = None

    def _move_cursor_end(self, select: bool, ctrl_pressed: bool):
        """Move cursor to end of line or end of text."""
        self._save_selection_start(select)

        if ctrl_pressed:
            # Move to end of text
            self.cursor = self.end_cursor()
        else:
            # Move to end of current wrapped line
            self.cursor.char_index = len(self._get_paragraph(self.cursor))

        self._update_scroll()

    def _clamp_cursor(self, cursor: Cursor) -> Cursor:
        """Ensure cursor is within valid bounds."""
        new_cursor = cursor.copy()
        if new_cursor.line_index >= len(self.lines):
            new_cursor.line_index = len(self.lines) - 1
            new_cursor.paragraph_index = max(0, self.lines[new_cursor.line_index].num_paragraphs() - 1)
            new_cursor.char_index = len(self._get_paragraph(new_cursor))
        elif new_cursor.paragraph_index >= self.lines[new_cursor.line_index].num_paragraphs():
            new_cursor.paragraph_index = self.lines[new_cursor.line_index].num_paragraphs() - 1
            new_cursor.char_index = len(self._get_paragraph(new_cursor))
        elif new_cursor.char_index > len(self._get_paragraph(new_cursor)):
            new_cursor.char_index = len(self._get_paragraph(new_cursor))

        return new_cursor

    def _delete_direction(self, direction: int, jump_words: bool = False):
        """Remove a character in the given direction."""
        if self.selection_start is not None:
            self._delete_selection()
        else:
            target_cursor = self.cursor.copy()
            self._move_cursor(target_cursor, direction, jump_words)
            self._delete(self.cursor, target_cursor)
            self.cursor = min(target_cursor, self.cursor)

    def _get_selection_range(self) -> Tuple[Cursor, Cursor]:
        """Get the start and end of the current selection (ordered)."""
        if self.selection_start is None:
            return self.cursor, self.cursor
        return min(self.selection_start, self.cursor), max(self.selection_start, self.cursor)

    def _delete_selection(self) -> bool:
        """Delete selected text if any. Returns True if text was deleted."""
        start, end = self._get_selection_range()
        if start != end:
            self._delete(start, end)
            self.cursor = start
            self.selection_start = None
            return True
        return False

    def _delete(self, start: Cursor, end: Cursor):
        """Delete text between both cursors."""
        if end < start:
            start, end = end, start
        max_width = self.rect.width - 2 * self.padding

        if start.line_index == end.line_index:
            line = self._get_line(start)
            line.delete(start, end)
            line.auto_wrap(self.font, max_width)
        else:
            new_lines = self.lines[:start.line_index].copy()

            last_start_line = self.lines[start.line_index]
            last_start_line.delete(start, last_start_line.end())

            first_end_line = self.lines[end.line_index]
            first_end_line.delete((0, 0), end)

            middle_line = Line(last_start_line.paragraphs + first_end_line.paragraphs)
            middle_line.ensure_paragraph()
            middle_line.auto_wrap(self.font, max_width)
            new_lines.append(middle_line)

            new_lines.extend(self.lines[end.line_index + 1:])
            self.lines = new_lines
        self.cursor = self._clamp_cursor(start)

    def _select_all(self):
        """Select all text."""
        self.selection_start = Cursor(0, 0, 0)
        self.cursor = self.end_cursor()

    def _copy_to_clipboard(self):
        """Copy selected text to clipboard."""
        start, end = self._get_selection_range()
        if start != end:
            text = '\n'.join(self.iter_paragraphs(start, end))
            pg.scrap.put(SCRAP_TEXT, text.encode('utf-8'))

    def iter_paragraphs(self, start: Cursor, stop: Cursor) -> Iterable[str]:
        """Iterate over paragraphs between start and stop cursors."""
        for line_index in range(start.line_index, stop.line_index + 1):
            paragraphs = self.lines[line_index].paragraphs
            if line_index == stop.line_index:
                paragraphs = paragraphs[:stop.paragraph_index + 1]
            if line_index == start.line_index:
                paragraphs = paragraphs[start.paragraph_index:]
            for p_index, paragraph in enumerate(paragraphs):
                if p_index == stop.paragraph_index:
                    paragraph = paragraph[:stop.char_index]
                if p_index == start.paragraph_index:
                    paragraph = paragraph[start.char_index:]
                yield paragraph

    def _paste_from_clipboard(self):
        """Paste text from clipboard."""
        try:
            clipboard_text = pg.scrap.get(SCRAP_TEXT).decode('utf-8')
            if clipboard_text:
                clipboard_text = clipboard_text.split('\n')
                for i, line in enumerate(clipboard_text):
                    if i == 0:
                        self._insert_text(clipboard_text[0])
                    elif i == len(clipboard_text) - 1:
                        self._create_newline()
                        self._insert_text(line)
        except pg.error:
            pass

    def _cut_to_clipboard(self):
        """Cut selected text to clipboard."""
        self._copy_to_clipboard()
        self._delete_selection()

    def draw(self, screen: pg.Surface, render_context: RenderContext):
        # Draw background
        if self.is_focused:
            color = self.clicked_color
        elif self.is_hovered:
            color = self.hover_color
        else:
            color = self.bg_color
        pg.draw.rect(screen, color, self.rect)

        # Draw border
        border_width = self.border_width + 1 if self.is_focused else self.border_width
        pg.draw.rect(screen, self.border_color, self.rect, border_width)

        # Text rendering area with padding
        text_area = pg.Rect(
            self.rect.left + self.padding,
            self.rect.top + self.padding,
            self.rect.width - 2 * self.padding,
            self.rect.height - 2 * self.padding
        )

        # Set clipping region
        clip_rect = screen.get_clip()
        screen.set_clip(text_area)

        # Draw text or placeholder
        y_pos = text_area.top + self.padding
        selection_start, selection_end = self._get_selection_range()
        for line_index, line in enumerate(self.lines):
            for paragraph_index, paragraph in enumerate(line.paragraphs):
                self._draw_selection(
                    line_index, paragraph, paragraph_index, screen, selection_end, selection_start, text_area, y_pos
                )

                text_surface = self.font.render(paragraph, True, self.text_color)
                screen.blit(text_surface, (text_area.left, y_pos))

                self.draw_cursor(screen, line_index, paragraph, paragraph_index, y_pos, text_area)

                y_pos += self.line_height

        # Restore clip rect
        screen.set_clip(clip_rect)

    def _draw_selection(
            self, line_index: int, paragraph: str, paragraph_index: int, screen: pg.Surface, selection_end: Cursor,
            selection_start: Cursor, text_area: pg.Rect, y_pos: int
    ):
        if self.selection_start is None:
            return
        if line_index < selection_start.line_index or line_index > selection_end.line_index:
            return
        if line_index == selection_start.line_index and paragraph_index < selection_start.paragraph_index:
            return
        if line_index == selection_end.line_index and paragraph_index > selection_end.paragraph_index:
            return
        start_char_index = 0
        if selection_start.line_index == line_index and selection_start.paragraph_index == paragraph_index:
            start_char_index = selection_start.char_index

        end_char_index = len(paragraph)
        if selection_end.line_index == line_index and selection_end.paragraph_index == paragraph_index:
            end_char_index = selection_end.char_index

        highlight_offset = self.font.size(paragraph[:start_char_index])[0]
        highlight_width = self.font.size(paragraph[start_char_index:end_char_index])[0]
        selection_rect = pg.Rect(
            text_area.left + highlight_offset, y_pos,
            highlight_width, self.line_height
        )
        pg.draw.rect(screen, (100, 150, 200), selection_rect)

    def draw_cursor(self, screen: pg.Surface, line_index: int, paragraph: str, paragraph_index: int, y_pos: int, text_area: pg.Rect):
        if self.is_focused:
            cursor_visible = (pg.time.get_ticks() // 500) % 2 == 0
            if cursor_visible:
                if self.cursor.line_index == line_index and self.cursor.paragraph_index == paragraph_index:
                    x_pos = text_area.left + self.font.size(paragraph[:self.cursor.char_index])[0]
                    pg.draw.line(screen, self.text_color, (x_pos, y_pos), (x_pos, y_pos + self.line_height), 2)
