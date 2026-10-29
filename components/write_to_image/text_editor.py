import uuid
from PySide6.QtWidgets import QTextEdit
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont, QColor, QTextOption, QTextBlockFormat, QTextCursor
from .models import WriteToImageModel
from .image_renderer import render_text_to_image


class TextEditorWidget(QTextEdit):
    editing_finished = Signal(object)  # Emits the model when done, or None to cancel

    # Default and max constraint size for the paragraph text box
    DEFAULT_WIDTH = 420
    DEFAULT_HEIGHT = 100
    MAX_PARAGRAPH_WIDTH = 680

    def __init__(self, x: float, y: float, existing_model=None, parent=None, center_in_view=False):
        super().__init__(parent)

        # Styling: transparent background with dashed border
        self.setStyleSheet("""
            QTextEdit {
                background: rgba(255, 255, 255, 0.92);
                border: 2px dashed #2E8B57;
                border-radius: 6px;
                color: #1a1a1a;
                padding: 8px;
            }
        """)
        self.setPlaceholderText("Type your paragraph here... (Enter for newline, Ctrl+Enter or click outside to finish)")

        # Load or create model
        self.is_new = not existing_model
        if existing_model:
            self.model = existing_model
            self.setPlainText(self.model.text)
        else:
            self.model = WriteToImageModel(
                id=f"wti_{uuid.uuid4().hex[:8]}",
                name="Text Image",
                pos_x=x,
                pos_y=y
            )

        # Set font
        font = QFont(self.model.font_family, self.model.font_size)
        self.setFont(font)
        self.setTextColor(QColor(self.model.color))

        # Enable proper word wrap
        self.setWordWrapMode(QTextOption.WrapMode.WordWrap)
        
        # Hide scrollbars completely to avoid visual clutter
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        # Re-entrancy guard for direction and layout updates
        self._is_updating_direction = False

        # Detect RTL
        self._update_text_direction()

        # Handle centering or boundary clamping
        if center_in_view and parent:
            view_center = parent.viewport().rect().center()
            x = view_center.x() - self.DEFAULT_WIDTH / 2
            y = view_center.y() - self.DEFAULT_HEIGHT / 2
            
            if not existing_model:
                # Update model's scene pos based on the new centered view pos
                scene_pos = parent.mapToScene(int(x), int(y))
                self.model.pos_x = scene_pos.x()
                self.model.pos_y = scene_pos.y()
        elif parent and hasattr(parent, 'viewport'):
            # Clamp within viewport visible bounds
            vp_rect = parent.viewport().rect()
            max_x = max(10, vp_rect.width() - self.DEFAULT_WIDTH - 20)
            max_y = max(10, vp_rect.height() - self.DEFAULT_HEIGHT - 20)
            x = max(10, min(int(x), max_x))
            y = max(10, min(int(y), max_y))

        # Set geometry: initial comfortable width, auto height
        self.setGeometry(int(x), int(y), self.DEFAULT_WIDTH, self.DEFAULT_HEIGHT)

        # Auto-resize as user types paragraphs
        self.document().contentsChanged.connect(self._adjust_size)
        self._adjust_size()

    def _update_text_direction(self):
        """Detect Arabic text and switch to RTL layout only if Arabic is dominant, or honor explicit model alignment."""
        if getattr(self, '_is_updating_direction', False):
            return
        self._is_updating_direction = True
        try:
            import re
            text = self.toPlainText()
            arabic_chars = len(re.findall(r'[\u0600-\u06FF]', text)) if text else 0
            english_chars = len(re.findall(r'[a-zA-Z]', text)) if text else 0
            is_rtl = arabic_chars > english_chars

            align_pref = getattr(self.model, 'text_align', 'auto')
            if align_pref == 'right':
                target_align = Qt.AlignmentFlag.AlignRight
            elif align_pref == 'center':
                target_align = Qt.AlignmentFlag.AlignHCenter
            elif align_pref == 'left':
                target_align = Qt.AlignmentFlag.AlignLeft
            else:
                target_align = Qt.AlignmentFlag.AlignRight if is_rtl else Qt.AlignmentFlag.AlignLeft

            doc = self.document()
            option = doc.defaultTextOption()
            if is_rtl:
                option.setTextDirection(Qt.LayoutDirection.RightToLeft)
            else:
                option.setTextDirection(Qt.LayoutDirection.LeftToRight)
            option.setAlignment(target_align)
            doc.setDefaultTextOption(option)

            # Block document signals so updating block formats does not recursively trigger contentsChanged
            doc.blockSignals(True)
            try:
                block_fmt = QTextBlockFormat()
                block_fmt.setAlignment(target_align)
                block = doc.firstBlock()
                while block.isValid():
                    if block.blockFormat().alignment() != target_align:
                        cur = QTextCursor(block)
                        cur.mergeBlockFormat(block_fmt)
                    block = block.next()
            finally:
                doc.blockSignals(False)
        finally:
            self._is_updating_direction = False

    def _adjust_size(self):
        """Auto-resize width and height to fit multi-line paragraph content."""
        self._update_text_direction()
        doc = self.document()
        
        ideal_w = int(doc.idealWidth()) + 32
        new_w = min(max(320, ideal_w), self.MAX_PARAGRAPH_WIDTH)
        
        if self.width() != new_w:
            self.resize(new_w, self.height())
            
        doc_height = doc.size().height()
        new_h = int(max(60, doc_height + 24))
        
        self.resize(self.width(), new_h)

    def keyPressEvent(self, event):
        # Ctrl+Enter or Shift+Enter to finish editing; plain Enter = newline for paragraphs
        if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            if event.modifiers() & (Qt.KeyboardModifier.ControlModifier | Qt.KeyboardModifier.ShiftModifier):
                self._finish_editing()
                return
        elif event.key() == Qt.Key.Key_Escape:
            self._finish_editing()
            return
        super().keyPressEvent(event)

    def focusOutEvent(self, event):
        super().focusOutEvent(event)
        self._finish_editing()

    def _finish_editing(self):
        if getattr(self, '_is_finished', False): return
        self._is_finished = True
        
        text = self.toPlainText().strip()
        if not text:
            self.editing_finished.emit(None)
            self.deleteLater()
            return

        # Update model text
        self.model.text = text

        # Render high-res PNG + charmap
        image_path = render_text_to_image(
            text=self.model.text,
            font_family=self.model.font_family,
            font_size=self.model.font_size,
            color=self.model.color,
            id_str=self.model.id,
            text_effect=getattr(self.model, 'text_effect', 'none'),
            text_align=getattr(self.model, 'text_align', 'auto')
        )
        self.model.image_path = image_path

        # Only reset dimensions for brand new items so workspace auto-fit positions it.
        # For existing items being edited, preserve user-customized scale and position!
        if self.is_new:
            self.model.width = 0.0
            self.model.height = 0.0
            self.model.scale_w = 0.0
            self.model.scale_h = 0.0

        # Set default duration only if it hasn't been explicitly configured (e.g. 0.0 or missing)
        char_count = len(self.model.text)
        if getattr(self.model, 'duration', 0.0) <= 0.0:
            calc_dur = max(1.0, char_count * 0.15) # 0.15s per character
            self.model.duration = min(max(calc_dur, 0.5), 8.0)
            print(f"[TextEditor LOG] Text: '{self.model.text[:10]}...', chars: {char_count}, Set Default Duration: {self.model.duration}s")
        else:
            print(f"[TextEditor LOG] Text: '{self.model.text[:10]}...', chars: {char_count}, Kept User Duration: {self.model.duration}s")

        self.editing_finished.emit(self.model)
        self.deleteLater()
