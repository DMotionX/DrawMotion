from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, 
                               QTextEdit, QComboBox, QPushButton, QLabel)
from PySide6.QtCore import Qt

class TextDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Add Text")
        self.setFixedSize(400, 300)
        self.text_content = ""
        self.font_family = "Arial"
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        
        # Font Selection
        font_layout = QHBoxLayout()
        font_layout.addWidget(QLabel("Font:"))
        self.font_combo = QComboBox()
        self.font_combo.addItems(["Arial", "Segoe UI", "Tahoma", "Courier New", "Comic Sans MS"])
        font_layout.addWidget(self.font_combo)
        layout.addLayout(font_layout)
        
        # Text Input
        self.text_input = QTextEdit()
        self.text_input.setPlaceholderText("Enter text here (Supports Arabic & English)...")
        layout.addWidget(self.text_input)
        
        # Buttons
        btn_layout = QHBoxLayout()
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        
        add_btn = QPushButton("Add Text")
        add_btn.setDefault(True)
        add_btn.clicked.connect(self._on_add)
        
        btn_layout.addStretch()
        btn_layout.addWidget(cancel_btn)
        btn_layout.addWidget(add_btn)
        layout.addLayout(btn_layout)

    def _on_add(self):
        self.text_content = self.text_input.toPlainText()
        self.font_family = self.font_combo.currentText()
        if self.text_content.strip():
            self.accept()
        else:
            self.reject()
