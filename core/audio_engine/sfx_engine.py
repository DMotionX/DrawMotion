from PySide6.QtCore import QObject, Slot, QUrl, Signal, QThread
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput, QMediaDevices
import os

class SFXWorker(QObject):
    def __init__(self):
        super().__init__()
        self.player = QMediaPlayer(self)
        self.audio_output = QAudioOutput(self)
        
        try:
            from core.audio_engine.audio_engine import get_preferred_audio_device
            pref_dev = get_preferred_audio_device()
            if pref_dev and not pref_dev.isNull():
                self.audio_output.setDevice(pref_dev)
        except Exception:
            pass
            
        self.player.setAudioOutput(self.audio_output)
        
        self.base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        self.sfx_dir = os.path.join(self.base_dir, 'assets', 'sfx', 'draw')
        self.motion_sfx_dir = os.path.join(self.base_dir, 'assets', 'sfx', 'motion')
        self.current_sfx_name = None
        self.player.setLoops(QMediaPlayer.Loops.Infinite)
        self.is_drawing = False
        self.current_volume = 100.0
        
        self.audio_output.setVolume(0.0)

        # Dedicated One-Shot Player for Motion Sound FX
        self.motion_player = QMediaPlayer(self)
        self.motion_audio_output = QAudioOutput(self)
        if pref_dev and not pref_dev.isNull():
            self.motion_audio_output.setDevice(pref_dev)
        self.motion_player.setAudioOutput(self.motion_audio_output)
        self.motion_player.setLoops(1)

    @Slot(str)
    def set_output_device_slot(self, device_desc: str):
        devices = QMediaDevices.audioOutputs()
        target = None
        for d in devices:
            if d.description() == device_desc:
                target = d
                break
        if not target:
            target = QMediaDevices.defaultAudioOutput()
        if target and not target.isNull():
            self.audio_output.setDevice(target)
            self.motion_audio_output.setDevice(target)

    @Slot(str, float)
    def on_pen_down_slot(self, sfx_name="None", volume=100.0):
        if sfx_name == "None" or not sfx_name:
            self.on_pen_up_slot()
            return
            
        if self.current_sfx_name != sfx_name:
            sfx_path = os.path.join(self.sfx_dir, sfx_name)
            if os.path.exists(sfx_path):
                self.player.setSource(QUrl.fromLocalFile(sfx_path))
                self.current_sfx_name = sfx_name
                self.player.play()
            else:
                self.current_sfx_name = None
                return
                
        # Centralized Global Drawing Sound Volume from Settings
        from core.settings_manager import SettingsManager
        global_vol = float(SettingsManager().get("sfx_volume", 40))
        # Studio calibrated ceiling (0.40) so marker SFX is clean and never overpowers narration
        calibrated_vol = (global_vol / 100.0) * 0.40
        self.current_volume = calibrated_vol
        
        if not self.is_drawing and self.current_sfx_name:
            self.is_drawing = True
            self.audio_output.setVolume(calibrated_vol)
            if self.player.playbackState() != QMediaPlayer.PlaybackState.PlayingState:
                self.player.play()
        elif self.is_drawing:
            self.audio_output.setVolume(calibrated_vol)

    @Slot()
    def on_pen_up_slot(self):
        if self.is_drawing:
            self.is_drawing = False
            self.audio_output.setVolume(0.0)

    @Slot(str, float)
    def play_motion_sfx_slot(self, sfx_name="none", volume=100.0):
        if not sfx_name or sfx_name.lower() in ("none", "silent"):
            return
            
        fname = sfx_name if "." in sfx_name else f"{sfx_name}.wav"
        sfx_path = os.path.join(self.motion_sfx_dir, fname)
        if not os.path.exists(sfx_path):
            sfx_path = os.path.join(self.sfx_dir, fname if "." in fname else f"{fname}.mp3")
            if not os.path.exists(sfx_path):
                return
                
        from core.settings_manager import SettingsManager
        global_vol = float(SettingsManager().get("sfx_volume", 40))
        calibrated_vol = (global_vol / 100.0) * (volume / 100.0) * 0.50
        self.motion_audio_output.setVolume(calibrated_vol)
        self.motion_player.setSource(QUrl.fromLocalFile(sfx_path))
        self.motion_player.setPosition(0)
        self.motion_player.play()

    @Slot()
    def reset_slot(self):
        self.is_drawing = False
        self.audio_output.setVolume(0.0)
        self.player.stop()
        self.motion_player.stop()
        self.current_sfx_name = None


class SFXSyncEngine(QObject):
    """
    Audio Sync Engine (Phase 5).
    Synchronizes marker/drawing sound effects perfectly with the pen's movement.
    Proxy class that communicates with SFXWorker living in a QThread.
    """
    request_pen_down = Signal(str, float)
    request_pen_up = Signal()
    request_reset = Signal()
    request_set_output_device = Signal(str)
    request_motion_sfx = Signal(str, float)

    def __init__(self, parent=None):
        super().__init__(parent)
        
        self._thread = QThread(self)
        self._thread.setObjectName("SFXSyncEngineThread")
        self._worker = SFXWorker()
        self._worker.moveToThread(self._thread)
        
        self.request_pen_down.connect(self._worker.on_pen_down_slot)
        self.request_pen_up.connect(self._worker.on_pen_up_slot)
        self.request_reset.connect(self._worker.reset_slot)
        self.request_set_output_device.connect(self._worker.set_output_device_slot)
        self.request_motion_sfx.connect(self._worker.play_motion_sfx_slot)
        
        self._thread.start()

    @property
    def sfx_dir(self) -> str:
        """Expose SFX directory path safely from worker."""
        return getattr(self._worker, 'sfx_dir', '')

    @property
    def motion_sfx_dir(self) -> str:
        """Expose motion SFX directory path safely from worker."""
        return getattr(self._worker, 'motion_sfx_dir', '')

    @Slot(str)
    def set_output_device(self, device_desc: str):
        self.request_set_output_device.emit(device_desc)

    @Slot(str, float)
    def on_pen_down(self, sfx_name="None", volume=100.0):
        self.request_pen_down.emit(sfx_name, volume)

    @Slot()
    def on_pen_up(self):
        self.request_pen_up.emit()

    @Slot(str, float)
    def play_motion_sfx(self, sfx_name="none", volume=100.0):
        self.request_motion_sfx.emit(sfx_name, volume)

    @Slot()
    def reset(self):
        self.request_reset.emit()
        
    def shutdown(self):
        """Safely stops the worker thread to prevent QThread destruction errors."""
        try:
            if hasattr(self, '_thread') and self._thread:
                if self._thread.isRunning():
                    self._thread.quit()
                    self._thread.wait(500)
        except Exception:
            pass

    def destroy(self):
        self.shutdown()

    def __del__(self):
        try:
            self.shutdown()
        except Exception:
            pass
