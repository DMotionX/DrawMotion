import os
import sys
import unittest

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt, QEvent
from PySide6.QtGui import QKeyEvent

# Ensure offscreen Qt platform for testing on headless Linux
if sys.platform != "win32":
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

app = QApplication.instance() or QApplication(sys.argv)

from components.write_to_image.text_editor import TextEditorWidget
from components.write_to_image.models import WriteToImageModel


class TestTextEditorRecursionFix(unittest.TestCase):
    def setUp(self):
        self.model = WriteToImageModel(
            id="test_editor_id",
            name="Test Text",
            text="Initial line",
            font_family="Arial",
            font_size=24,
            color="#000000"
        )
        self.editor = TextEditorWidget(x=100, y=100, existing_model=self.model)

    def tearDown(self):
        self.editor.deleteLater()

    def test_enter_key_does_not_cause_recursion(self):
        """Simulate pressing Enter 10 times to verify no recursion error occurs."""
        for _ in range(10):
            event = QKeyEvent(QEvent.Type.KeyPress, Qt.Key.Key_Return, Qt.KeyboardModifier.NoModifier, "\n")
            self.editor.keyPressEvent(event)

        text = self.editor.toPlainText()
        self.assertIn("\n", text)
        self.assertFalse(self.editor._is_updating_direction)

    def test_arabic_multiline_enter_and_alignment(self):
        """Test Arabic text with newlines and verify RTL direction is correctly set without recursion."""
        self.editor.setPlainText("السطر الأول")
        event = QKeyEvent(QEvent.Type.KeyPress, Qt.Key.Key_Return, Qt.KeyboardModifier.NoModifier, "\n")
        self.editor.keyPressEvent(event)
        
        # Append second line
        cursor = self.editor.textCursor()
        cursor.insertText("السطر الثاني")
        
        # Fire contentsChanged explicitly via adjust_size
        self.editor._adjust_size()
        
        # Document option should be RTL
        self.assertEqual(
            self.editor.document().defaultTextOption().textDirection(),
            Qt.LayoutDirection.RightToLeft
        )
        self.assertFalse(self.editor._is_updating_direction)

    def test_english_multiline_enter_and_alignment(self):
        """Test English text with newlines and verify LTR direction is maintained without recursion."""
        self.editor.setPlainText("First line of paragraph")
        event = QKeyEvent(QEvent.Type.KeyPress, Qt.Key.Key_Return, Qt.KeyboardModifier.NoModifier, "\n")
        self.editor.keyPressEvent(event)
        
        cursor = self.editor.textCursor()
        cursor.insertText("Second line of paragraph")
        
        self.editor._adjust_size()
        self.assertEqual(
            self.editor.document().defaultTextOption().textDirection(),
            Qt.LayoutDirection.LeftToRight
        )
        self.assertFalse(self.editor._is_updating_direction)


if __name__ == '__main__':
    unittest.main()
