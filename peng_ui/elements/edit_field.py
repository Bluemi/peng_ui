from typing import Optional

import pygame as pg

from peng_ui.elements.base_element import BaseElement
from peng_ui.utils import RenderContext, ColorType


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
                # Handle text input
                if event.key == pg.K_BACKSPACE:
                    self._handle_backspace()
                elif event.key == pg.K_DELETE:
                    self._handle_delete()
                elif event.key == pg.K_LEFT:
                    self._move_cursor_left(event.mod & pg.KMOD_SHIFT)
                elif event.key == pg.K_RIGHT:
                    self._move_cursor_right(event.mod & pg.KMOD_SHIFT)
                elif event.key == pg.K_HOME:
                    self._move_cursor_home(event.mod & pg.KMOD_SHIFT)
                elif event.key == pg.K_END:
                    self._move_cursor_end(event.mod & pg.KMOD_SHIFT)
                elif event.key == pg.K_a and (event.mod & pg.KMOD_CTRL):
                    self._select_all()
                elif event.key == pg.K_c and (event.mod & pg.KMOD_CTRL):
                    self._copy_to_clipboard()
                elif event.key == pg.K_v and (event.mod & pg.KMOD_CTRL):
                    self._paste_from_clipboard()
                elif event.key == pg.K_x and (event.mod & pg.KMOD_CTRL):
                    self._cut_to_clipboard()
                elif event.unicode and event.unicode.isprintable():
                    self._insert_text(event.unicode)

    def _get_char_index_at_pos(self, mouse_pos) -> int:
        """Get the character index at the mouse position."""
        if not self.text:
            return 0
        
        # Get the relative x position within the edit field
        rel_x = mouse_pos[0] - self.rect.left - 5  # 5px padding
        
        # Use a default font if render_context is not available yet
        font = pg.font.Font(None, 24)
        
        # Find the closest character position
        for i in range(len(self.text) + 1):
            text_width = font.size(self.text[:i])[0]
            if rel_x <= text_width:
                # Check if we're closer to previous or current position
                if i > 0:
                    prev_width = font.size(self.text[:i-1])[0]
                    if rel_x - prev_width < text_width - rel_x:
                        return i - 1
                return i
        
        return len(self.text)

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

    def _insert_text(self, char: str):
        """Insert a character at the cursor position."""
        self._delete_selection()
        self.text = self.text[:self.cursor_pos] + char + self.text[self.cursor_pos:]
        self.cursor_pos += len(char)
        self.selection_start = None

    def _handle_backspace(self):
        """Handle backspace key."""
        if not self._delete_selection():
            if self.cursor_pos > 0:
                self.text = self.text[:self.cursor_pos - 1] + self.text[self.cursor_pos:]
                self.cursor_pos -= 1

    def _handle_delete(self):
        """Handle delete key."""
        if not self._delete_selection():
            if self.cursor_pos < len(self.text):
                self.text = self.text[:self.cursor_pos] + self.text[self.cursor_pos + 1:]

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

    def _move_cursor_home(self, shift_pressed: bool):
        """Move cursor to the start of the text."""
        if shift_pressed and self.selection_start is None:
            self.selection_start = self.cursor_pos
        self.cursor_pos = 0
        if not shift_pressed:
            self.selection_start = None

    def _move_cursor_end(self, shift_pressed: bool):
        """Move cursor to the end of the text."""
        if shift_pressed and self.selection_start is None:
            self.selection_start = self.cursor_pos
        self.cursor_pos = len(self.text)
        if not shift_pressed:
            self.selection_start = None

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
        except:
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
        text_x = self.rect.left + padding
        text_y = self.rect.centery

        # Draw selection highlight if there's a selection
        if self.selection_start is not None and self.is_focused:
            start, end = self._get_selection_range()
            if start != end:
                # Calculate selection rectangle
                text_before_selection = self.text[:start]
                selected_text = self.text[start:end]
                
                before_width = render_context.font.size(text_before_selection)[0]
                selection_width = render_context.font.size(selected_text)[0]
                
                selection_rect = pg.Rect(
                    text_x + before_width,
                    self.rect.top + padding,
                    selection_width,
                    self.rect.height - 2 * padding
                )
                # Draw selection highlight
                pg.draw.rect(screen, (100, 150, 200), selection_rect)

        # Render text or placeholder
        if self.text:
            text_surface = render_context.font.render(self.text, True, self.text_color)
            text_rect = text_surface.get_rect(midleft=(text_x, text_y))
            screen.blit(text_surface, text_rect)
        elif not self.is_focused and self.placeholder:
            # Draw placeholder text in a dimmer color
            placeholder_color = (100, 100, 100)
            placeholder_surface = render_context.font.render(self.placeholder, True, placeholder_color)
            placeholder_rect = placeholder_surface.get_rect(midleft=(text_x, text_y))
            screen.blit(placeholder_surface, placeholder_rect)

        # Draw cursor if focused
        if self.is_focused:
            # Blink cursor (using time-based blinking)
            cursor_visible = (pg.time.get_ticks() // 500) % 2 == 0
            
            if cursor_visible:
                # Calculate cursor position
                text_before_cursor = self.text[:self.cursor_pos]
                cursor_x = text_x + render_context.font.size(text_before_cursor)[0]
                
                cursor_height = self.rect.height - 2 * padding
                cursor_top = self.rect.top + padding
                
                # Draw cursor line
                pg.draw.line(
                    screen,
                    self.text_color,
                    (cursor_x, cursor_top),
                    (cursor_x, cursor_top + cursor_height),
                    2
                )
