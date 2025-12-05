from typing import Optional, Tuple, List, Union

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

    def __repr__(self):
        return f'Cursor({self.line_index}, {self.paragraph_index}, {self.char_index})'


class Line:
    """
    Represents a line in a text field. Can contain multiple paragraphs that are automatically wrapped.
    Each manual enter from the user will create a new Line object. Each line that is longer than the width of the
    TextField will create a new paragraph.
    """
    def __init__(self, text: str = ''):
        self.paragraphs: List[str] = [text]

    def __repr__(self):
        return f'Line({len(self.paragraphs)} paragraphs, {self.num_chars()} chars)'

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

    def auto_wrap(self, font: pg.font.Font, max_width: int):
        words = ' '.join(self.paragraphs).split(' ')
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
        left_part = middle_paragraph[:split_index]
        right_part = middle_paragraph[split_index:]
        left_paragraphs.append(left_part)
        right_paragraphs.insert(0, right_part)
        return Line(''.join(left_paragraphs)), Line(''.join(right_paragraphs))


class TextField(BaseElement):
    def __init__(
            self, rect: pg.Rect, text: str = "", placeholder: str = "",
            bg_color: ColorType = (40, 40, 40), hover_color: ColorType = (60, 60, 60),
            clicked_color: ColorType = (90, 90, 100), border_color: ColorType = (140, 140, 140),
            text_color: ColorType = (200, 200, 200)
    ):
        super().__init__(rect)
        self.text: List[Line] = [Line(t) for t in text.split('\n')]
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

    def end_cursor(self) -> Cursor:
        if not self.text:
            return Cursor(0, 0, 0)
        line = self.text[-1]
        line_index = len(self.text)-1
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
        for line_index, line in enumerate(self.text):
            if line_index == self.cursor.line_index:
                self.cursor = line.auto_wrap_and_norm_cursor(self.font, max_width, self.cursor)
            else:
                line.auto_wrap(self.font, max_width)

    def _cursor_from_mouse_pos(self, mouse_pos: Tuple[int, int]) -> Optional[Cursor]:
        """Calculate the character index in text based on mouse position."""
        if not self.rect.collidepoint(*mouse_pos):
            return self.end_cursor()

        if not self.text:
            return Cursor(0, 0, 0)

        rel_x = mouse_pos[0] - self.rect.x - self.padding
        rel_y = mouse_pos[1] - self.rect.y - self.padding

        # Calculate line index based on Y position and scroll
        line_par = self._get_line_and_paragraph_by_y(rel_y)
        if line_par is None:
            return self.end_cursor()
        line_index, paragraph_index = line_par

        line = self.text[line_index]
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
        for line in self.text[:cursor.line_index]:
            view_line_pos += line.num_paragraphs()
        return view_line_pos + cursor.paragraph_index

    def _get_num_paragraphs(self) -> int:
        return sum(l.num_paragraphs() for l in self.text)

    def _get_line_and_paragraph_by_y(self, ypos: int) -> Optional[Tuple[int, int]]:
        view_line_index = self.scroll_offset + ypos // self.line_height

        start_line_index = 0
        for line_index, line in enumerate(self.text):
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
                else:
                    print('cursor is None')
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
                    else:
                        print('cursor is None')

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
                ctrl_pressed = event.mod & pg.KMOD_CTRL
                shift_pressed = event.mod & pg.KMOD_SHIFT

                if event.key == pg.K_RETURN:
                    self._create_newline()
                # elif event.key == pg.K_BACKSPACE:
                #     self._handle_backspace(ctrl_pressed)
                # elif event.key == pg.K_DELETE:
                #     self._handle_delete(ctrl_pressed)
                elif event.key == pg.K_LEFT:
                    self._move_my_cursor(-1, ctrl_pressed)
                elif event.key == pg.K_RIGHT:
                    self._move_my_cursor(1, ctrl_pressed)
                # elif event.key == pg.K_UP:
                #     self._move_cursor_up(shift_pressed)
                # elif event.key == pg.K_DOWN:
                #     self._move_cursor_down(shift_pressed)
                # elif event.key == pg.K_HOME:
                #     self._move_cursor_home(shift_pressed, ctrl_pressed)
                # elif event.key == pg.K_END:
                #     self._move_cursor_end(shift_pressed, ctrl_pressed)
                # elif event.key == pg.K_a and ctrl_pressed:
                #     self._select_all()
                # elif event.key == pg.K_c and ctrl_pressed:
                #     self._copy_to_clipboard()
                # elif event.key == pg.K_v and ctrl_pressed:
                #     self._paste_from_clipboard()
                # elif event.key == pg.K_x and ctrl_pressed:
                #     self._cut_to_clipboard()
                elif event.unicode and event.unicode.isprintable():
                    self._insert_text(event.unicode)

    def _get_line(self, cursor: Cursor) -> Line:
        return self.text[cursor.line_index]

    def _get_paragraph(self, cursor: Union[Cursor, Tuple[int, int]]) -> str:
        if isinstance(cursor, Cursor):
            return self._get_line(cursor).paragraphs[cursor.paragraph_index]
        elif isinstance(cursor, tuple):
            return self.text[cursor[0]].paragraphs[cursor[1]]
        else:
            raise ValueError(f"Invalid cursor type: {type(cursor)}")

    def _create_newline(self):
        """Split a line into two."""
        line_index = self.cursor.line_index
        orig_line = self.text[line_index]
        left_line, right_line = orig_line.split(self.cursor.paragraph_index, self.cursor.char_index)

        self.text[line_index] = left_line
        self.text.insert(line_index + 1, right_line)

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

    def _move_my_cursor(self, direction: int, jump_words: bool = False):
        """Move the cursor in the direction given by the given direction."""
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
        new_char_index = cursor.char_index
        if not jump_words:
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
                    if new_line_index < 0 or new_line_index >= len(self.text):
                        return
                    if new_paragraph_index < 0:
                        new_paragraph_index = self.text[new_line_index].num_paragraphs() - 1
                    if new_paragraph_index >= current_line.num_paragraphs():
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
        # self._delete_selection()  # TODO

        # insert text
        paragraph = self._get_paragraph(self.cursor)
        paragraph = paragraph[:self.cursor.char_index] + char + paragraph[self.cursor.char_index:]
        line = self.text[self.cursor.line_index]
        line.paragraphs[self.cursor.paragraph_index] = paragraph

        # wrap line
        self._wrap_text()

        # handle cursor
        self.cursor.char_index += len(char)
        self.selection_start = None
        self._update_scroll()

    '''
    def _move_cursor_up(self, shift_pressed: bool):
        """Move cursor up one line."""
        if shift_pressed and self.selection_start is None:
            self.selection_start = self.cursor

        line, col = self._get_cursor_line_col_wrapped()
        if line > 0:
            wrapped_lines = self.text
            new_col = min(col, len(wrapped_lines[line - 1]))
            self.cursor = self._get_pos_from_wrapped_line_col(line - 1, new_col)

        if not shift_pressed:
            self.selection_start = None
        self._update_scroll()

    def _move_cursor_down(self, shift_pressed: bool):
        """Move cursor down one line."""
        if shift_pressed and self.selection_start is None:
            self.selection_start = self.cursor

        line, col = self._get_cursor_line_col_wrapped()
        wrapped_lines = self.text
        if line < len(wrapped_lines) - 1:
            new_col = min(col, len(wrapped_lines[line + 1]))
            self.cursor = self._get_pos_from_wrapped_line_col(line + 1, new_col)

        if not shift_pressed:
            self.selection_start = None
        self._update_scroll()

    def _move_cursor_home(self, shift_pressed: bool, ctrl_pressed: bool):
        """Move cursor to start of line or start of text."""
        if shift_pressed and self.selection_start is None:
            self.selection_start = self.cursor

        if ctrl_pressed:
            # Move to start of text
            self.cursor = 0
        else:
            # Move to start of current wrapped line
            line, _ = self._get_cursor_line_col_wrapped()
            self.cursor = self._get_pos_from_wrapped_line_col(line, 0)

        if not shift_pressed:
            self.selection_start = None
        self._update_scroll()

    def _move_cursor_end(self, shift_pressed: bool, ctrl_pressed: bool):
        """Move cursor to end of line or end of text."""
        if shift_pressed and self.selection_start is None:
            self.selection_start = self.cursor

        if ctrl_pressed:
            # Move to end of text
            self.cursor = len(self.text)
        else:
            # Move to end of current wrapped line
            line, _ = self._get_cursor_line_col_wrapped()
            wrapped_lines = self.text
            self.cursor = self._get_pos_from_wrapped_line_col(line, len(wrapped_lines[line]))

        if not shift_pressed:
            self.selection_start = None
        self._update_scroll()

    def _handle_backspace(self, ctrl_pressed: bool = False):
        """Handle backspace key."""
        if not self._delete_selection():
            if ctrl_pressed:
                new_pos = self._find_word_start(self.cursor)
                if new_pos < self.cursor:
                    self.text = self.text[:new_pos] + self.text[self.cursor:]
                    self.cursor = new_pos
            elif self.cursor > 0:
                self.text = self.text[:self.cursor - 1] + self.text[self.cursor:]
                self.cursor -= 1
        self._update_scroll()

    def _handle_delete(self, ctrl_pressed: bool = False):
        """Handle delete key."""
        if not self._delete_selection():
            if ctrl_pressed:
                new_pos = self._find_word_end(self.cursor)
                if new_pos > self.cursor:
                    self.text = self.text[:self.cursor] + self.text[new_pos:]
            elif self.cursor < len(self.text):
                self.text = self.text[:self.cursor] + self.text[self.cursor + 1:]
        self._update_scroll()

    def _get_selection_range(self) -> Tuple[int, int]:
        """Get the start and end of the current selection (ordered)."""
        if self.selection_start is None:
            return self.cursor, self.cursor
        return min(self.selection_start, self.cursor), max(self.selection_start, self.cursor)

    def _delete_selection(self) -> bool:
        """Delete selected text if any. Returns True if text was deleted."""
        start, end = self._get_selection_range()
        if start != end:
            self.text = self.text[:start] + self.text[end:]
            self.cursor = start
            self.selection_start = None
            return True
        return False

    def _select_all(self):
        """Select all text."""
        self.selection_start = 0
        self.cursor = len(self.text)

    def _copy_to_clipboard(self):
        """Copy selected text to clipboard."""
        start, end = self._get_selection_range()
        if start != end:
            pg.scrap.put(SCRAP_TEXT, self.text[start:end].encode('utf-8'))

    def _paste_from_clipboard(self):
        """Paste text from clipboard."""
        try:
            clipboard_text = pg.scrap.get(SCRAP_TEXT).decode('utf-8')
            if clipboard_text:
                self._insert_text(clipboard_text)
        except pg.error:
            pass

    def _cut_to_clipboard(self):
        """Cut selected text to clipboard."""
        start, end = self._get_selection_range()
        if start != end:
            pg.scrap.put(SCRAP_TEXT, self.text[start:end].encode('utf-8'))
            self._delete_selection()
    '''

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

        wrapped_lines = self.text
        visible_lines = max(1, int(text_area.height / self.line_height))

        # Draw text or placeholder
        y_pos = text_area.top + self.padding
        for line_index, line in enumerate(self.text):
            for paragraph_index, paragraph in enumerate(line.paragraphs):
                text_surface = self.font.render(paragraph, True, self.text_color)
                screen.blit(text_surface, (text_area.left, y_pos))

                # draw cursor
                self.draw_cursor(screen, line_index, paragraph, paragraph_index, y_pos, text_area)

                y_pos += self.line_height

                '''
                # Draw selection highlight for this line
                if self.selection_start is not None and self.is_focused:
                    sel_start, sel_end = self._get_selection_range()
                    if sel_start < line_end_pos and sel_end > line_start_pos:
                        # Calculate selection within this wrapped line
                        line_sel_start = max(0, sel_start - line_start_pos)
                        line_sel_end = min(len(line_text), sel_end - line_start_pos)

                        before_width = self.font.size(line_text[:line_sel_start])[0]
                        sel_width = self.font.size(line_text[line_sel_start:line_sel_end])[0]

                        selection_rect = pg.Rect(
                            text_area.left + before_width,
                            y_pos,
                            sel_width,
                            self.line_height
                        )
                        pg.draw.rect(screen, (100, 150, 200), selection_rect)

                '''

        '''
        elif not self.is_focused and self.placeholder:
            # Draw placeholder with wrapping
            placeholder_wrapped = self._wrap_text(self.placeholder, text_area.width)
            placeholder_color = (100, 100, 100)
            for i, line in enumerate(placeholder_wrapped[:visible_lines]):
                y_pos = text_area.top + i * self.line_height
                placeholder_surface = self.font.render(line, True, placeholder_color)
                screen.blit(placeholder_surface, (text_area.left, y_pos))
        '''

        '''
        # Draw cursor if focused
        if self.is_focused:
            cursor_visible = (pg.time.get_ticks() // 500) % 2 == 0

            if cursor_visible:
                cursor_line, cursor_col = self._get_cursor_line_col_wrapped()

                # Only draw cursor if it's in the visible area
                if self.scroll_offset <= cursor_line < self.scroll_offset + visible_lines:
                    line_text = wrapped_lines[cursor_line] if cursor_line < len(wrapped_lines) else ""
                    cursor_x = text_area.left + self.font.size(line_text[:cursor_col])[0]
                    cursor_y = text_area.top + (cursor_line - self.scroll_offset) * self.line_height

                    pg.draw.line(
                        screen,
                        self.text_color,
                        (cursor_x, cursor_y),
                        (cursor_x, cursor_y + self.line_height),
                        2
                    )
        '''

        # Restore clip rect
        screen.set_clip(clip_rect)

    def draw_cursor(self, screen: pg.Surface, line_index: int, paragraph: str, paragraph_index: int, y_pos: int, text_area: pg.Rect):
        cursor_visible = (pg.time.get_ticks() // 500) % 2 == 0
        if cursor_visible:
            if self.cursor.line_index == line_index and self.cursor.paragraph_index == paragraph_index:
                x_pos = text_area.left + self.font.size(paragraph[:self.cursor.char_index])[0]
                pg.draw.line(screen, self.text_color, (x_pos, y_pos), (x_pos, y_pos + self.line_height), 2)
