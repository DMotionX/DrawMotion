import os
import logging
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput, QMediaDevices, QAudioDevice
from PySide6.QtCore import QObject, QUrl, Slot, Signal, QThread

def get_preferred_audio_device() -> QAudioDevice:
    """
    Returns the preferred audio output device.
    Prioritizes user setting from SettingsManager, then headphones/earphones,
    and falls back to system default.
    """
    try:
        from core.settings_manager import SettingsManager
        saved_desc = SettingsManager().get("audio_output_device", "")
        devices = QMediaDevices.audioOutputs()
        if not devices:
            return QMediaDevices.defaultAudioOutput()
            
        if saved_desc:
            for d in devices:
                if d.description() == saved_desc:
                    return d
                    
        # Prefer headphones/headset if detected
        for d in devices:
            desc_lower = d.description().lower()
            if any(k in desc_lower for k in ["headphone", "earphone", "headset"]):
                return d
                
        return QMediaDevices.defaultAudioOutput()
    except Exception as e:
        logging.warning(f"Failed to get preferred audio device: {e}")
        return QMediaDevices.defaultAudioOutput()

class TrackPlayer(QObject):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.player = QMediaPlayer(self)
        self.audio_output = QAudioOutput(self)
        
        pref_dev = get_preferred_audio_device()
        if pref_dev and not pref_dev.isNull():
            self.audio_output.setDevice(pref_dev)
            
        self.player.setAudioOutput(self.audio_output)
        
        self.is_loaded = False
        self.original_file = ""
        self.current_file = ""
        self.start_delay = 0.0 # Time in seconds when this track should start
        self.base_volume = 1.0
        self.volume_percent = 100
        self.playback_speed = 1.0
        self.fade_in_sec = 0.0
        self.fade_out_sec = 0.0
        self.track_duration_sec = 0.0
        
        self.player.durationChanged.connect(self._on_duration_changed)
        
    def _on_duration_changed(self, dur_ms: int):
        if dur_ms > 0:
            self.track_duration_sec = dur_ms / 1000.0

    def set_audio_device(self, device: QAudioDevice):
        if device and not device.isNull():
            self.audio_output.setDevice(device)
        
    def load(self, file_path: str, start_delay: float = 0.0):
        if not os.path.exists(file_path):
            return False
            
        self.original_file = file_path
        self.current_file = file_path
        self.start_delay = start_delay
        self.player.setSource(QUrl.fromLocalFile(file_path))
        self.is_loaded = True
        return True
        
    def set_volume(self, volume: float):
        self.base_volume = max(0.0, min(1.0, volume))
        self.audio_output.setVolume(self.base_volume)

    def apply_fx_settings(self, settings: dict):
        """
        Dynamically applies audio plugin properties without restarting the track or freezing:
        - volume: percentage (0 - 300) or float
        - speed: multiplier (0.25 - 3.0)
        - fade_in: seconds (float)
        - fade_out: seconds (float)
        """
        if not settings:
            return
            
        if "volume" in settings:
            raw_vol = float(settings["volume"])
            self.volume_percent = int(raw_vol)
            # 0% to 100% adjusts hardware output smoothly; >100% clamps to maximum listening level (1.0)
            self.base_volume = max(0.0, min(1.0, raw_vol / 100.0))
            self.audio_output.setVolume(self.base_volume)
            
        if "speed" in settings:
            speed = max(0.25, min(3.0, float(settings["speed"])))
            self.playback_speed = speed
            self.player.setPlaybackRate(speed)
            
        if "fade_in" in settings:
            self.fade_in_sec = max(0.0, float(settings["fade_in"]))
            
        if "fade_out" in settings:
            self.fade_out_sec = max(0.0, float(settings["fade_out"]))

        if "start_delay" in settings:
            self.start_delay = max(0.0, float(settings["start_delay"]))
        elif "delay" in settings:
            self.start_delay = max(0.0, float(settings["delay"]))
        
    def seek_and_sync(self, global_time_sec: float, is_playing: bool):
        if not self.is_loaded:
            return
            
        # Calculate local time for this track
        local_time_sec = global_time_sec - self.start_delay
        
        if local_time_sec < 0:
            # Not started yet
            if not is_playing:
                self.player.setPosition(0)
            if self.player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
                self.player.pause()
        else:
            # Apply dynamic fade envelope calculation
            effective_vol = self.base_volume
            dur = self.track_duration_sec if self.track_duration_sec > 0 else (self.player.duration() / 1000.0 if self.player.duration() > 0 else 0.0)
            effective_track_dur = (dur / self.playback_speed) if (self.playback_speed > 0 and dur > 0) else dur
            
            if self.fade_in_sec > 0 and local_time_sec < self.fade_in_sec:
                effective_vol = self.base_volume * (local_time_sec / self.fade_in_sec)
            elif self.fade_out_sec > 0 and effective_track_dur > 0 and (effective_track_dur - local_time_sec) < self.fade_out_sec:
                remaining = max(0.0, effective_track_dur - local_time_sec)
                effective_vol = self.base_volume * (remaining / self.fade_out_sec)
                
            self.audio_output.setVolume(max(0.0, min(1.0, effective_vol)))

            expected_ms = int(local_time_sec * self.playback_speed * 1000)
            total_dur_ms = self.player.duration()
            
            if not is_playing:
                # Manual scrubbing: seek to exact position immediately
                target_pos = min(expected_ms, total_dur_ms) if total_dur_ms > 0 else expected_ms
                self.player.setPosition(target_pos)
                if self.player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
                    self.player.pause()
            else:
                # Active playing: check if track reached end
                if total_dur_ms > 0 and expected_ms >= total_dur_ms:
                    if self.player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
                        self.player.pause()
                    return

                # Active playing: start playback immediately if stopped or paused
                if self.player.playbackState() != QMediaPlayer.PlaybackState.PlayingState:
                    if total_dur_ms == 0 or expected_ms < total_dur_ms:
                        self.player.setPosition(expected_ms)
                        self.player.play()
                else:
                    # While already playing, do NOT thrash setPosition every frame!
                    # Only correct if extreme drift (> 1200ms) occurs
                    current_ms = self.player.position()
                    if abs(current_ms - expected_ms) > 1200:
                        self.player.setPosition(expected_ms)

    def pause(self):
        if self.is_loaded:
            self.player.pause()
            
    def stop(self):
        if self.is_loaded:
            self.player.stop()

class AudioWorker(QObject):
    """
    Runs completely in a background thread to process audio
    so the UI does not block it during transitions.
    """
    def __init__(self):
        super().__init__()
        self.tracks = []
        
    @Slot(str, float, float)
    def add_track_slot(self, file_path: str, start_time: float, volume: float):
        track = TrackPlayer(self)
        if track.load(file_path, start_time):
            track.set_volume(volume)
            self.tracks.append(track)

    @Slot(str, dict)
    def update_track_fx_slot(self, file_path: str, settings: dict):
        norm_target = os.path.normpath(os.path.abspath(file_path)) if file_path else ""
        for track in self.tracks:
            norm_orig = os.path.normpath(os.path.abspath(track.original_file)) if getattr(track, 'original_file', None) else ""
            norm_curr = os.path.normpath(os.path.abspath(track.current_file)) if track.current_file else ""
            if norm_orig == norm_target or norm_curr == norm_target or track.original_file == file_path or track.current_file == file_path:
                track.apply_fx_settings(settings)
            
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
        for track in self.tracks:
            track.set_audio_device(target)

    @Slot(str)
    def remove_track_slot(self, file_path: str):
        norm_target = os.path.normpath(os.path.abspath(file_path)) if file_path else ""
        for track in list(self.tracks):
            norm_orig = os.path.normpath(os.path.abspath(track.original_file)) if getattr(track, 'original_file', None) else ""
            norm_curr = os.path.normpath(os.path.abspath(track.current_file)) if track.current_file else ""
            if norm_orig == norm_target or norm_curr == norm_target or track.original_file == file_path or track.current_file == file_path:
                track.stop()
                self.tracks.remove(track)
                track.deleteLater()
                break
                
    @Slot()
    def clear_tracks_slot(self):
        for track in self.tracks:
            track.stop()
            track.deleteLater()
        self.tracks.clear()
        
    @Slot(float, bool)
    def on_progress_updated_slot(self, time_sec: float, is_playing: bool):
        for track in self.tracks:
            track.seek_and_sync(time_sec, is_playing)
            
    @Slot()
    def pause_all_slot(self):
        for track in self.tracks:
            track.pause()
            
    @Slot()
    def stop_all_slot(self):
        for track in self.tracks:
            track.stop()

class AudioEngine(QObject):
    """
    Central manager for Voice and SFX playback during real-time preview.
    Proxy class that communicates with AudioWorker living in a QThread.
    """
    request_add_track = Signal(str, float, float)
    request_update_track_fx = Signal(str, dict)
    request_set_output_device = Signal(str)
    request_remove_track = Signal(str)
    request_clear_tracks = Signal()
    request_progress_update = Signal(float, bool)
    request_pause_all = Signal()
    request_stop_all = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.parent_ws = parent
        
        # Setup the background thread
        self._thread = QThread(self)
        self._thread.setObjectName("AudioProxyThread")
        self._worker = AudioWorker()
        self._worker.moveToThread(self._thread)
        
        # Connect signals
        self.request_add_track.connect(self._worker.add_track_slot)
        self.request_update_track_fx.connect(self._worker.update_track_fx_slot)
        self.request_set_output_device.connect(self._worker.set_output_device_slot)
        self.request_remove_track.connect(self._worker.remove_track_slot)
        self.request_clear_tracks.connect(self._worker.clear_tracks_slot)
        self.request_progress_update.connect(self._worker.on_progress_updated_slot)
        self.request_pause_all.connect(self._worker.pause_all_slot)
        self.request_stop_all.connect(self._worker.stop_all_slot)
        
        self._thread.start()
        
    def shutdown(self):
        """Safely stops the worker thread to prevent crashes."""
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
            
    def add_track(self, file_path: str, start_time: float = 0.0, volume: float = 1.0):
        self.request_add_track.emit(file_path, start_time, volume)
        return True

    def update_track_fx(self, file_path: str, settings: dict):
        self.request_update_track_fx.emit(file_path, settings)
        return True

    def set_output_device(self, device_desc: str):
        self.request_set_output_device.emit(device_desc)
        return True
        
    def remove_track(self, file_path: str):
        self.request_remove_track.emit(file_path)
        return True
        
    def clear_tracks(self):
        self.request_clear_tracks.emit()
        
    @Slot(float)
    def on_progress_updated(self, time_sec: float):
        is_playing = False
        if self.parent_ws and hasattr(self.parent_ws, 'animator_engine'):
            is_playing = self.parent_ws.animator_engine.timer.isActive()
                
        self.request_progress_update.emit(time_sec, is_playing)
            
    def pause_all(self):
        self.request_pause_all.emit()
            
    def stop_all(self):
        self.request_stop_all.emit()
        
    def destroy(self):
        self._thread.quit()
        self._thread.wait()
