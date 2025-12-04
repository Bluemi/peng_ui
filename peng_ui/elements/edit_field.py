from typing import Optional, Tuple

import pygame as pg

from peng_ui.elements.base_element import BaseElement
from peng_ui.utils import RenderContext, ColorType, load_font

SCRAP_TEXT = 'text/plain;charset=utf-8'


class EditField(BaseElement):
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
        self.text_offset: int = 0  # Horizontal scroll offset for text

        self.font = load_font()

    def _get_char_index_at_pos(self, pos: Tuple[int, int]) -> int:
        """Calculate the character index in text based on mouse position."""
        # Convert screen position to relative position within edit field
        rel_x = pos[0] - self.rect.x - 5 + self.text_offset  # Add offset to account for scrolling

        if not self.text:
            return 0

        # If click is before text start
        if rel_x <= 0:
            return 0

        # Find the closest character position
        for i in range(len(self.text) + 1):
            text_width = self.font.size(self.text[:i])[0]
            if rel_x <= text_width:
                # Check if we're closer to previous or current position
                if i > 0:
                    prev_width = self.font.size(self.text[:i - 1])[0]
                    if rel_x - prev_width < text_width - rel_x:
                        return i - 1
                return i

        return len(self.text)

    def handle_event(self, event: pg.event.Event):
        super().handle_event(event)

        # Handle mouse button down - start selection
        if event.type == pg.MOUSEBUTTONDOWN and event.button == 1:
            if self.is_hovered:
                self.is_focused = True
                # Calculate cursor position from mouse click
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
                # If no text was selected (click without drag), clear selection
                if self.selection_start == self.cursor_pos:
                    self.selection_start = None
            self.mouse_down_pos = None

        # Handle keyboard input only if focused
        if self.is_focused:
            if event.type == pg.KEYDOWN:
                ctrl_pressed = event.mod & pg.KMOD_CTRL
                shift_pressed = event.mod & pg.KMOD_SHIFT

                # Handle text input
                if event.key == pg.K_BACKSPACE:
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
                elif event.key == pg.K_HOME:
                    self._move_cursor_home(shift_pressed)
                elif event.key == pg.K_END:
                    self._move_cursor_end(shift_pressed)
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
        while pos > 0 and self.text[pos - 1].isspace():
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

        # Move forward to skip whitespace
        while pos < text_len and self.text[pos].isspace():
            pos += 1

        # Move forward to the end of the current word
        while pos < text_len and not self.text[pos].isspace():
            pos += 1

        return pos

    def _update_text_offset(self):
        """Update text offset to keep cursor visible."""
        padding = 5
        visible_width = self.rect.width - 2 * padding

        # Calculate cursor position in text coordinates
        text_before_cursor = self.text[:self.cursor_pos]
        cursor_x = self.font.size(text_before_cursor)[0]

        # Adjust offset to keep cursor visible
        # If cursor is to the right of visible area, scroll right
        if cursor_x - self.text_offset > visible_width:
            self.text_offset = cursor_x - visible_width

        # If cursor is to the left of visible area, scroll left
        if cursor_x < self.text_offset:
            self.text_offset = cursor_x

        # Don't scroll past the beginning
        if self.text_offset < 0:
            self.text_offset = 0

    def _insert_text(self, char: str):
        """Insert a character at the cursor position."""
        self._delete_selection()
        self.text = self.text[:self.cursor_pos] + char + self.text[self.cursor_pos:]
        self.cursor_pos += len(char)
        self.selection_start = None
        self._update_text_offset()

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
        self._update_text_offset()

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
        self._update_text_offset()

    def _move_cursor_home(self, shift_pressed: bool):
        """Move cursor to the start of the text."""
        if shift_pressed and self.selection_start is None:
            self.selection_start = self.cursor_pos
        self.cursor_pos = 0
        if not shift_pressed:
            self.selection_start = None
        self._update_text_offset()

    def _move_cursor_end(self, shift_pressed: bool):
        """Move cursor to the end of the text."""
        if shift_pressed and self.selection_start is None:
            self.selection_start = self.cursor_pos
        self.cursor_pos = len(self.text)
        if not shift_pressed:
            self.selection_start = None
        self._update_text_offset()

    def _move_cursor_word_left(self, shift_pressed: bool):
        """Move cursor to the start of the previous word."""
        if shift_pressed and self.selection_start is None:
            self.selection_start = self.cursor_pos

        self.cursor_pos = self._find_word_start(self.cursor_pos)

        if not shift_pressed:
            self.selection_start = None
        self._update_text_offset()

    def _move_cursor_word_right(self, shift_pressed: bool):
        """Move cursor to the end of the current/next word."""
        if shift_pressed and self.selection_start is None:
            self.selection_start = self.cursor_pos

        self.cursor_pos = self._find_word_end(self.cursor_pos)

        if not shift_pressed:
            self.selection_start = None
        self._update_text_offset()

    def _handle_backspace(self, ctrl_pressed: bool = False):
        """Handle backspace key."""
        if not self._delete_selection():
            if ctrl_pressed:
                # Delete word to the left
                new_pos = self._find_word_start(self.cursor_pos)
                if new_pos < self.cursor_pos:
                    self.text = self.text[:new_pos] + self.text[self.cursor_pos:]
                    self.cursor_pos = new_pos
            elif self.cursor_pos > 0:
                self.text = self.text[:self.cursor_pos - 1] + self.text[self.cursor_pos:]
                self.cursor_pos -= 1
        self._update_text_offset()

    def _handle_delete(self, ctrl_pressed: bool = False):
        """Handle delete key."""
        if not self._delete_selection():
            if ctrl_pressed:
                # Delete word to the right
                new_pos = self._find_word_end(self.cursor_pos)
                if new_pos > self.cursor_pos:
                    self.text = self.text[:self.cursor_pos] + self.text[new_pos:]
            elif self.cursor_pos < len(self.text):
                self.text = self.text[:self.cursor_pos] + self.text[self.cursor_pos + 1:]
        self._update_text_offset()

    def _get_selection_range(self) -> tuple[int, int]:
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
                # Remove newlines and other problematic characters
                clipboard_text = clipboard_text.replace('\n', '').replace('\r', '')
                self._insert_text(clipboard_text)
        except pg.error:
            pass  # Clipboard might not be available

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

        # Draw border (thicker if focused)
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

        # Create a subsurface for clipping
        clip_rect = screen.get_clip()
        screen.set_clip(text_area)

        text_x = text_area.left - self.text_offset
        text_y = self.rect.centery

        # Draw selection highlight if there's a selection
        if self.selection_start is not None and self.is_focused:
            start, end = self._get_selection_range()
            if start != end:
                # Calculate selection rectangle
                text_before_selection = self.text[:start]
                selected_text = self.text[start:end]

                before_width = self.font.size(text_before_selection)[0]
                selection_width = self.font.size(selected_text)[0]

                selection_rect = pg.Rect(
                    text_x + before_width,
                    text_area.top,
                    selection_width,
                    text_area.height
                )
                # Draw selection highlight
                pg.draw.rect(screen, (100, 150, 200), selection_rect)

        # Render text or placeholder
        if self.text:
            text_surface = self.font.render(self.text, True, self.text_color)
            text_rect = text_surface.get_rect(midleft=(text_x, text_y))
            screen.blit(text_surface, text_rect)
        elif not self.is_focused and self.placeholder:
            # Draw placeholder text in a dimmer color
            placeholder_color = (100, 100, 100)
            placeholder_surface = self.font.render(self.placeholder, True, placeholder_color)
            placeholder_rect = placeholder_surface.get_rect(midleft=(text_x, text_y))
            screen.blit(placeholder_surface, placeholder_rect)

        # Draw cursor if focused
        if self.is_focused:
            # Blink cursor (using time-based blinking)
            cursor_visible = (pg.time.get_ticks() // 500) % 2 == 0

            if cursor_visible:
                # Calculate cursor position
                text_before_cursor = self.text[:self.cursor_pos]
                cursor_x = text_x + self.font.size(text_before_cursor)[0]

                cursor_height = text_area.height
                cursor_top = text_area.top

                # Draw cursor line
                pg.draw.line(
                    screen,
                    self.text_color,
                    (cursor_x, cursor_top),
                    (cursor_x, cursor_top + cursor_height),
                    2
                )

        # Restore original clip rect
        screen.set_clip(clip_rect)
