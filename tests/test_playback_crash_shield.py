import sys
import pytest
from unittest.mock import MagicMock, patch
from PySide6.QtWidgets import QApplication
from graphics.hand_item import HandItem
from core.animator_engine import AnimatorEngine
from core.error_handler.tracker import GlobalErrorTracker

@pytest.fixture(scope="session")
def qapp():
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    return app

def test_animator_engine_timer_stops_immediately_on_exception(qapp):
    """
    Verify that if an unhandled exception occurs inside _step_internal:
    1. engine.timer is stopped immediately.
    2. engine.stop() is executed to cleanly hide hands and reset state.
    3. playback_error signal is emitted.
    4. No infinite loop or unhandled re-entrancy occurs.
    """
    hand_item = HandItem()
    writing_hand_item = HandItem()
    engine = AnimatorEngine(hand_item, writing_hand_item=writing_hand_item)
    
    # Start timer simulating active playback
    engine.timer.start(16)
    assert engine.timer.isActive()
    
    # Track error signal emission
    emitted_errors = []
    engine.playback_error.connect(lambda msg: emitted_errors.append(msg))
    
    # Inject deliberate exception into _step_internal
    def failing_step(dt):
        raise ValueError("Simulated unexpected playback calculation error")
        
    engine._step_internal = failing_step
    
    # Execute update loop (which would be called by timer timeout)
    engine._update_loop()
    
    # Assertions
    assert not engine.timer.isActive(), "Timer MUST be stopped immediately on exception!"
    assert not engine.hand_item.isVisible(), "Hand item MUST be hidden on error stop!"
    assert not engine.writing_hand_item.isVisible(), "Writing hand item MUST be hidden on error stop!"
    assert len(emitted_errors) == 1
    assert "Simulated unexpected playback calculation error" in emitted_errors[0]
    
    # Ensure calling _update_loop again does not loop or raise
    engine._update_loop()
    assert not engine.timer.isActive()

def test_global_error_tracker_bypasses_keyboard_interrupt():
    """
    Verify that KeyboardInterrupt and SystemExit bypass QMessageBox completely
    and delegate directly to sys.__excepthook__ so the app can be terminated cleanly.
    """
    with patch.object(sys, '__excepthook__') as mock_sys_hook, \
         patch('PySide6.QtWidgets.QMessageBox.exec') as mock_exec:
        
        # Simulate Ctrl+C (KeyboardInterrupt)
        try:
            raise KeyboardInterrupt()
        except KeyboardInterrupt:
            exc_type, exc_val, exc_tb = sys.exc_info()
            GlobalErrorTracker._exception_hook(exc_type, exc_val, exc_tb)
            
        mock_sys_hook.assert_called_once_with(exc_type, exc_val, exc_tb)
        mock_exec.assert_not_called()

def test_global_error_tracker_reentrancy_guard(qapp):
    """
    Verify that if an error dialog is already open (_is_displaying_error = True),
    subsequent exceptions do NOT create or show stacked modal QMessageBox dialogs.
    """
    GlobalErrorTracker._is_displaying_error = True
    
    with patch('PySide6.QtWidgets.QMessageBox.exec') as mock_exec, \
         patch.object(sys, '__excepthook__') as mock_sys_hook:
        
        try:
            raise RuntimeError("Secondary cascading error during open dialog")
        except RuntimeError:
            exc_type, exc_val, exc_tb = sys.exc_info()
            GlobalErrorTracker._exception_hook(exc_type, exc_val, exc_tb)
            
        # Logged to sys.__excepthook__, but QMessageBox.exec MUST NOT be called!
        mock_sys_hook.assert_called_once()
        mock_exec.assert_not_called()
        
    # Reset flag
    GlobalErrorTracker._is_displaying_error = False

def test_global_error_tracker_resets_flag_after_dialog(qapp):
    """
    Verify that _is_displaying_error flag is safely reset to False after dialog closes.
    """
    GlobalErrorTracker._is_displaying_error = False
    
    with patch('PySide6.QtWidgets.QMessageBox.exec') as mock_exec, \
         patch.object(sys, '__excepthook__'):
        
        try:
            raise RuntimeError("Single unexpected error")
        except RuntimeError:
            exc_type, exc_val, exc_tb = sys.exc_info()
            GlobalErrorTracker._exception_hook(exc_type, exc_val, exc_tb)
            
        mock_exec.assert_called_once()
        assert GlobalErrorTracker._is_displaying_error is False
