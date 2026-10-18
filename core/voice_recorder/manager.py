"""
Voice Recorder Manager: Handles the actual QtMultimedia recording logic.
Provides signals to integrate cleanly with the timeline.
"""
from PySide6.QtMultimedia import QMediaCaptureSession, QAudioInput, QMediaRecorder, QMediaFormat
from PySide6.QtCore import QObject, Signal, QUrl
import os
import time
from utils.paths import get_app_data_dir

class VoiceRecorderManager(QObject):
    recording_finished = Signal(str)
    recording_error = Signal(str)

    def __init__(self):
        super().__init__()
        
        # Temp dir for voice records
        self.output_dir = os.path.join(get_app_data_dir(), "temp_records")
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)

        # Setup PySide6 Audio Engine
        self.session = QMediaCaptureSession()
        self.audio_input = QAudioInput()
        
        # Set a safe volume to prevent clipping/distortion
        self.audio_input.setVolume(0.8)
        self.session.setAudioInput(self.audio_input)

        self.recorder = QMediaRecorder()
        self.recorder.recorderStateChanged.connect(self._on_state_changed)
        
        # Configure format (WAV)
        format = QMediaFormat()
        format.setFileFormat(QMediaFormat.FileFormat.Wave)
        format.setAudioCodec(QMediaFormat.AudioCodec.Wave)
        self.recorder.setMediaFormat(format)
        
        # Strict Audio Specifications for clear voice
        self.recorder.setAudioSampleRate(44100)
        self.recorder.setAudioChannelCount(1)
        self.recorder.setQuality(QMediaRecorder.Quality.HighQuality)
        
        self.session.setRecorder(self.recorder)
        self.current_file = ""
        self._is_stopping = False

    def start_recording(self):
        self._is_stopping = False
        filename = f"voice_record_{int(time.time())}.wav"
        self.current_file = os.path.join(self.output_dir, filename)
        
        self.recorder.setOutputLocation(QUrl.fromLocalFile(self.current_file))
        self.recorder.record()

    def stop_recording(self):
        self._is_stopping = True
        self.recorder.stop()
        # The actual save happens instantly when recorderStateChanged fires StoppedState
        
    def _on_state_changed(self, state):
        if state == QMediaRecorder.RecorderState.StoppedState and getattr(self, '_is_stopping', False):
            self._is_stopping = False
            self._check_file_saved()

    def _check_file_saved(self):
        if os.path.exists(self.current_file):
            # Check if file has data (not 0 bytes)
            if os.path.getsize(self.current_file) > 0:
                # Apply Zero-Risk purification (Post-Processing)
                try:
                    from core.voice_recorder.audio_purifier import AudioPurifier
                    purified_file = AudioPurifier.purify(self.current_file)
                except Exception:
                    purified_file = self.current_file # Fallback
                
                self.recording_finished.emit(purified_file)
            else:
                self.recording_error.emit("Audio file is empty. Check microphone settings.")
                os.remove(self.current_file)
        else:
            self.recording_error.emit("Failed to save audio file. Check permissions.")
