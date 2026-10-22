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

def test_timeline_resize_handle(qtbot):
    """Test that timeline resize handle exists, clamps height safely, and resets on double click."""
    window = WhiteInkMainWindow()
    qtbot.addWidget(window)
    
    timeline = window.bottom_panel
    assert hasattr(timeline, 'resize_handle')
    handle = timeline.resize_handle
    assert handle is not None
    assert handle.cursor().shape() == Qt.CursorShape.SplitVCursor
    
    # Test setting height within and outside boundaries
    timeline.set_timeline_height(100)
    assert timeline.height() == 100
    
    # Minimum clamp boundary (76px)
    timeline.set_timeline_height(30)
    assert timeline.height() == 76
    
    # Maximum clamp boundary (capped at 450 max)
    timeline.set_timeline_height(800)
    assert timeline.height() <= 450
    
    # Double click reset to default height (180px)
    timeline.set_timeline_height(120)
    assert timeline.height() == 120
    qtbot.mouseDClick(handle, Qt.MouseButton.LeftButton)
    assert timeline.height() == 180

def test_settings_page_save_and_scroll_reset(qtbot):
    """Test that settings page does NOT exit on save and resets scrollbar on section switch."""
    from components.settings.settings_page import SettingsPage
    page = SettingsPage()
    qtbot.addWidget(page)
    page.show()
    
    # 1. Test Save does NOT emit back_requested
    back_signal_fired = False
    def on_back():
        nonlocal back_signal_fired
        back_signal_fired = True
    page.back_requested.connect(on_back)
    
    qtbot.mouseClick(page.save_btn, Qt.MouseButton.LeftButton)
    assert back_signal_fired is False
    assert "Saved" in page.save_btn.text()
    
    # 2. Test Section Switch resets scroll position to 0
    page.content_scroll.verticalScrollBar().setValue(150)
    assert page.content_scroll.verticalScrollBar().value() == 150
    page._on_section_selected(1)
    assert page.content_scroll.verticalScrollBar().value() == 0

def test_inspector_scroll_reset_and_tab_retention(qtbot):
    """Test that inspector panel stores persistent scroll areas and resets scroll on tab change."""
    from components.inspector import InspectorPanel
    panel = InspectorPanel()
    qtbot.addWidget(panel)
    panel.show()
    
    assert hasattr(panel, 'object_scroll_area')
    assert hasattr(panel, 'style_scroll_area')
    assert hasattr(panel, 'audio_scroll_area')
    
    # Switch stack to properties page and set range to test scroll reset
    panel.stack.setCurrentWidget(panel.properties_page)
    panel.object_scroll_area.verticalScrollBar().setRange(0, 500)
    panel.object_scroll_area.verticalScrollBar().setValue(80)
    assert panel.object_scroll_area.verticalScrollBar().value() == 80
    panel._on_tab_changed(1)
    assert panel.object_scroll_area.verticalScrollBar().value() == 0


