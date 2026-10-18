import uuid
from PySide6.QtWidgets import QTextEdit
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont, QColor, QTextOption
from .models import WriteToImageModel
from .image_renderer import render_text_to_image


class TextEditorWidget(QTextEdit):
    editing_finished = Signal(object)  # Emits the model when done, or None to cancel

    # Default size for the text box
    DEFAULT_WIDTH = 400
    DEFAULT_HEIGHT = 100

    def __init__(self, x: float, y: float, existing_model=None, parent=None, center_in_view=False):
        super().__init__(parent)

        # Styling: transparent background with dashed border
        self.setStyleSheet("""
            QTextEdit {
                background: rgba(255, 255, 255, 0.85);
                border: 2px dashed #2E8B57;
                border-radius: 4px;
                color: #1a1a1a;
                padding: 6px;
            }
        """)
        self.setPlaceholderText("Type here...")

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
        
        # Hide scrollbars completely to avoid the "black halo" visual bug
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        # Detect RTL
        self._update_text_direction()

        # Handle centering
        if center_in_view and parent:
            view_center = parent.viewport().rect().center()
            x = view_center.x() - self.DEFAULT_WIDTH / 2
            y = view_center.y() - self.DEFAULT_HEIGHT / 2
            
            if not existing_model:
                # Update model's scene pos based on the new centered view pos
                scene_pos = parent.mapToScene(int(x), int(y))
                self.model.pos_x = scene_pos.x()
                self.model.pos_y = scene_pos.y()

        # Set geometry: fixed width, auto height
        self.setGeometry(int(x), int(y), self.DEFAULT_WIDTH, self.DEFAULT_HEIGHT)

        # Auto-resize as user types
        self.document().contentsChanged.connect(self._adjust_size)
        self._adjust_size()

    def _update_text_direction(self):
        """Detect Arabic text and switch to RTL layout automatically."""
        import re
        text = self.toPlainText()
        is_rtl = bool(re.search(r'[\u0600-\u06FF]', text)) if text else False

        option = self.document().defaultTextOption()
        if is_rtl:
            option.setTextDirection(Qt.LayoutDirection.RightToLeft)
            option.setAlignment(Qt.AlignmentFlag.AlignRight)
        else:
            option.setTextDirection(Qt.LayoutDirection.LeftToRight)
            option.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.document().setDefaultTextOption(option)

    def _adjust_size(self):
        """Auto-resize width and height to fit content."""
        self._update_text_direction()
        doc = self.document()
        
        ideal_w = int(doc.idealWidth()) + 30 
        new_w = min(max(250, ideal_w), 1600)
        
        if self.width() != new_w:
            self.resize(new_w, self.height())
            
        doc_height = doc.size().height()
        new_h = int(max(50, doc_height + 20))
        
        self.resize(self.width(), new_h)

    def keyPressEvent(self, event):
        # Ctrl+Enter or Shift+Enter to finish editing; plain Enter = newline for paragraphs
        if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            if event.modifiers() & (Qt.KeyboardModifier.ControlModifier | Qt.KeyboardModifier.ShiftModifier):
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
            text_effect=getattr(self.model, 'text_effect', 'none')
        )
        self.model.image_path = image_path

        # Reset dimensions so graphics_item resets scale on next load
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
