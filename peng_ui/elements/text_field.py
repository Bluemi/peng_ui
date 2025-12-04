from typing import Optional, Tuple, List

import pygame as pg

from peng_ui.elements.base_element import BaseElement
from peng_ui.utils import RenderContext, ColorType, load_font

SCRAP_TEXT = 'text/plain;charset=utf-8'


class TextField(BaseElement):
    def __init__(
            self, rect: pg.Rect, text: str = "", placeholder: str = "",
            bg_color: ColorType = (40, 40, 40), hover_color: ColorType = (60, 60, 60),
            clicked_color: ColorType = (90, 90, 100), border_color: ColorType = (140, 140, 140),
            text_color: ColorType = (200, 200, 200)
    ):
        super().__init__(rect)
        self.text = text
        self.placeholder = placeholder

        self.bg_color = bg_color
        self.hover_color = hover_color
        self.clicked_color = clicked_color
        self.border_color = border_color
        self.text_color = text_color
        self.border_width = 2

        self.cursor_pos: int = len(text)  # Cursor position in text
        self.selection_start: Optional[int] = None  # Start of text selection
        self.is_focused: bool = False  # Whether the field is focused
        self.mouse_down_pos: Optional[int] = None  # For tracking drag selection
        self.scroll_offset: int = 0  # Vertical scroll offset (in lines)

        self.font = load_font()
        self.line_height = self.font.get_height() if self.font else 20

    def _get_lines(self) -> List[str]:
        """Split text into lines."""
        if not self.text:
            return [""]
        return self.text.split('\n')

    def _wrap_text(self, text: str, max_width: int) -> List[str]:
        """
        Wrap text to fit within max_width, breaking at word boundaries.
        Returns a list of wrapped lines.
        """
        if not text:
            return [""]

        wrapped_lines = []
        paragraphs = text.split('\n')

        for paragraph in paragraphs:
            if not paragraph:
                wrapped_lines.append("")
                continue

            words = paragraph.split(' ')
            current_line = ""

            for word in words:
                # Test if adding this word would exceed max width
                test_line = current_line + (" " if current_line else "") + word
                test_width = self.font.size(test_line)[0]

                if test_width <= max_width:
                    # Word fits on current line
                    current_line = test_line
                else:
                    # Word doesn't fit
                    if current_line:
                        # Save current line and start new one
                        wrapped_lines.append(current_line)
                        current_line = word
                    else:
                        # Single word is too long, force it on its own line
                        wrapped_lines.append(word)
                        current_line = ""

            # Add the last line of this paragraph
            if current_line:
                wrapped_lines.append(current_line)

        return wrapped_lines if wrapped_lines else [""]

    def _get_wrapped_lines(self) -> List[str]:
        """Get text lines with word wrapping applied."""
        padding = 5
        max_width = self.rect.width - 2 * padding
        return self._wrap_text(self.text, max_width)

    def _get_cursor_line_col_wrapped(self) -> Tuple[int, int]:
        """
        Get the line and column position of the cursor in wrapped text.
        Returns (wrapped_line_index, column_in_wrapped_line).
        """
        wrapped_lines = self._get_wrapped_lines()
        pos = 0

        for wrapped_line_idx, wrapped_line in enumerate(wrapped_lines):
            line_len = len(wrapped_line)

            # Check if cursor is in this wrapped line
            if pos + line_len >= self.cursor_pos:
                col = self.cursor_pos - pos
                return wrapped_line_idx, col

            # For simplicity, add 1 for space unless it's the last word of a paragraph
            chars_so_far = pos + line_len
            if chars_so_far < len(self.text):
                next_char = self.text[chars_so_far]
                if next_char == '\n':
                    pos += line_len + 1  # +1 for newline
                elif next_char == ' ':
                    pos += line_len + 1  # +1 for space
                else:
                    pos += line_len
            else:
                pos += line_len

        # Cursor at end
        return len(wrapped_lines) - 1, len(wrapped_lines[-1]) if wrapped_lines else 0

    def _get_pos_from_wrapped_line_col(self, wrapped_line: int, col: int) -> int:
        """Convert wrapped line and column to absolute position in original text."""
        wrapped_lines = self._get_wrapped_lines()
        pos = 0

        for i in range(min(wrapped_line, len(wrapped_lines))):
            line_len = len(wrapped_lines[i])
            pos += line_len

            # Add separator (space or newline) if not at end
            if pos < len(self.text):
                next_char = self.text[pos]
                if next_char in (' ', '\n'):
                    pos += 1

        # Add column offset
        if wrapped_line < len(wrapped_lines):
            pos += min(col, len(wrapped_lines[wrapped_line]))

        return min(pos, len(self.text))

    def _get_char_index_at_pos(self, pos: Tuple[int, int]) -> int:
        """Calculate the character index in text based on mouse position."""
        padding = 5
        rel_x = pos[0] - self.rect.x - padding
        rel_y = pos[1] - self.rect.y - padding

        # Calculate which wrapped line was clicked
        line_idx = self.scroll_offset + int(rel_y / self.line_height)
        wrapped_lines = self._get_wrapped_lines()

        if line_idx < 0:
            return 0
        if line_idx >= len(wrapped_lines):
            return len(self.text)

        # Find the column in that wrapped line
        line_text = wrapped_lines[line_idx]
        if not line_text or rel_x <= 0:
            return self._get_pos_from_wrapped_line_col(line_idx, 0)

        # Find the closest character position in the line
        for i in range(len(line_text) + 1):
            text_width = self.font.size(line_text[:i])[0]
            if rel_x <= text_width:
                if i > 0:
                    prev_width = self.font.size(line_text[:i - 1])[0]
                    if rel_x - prev_width < text_width - rel_x:
                        return self._get_pos_from_wrapped_line_col(line_idx, i - 1)
                return self._get_pos_from_wrapped_line_col(line_idx, i)

        return self._get_pos_from_wrapped_line_col(line_idx, len(line_text))

    def handle_event(self, event: pg.event.Event):
        super().handle_event(event)

        # Handle mouse button down - start selection
        if event.type == pg.MOUSEBUTTONDOWN and event.button == 1:
            if self.is_hovered:
                self.is_focused = True
                self.cursor_pos = self._get_char_index_at_pos(event.pos)
                self.selection_start = self.cursor_pos
                self.mouse_down_pos = self.cursor_pos
            else:
                self.is_focused = False
                self.selection_start = None

        # Handle mouse drag - update selection
        if event.type == pg.MOUSEMOTION:
            if self.mouse_down_pos is not None and pg.mouse.get_pressed()[0]:
                if self.is_hovered or self.is_focused:
                    self.cursor_pos = self._get_char_index_at_pos(event.pos)

        # Handle mouse button up - finish selection
        if event.type == pg.MOUSEBUTTONUP and event.button == 1:
            if self.mouse_down_pos is not None:
                if self.selection_start == self.cursor_pos:
                    self.selection_start = None
            self.mouse_down_pos = None

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
                    self._insert_text('\n')
                elif event.key == pg.K_BACKSPACE:
                    self._handle_backspace(ctrl_pressed)
                elif event.key == pg.K_DELETE:
                    self._handle_delete(ctrl_pressed)
                elif event.key == pg.K_LEFT:
                    if ctrl_pressed:
                        self._move_cursor_word_left(shift_pressed)
                    else:
                        self._move_cursor_left(shift_pressed)
                elif event.key == pg.K_RIGHT:
                    if ctrl_pressed:
                        self._move_cursor_word_right(shift_pressed)
                    else:
                        self._move_cursor_right(shift_pressed)
                elif event.key == pg.K_UP:
                    self._move_cursor_up(shift_pressed)
                elif event.key == pg.K_DOWN:
                    self._move_cursor_down(shift_pressed)
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

    def _find_word_start(self, pos: int) -> int:
        """Find the start position of the word at or before the given position."""
        if pos == 0:
            return 0

        # Move back to skip whitespace
        while pos > 0 and self.text[pos - 1].isspace() and self.text[pos - 1] != '\n':
            pos -= 1

        # Move back to the start of the previous word
        while pos > 0 and not self.text[pos - 1].isspace():
            pos -= 1

        return pos

    def _find_word_end(self, pos: int) -> int:
        """Find the end position of the word at or after the given position."""
        text_len = len(self.text)

        if pos >= text_len:
            return text_len

        # Move forward to skip whitespace (but not newlines for word boundaries)
        while pos < text_len and self.text[pos].isspace() and self.text[pos] != '\n':
            pos += 1

        # Move forward to the end of the current word
        while pos < text_len and not self.text[pos].isspace():
            pos += 1

        return pos

    def _update_scroll(self):
        """Update scroll offset to keep cursor visible."""
        padding = 5
        visible_height = self.rect.height - 2 * padding
        visible_lines = max(1, int(visible_height / self.line_height))

        cursor_line, _ = self._get_cursor_line_col_wrapped()

        # Scroll down if cursor is below visible area
        if cursor_line >= self.scroll_offset + visible_lines:
            self.scroll_offset = cursor_line - visible_lines + 1

        # Scroll up if cursor is above visible area
        if cursor_line < self.scroll_offset:
            self.scroll_offset = cursor_line

        self._clamp_scroll()

    def _clamp_scroll(self):
        """Ensure scroll offset is within valid bounds."""
        wrapped_lines = self._get_wrapped_lines()
        padding = 5
        visible_height = self.rect.height - 2 * padding
        visible_lines = max(1, int(visible_height / self.line_height))

        max_scroll = max(0, len(wrapped_lines) - visible_lines)
        self.scroll_offset = max(0, min(self.scroll_offset, max_scroll))

    def _insert_text(self, char: str):
        """Insert a character at the cursor position."""
        self._delete_selection()
        self.text = self.text[:self.cursor_pos] + char + self.text[self.cursor_pos:]
        self.cursor_pos += len(char)
        self.selection_start = None
        self._update_scroll()

    def _move_cursor_left(self, shift_pressed: bool):
        """Move cursor left, optionally extending selection."""
        if shift_pressed:
            if self.selection_start is None:
                self.selection_start = self.cursor_pos
            if self.cursor_pos > 0:
                self.cursor_pos -= 1
        else:
            if self.selection_start is not None:
                self.cursor_pos = min(self.selection_start, self.cursor_pos)
                self.selection_start = None
            elif self.cursor_pos > 0:
                self.cursor_pos -= 1
        self._update_scroll()

    def _move_cursor_right(self, shift_pressed: bool):
        """Move cursor right, optionally extending selection."""
        if shift_pressed:
            if self.selection_start is None:
                self.selection_start = self.cursor_pos
            if self.cursor_pos < len(self.text):
                self.cursor_pos += 1
        else:
            if self.selection_start is not None:
                self.cursor_pos = max(self.selection_start, self.cursor_pos)
                self.selection_start = None
            elif self.cursor_pos < len(self.text):
                self.cursor_pos += 1
        self._update_scroll()

    def _move_cursor_up(self, shift_pressed: bool):
        """Move cursor up one line."""
        if shift_pressed and self.selection_start is None:
            self.selection_start = self.cursor_pos

        line, col = self._get_cursor_line_col_wrapped()
        if line > 0:
            wrapped_lines = self._get_wrapped_lines()
            new_col = min(col, len(wrapped_lines[line - 1]))
            self.cursor_pos = self._get_pos_from_wrapped_line_col(line - 1, new_col)

        if not shift_pressed:
            self.selection_start = None
        self._update_scroll()

    def _move_cursor_down(self, shift_pressed: bool):
        """Move cursor down one line."""
        if shift_pressed and self.selection_start is None:
            self.selection_start = self.cursor_pos

        line, col = self._get_cursor_line_col_wrapped()
        wrapped_lines = self._get_wrapped_lines()
        if line < len(wrapped_lines) - 1:
            new_col = min(col, len(wrapped_lines[line + 1]))
            self.cursor_pos = self._get_pos_from_wrapped_line_col(line + 1, new_col)

        if not shift_pressed:
            self.selection_start = None
        self._update_scroll()

    def _move_cursor_home(self, shift_pressed: bool, ctrl_pressed: bool):
        """Move cursor to start of line or start of text."""
        if shift_pressed and self.selection_start is None:
            self.selection_start = self.cursor_pos

        if ctrl_pressed:
            # Move to start of text
            self.cursor_pos = 0
        else:
            # Move to start of current wrapped line
            line, _ = self._get_cursor_line_col_wrapped()
            self.cursor_pos = self._get_pos_from_wrapped_line_col(line, 0)

        if not shift_pressed:
            self.selection_start = None
        self._update_scroll()

    def _move_cursor_end(self, shift_pressed: bool, ctrl_pressed: bool):
        """Move cursor to end of line or end of text."""
        if shift_pressed and self.selection_start is None:
            self.selection_start = self.cursor_pos

        if ctrl_pressed:
            # Move to end of text
            self.cursor_pos = len(self.text)
        else:
            # Move to end of current wrapped line
            line, _ = self._get_cursor_line_col_wrapped()
            wrapped_lines = self._get_wrapped_lines()
            self.cursor_pos = self._get_pos_from_wrapped_line_col(line, len(wrapped_lines[line]))

        if not shift_pressed:
            self.selection_start = None
        self._update_scroll()

    def _move_cursor_word_left(self, shift_pressed: bool):
        """Move cursor to the start of the previous word."""
        if shift_pressed and self.selection_start is None:
            self.selection_start = self.cursor_pos

        self.cursor_pos = self._find_word_start(self.cursor_pos)

        if not shift_pressed:
            self.selection_start = None
        self._update_scroll()

    def _move_cursor_word_right(self, shift_pressed: bool):
        """Move cursor to the end of the current/next word."""
        if shift_pressed and self.selection_start is None:
            self.selection_start = self.cursor_pos

        self.cursor_pos = self._find_word_end(self.cursor_pos)

        if not shift_pressed:
            self.selection_start = None
        self._update_scroll()

    def _handle_backspace(self, ctrl_pressed: bool = False):
        """Handle backspace key."""
        if not self._delete_selection():
            if ctrl_pressed:
                new_pos = self._find_word_start(self.cursor_pos)
                if new_pos < self.cursor_pos:
                    self.text = self.text[:new_pos] + self.text[self.cursor_pos:]
                    self.cursor_pos = new_pos
            elif self.cursor_pos > 0:
                self.text = self.text[:self.cursor_pos - 1] + self.text[self.cursor_pos:]
                self.cursor_pos -= 1
        self._update_scroll()

    def _handle_delete(self, ctrl_pressed: bool = False):
        """Handle delete key."""
        if not self._delete_selection():
            if ctrl_pressed:
                new_pos = self._find_word_end(self.cursor_pos)
                if new_pos > self.cursor_pos:
                    self.text = self.text[:self.cursor_pos] + self.text[new_pos:]
            elif self.cursor_pos < len(self.text):
                self.text = self.text[:self.cursor_pos] + self.text[self.cursor_pos + 1:]
        self._update_scroll()

    def _get_selection_range(self) -> Tuple[int, int]:
        """Get the start and end of the current selection (ordered)."""
        if self.selection_start is None:
            return self.cursor_pos, self.cursor_pos
        return min(self.selection_start, self.cursor_pos), max(self.selection_start, self.cursor_pos)

    def _delete_selection(self) -> bool:
        """Delete selected text if any. Returns True if text was deleted."""
        start, end = self._get_selection_range()
        if start != end:
            self.text = self.text[:start] + self.text[end:]
            self.cursor_pos = start
            self.selection_start = None
            return True
        return False

    def _select_all(self):
        """Select all text."""
        self.selection_start = 0
        self.cursor_pos = len(self.text)

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
        padding = 5
        text_area = pg.Rect(
            self.rect.left + padding,
            self.rect.top + padding,
            self.rect.width - 2 * padding,
            self.rect.height - 2 * padding
        )

        # Set clipping region
        clip_rect = screen.get_clip()
        screen.set_clip(text_area)

        wrapped_lines = self._get_wrapped_lines()
        visible_lines = max(1, int(text_area.height / self.line_height))

        # Draw text or placeholder
        if self.text:
            # Draw visible wrapped lines
            for i in range(self.scroll_offset, min(len(wrapped_lines), self.scroll_offset + visible_lines)):
                line_text = wrapped_lines[i]
                y_pos = text_area.top + (i - self.scroll_offset) * self.line_height

                # Get line start position in original text
                line_start_pos = self._get_pos_from_wrapped_line_col(i, 0)
                line_end_pos = self._get_pos_from_wrapped_line_col(i, len(line_text))

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

                # Draw line text
                if line_text:
                    text_surface = self.font.render(line_text, True, self.text_color)
                    screen.blit(text_surface, (text_area.left, y_pos))

        elif not self.is_focused and self.placeholder:
            # Draw placeholder with wrapping
            placeholder_wrapped = self._wrap_text(self.placeholder, text_area.width)
            placeholder_color = (100, 100, 100)
            for i, line in enumerate(placeholder_wrapped[:visible_lines]):
                y_pos = text_area.top + i * self.line_height
                placeholder_surface = self.font.render(line, True, placeholder_color)
                screen.blit(placeholder_surface, (text_area.left, y_pos))

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

        # Restore clip rect
        screen.set_clip(clip_rect)
