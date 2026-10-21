import pytest
from PySide6.QtCore import Qt
from main import WhiteInkMainWindow

def test_main_window_loads(qtbot):
    """Test that the main window initializes without crashing."""
    window = WhiteInkMainWindow()
    qtbot.addWidget(window)
    
    # Assert that components are created
    assert window.top_bar is not None
    assert window.left_panel is not None
    assert window.center_workspace is not None
    
def test_export_button_triggers_dialog(qtbot, monkeypatch):
    """Test that clicking the export button triggers the export dialog without blocking."""
    window = WhiteInkMainWindow()
    qtbot.addWidget(window)
    
    # Mock ExportDialog.exec so the test does not block waiting for user modal interaction
    dialog_opened = []
    
    import main
    original_export_dialog = main.ExportDialog
    
    class MockExportDialog(original_export_dialog):
        def exec(self):
            dialog_opened.append(True)
            return 1
            
    monkeypatch.setattr(main, 'ExportDialog', MockExportDialog)
    
    # Simulate user clicking the Export button
    qtbot.mouseClick(window.top_bar.export_btn, Qt.MouseButton.LeftButton)
    
    # Verify the dialog was created and executed
    assert len(dialog_opened) == 1

def test_assets_grid_left_alignment(qtbot):
    """Test that assets grid starts strictly from the left and aligns to the top-left corner."""
    window = WhiteInkMainWindow()
    qtbot.addWidget(window)
    
    panel = window.left_panel
    layout = panel.assets_grid_layout
    
    assert bool(layout.alignment() & Qt.AlignmentFlag.AlignLeft)
    assert bool(layout.alignment() & Qt.AlignmentFlag.AlignTop)
    assert layout.columnMinimumWidth(0) == 102
    assert layout.columnMinimumWidth(1) == 102
    assert layout.columnStretch(2) == 1

