from PySide6.QtWidgets import QListWidgetItem, QLabel
from PySide6.QtCore import Qt
from utils.theme import THEME_COLORS
from advanced_features.components.audio_tracks import AudioTrackComponent, SoundEffectTrackComponent

class TimelineAssembly:
    """
    Handles the integration of advanced features (like Audio and Sound Effect tracks)
    into the existing timeline safely without breaking the current UI.
    """
    @staticmethod
    def integrate_audio_layers(layers_list, tracks_layout):
        """
        Injects the fixed Audio and Sound Effect tracks at the bottom of the timeline layers.
        Should be called after the main timeline updates its visual items.
        """
        # 1. Add to the left panel (Layers list)
        audio_item = QListWidgetItem()
        audio_item.setFlags(audio_item.flags() & ~Qt.ItemIsSelectable) # Fixed layer
        
        sfx_item = QListWidgetItem()
        sfx_item.setFlags(sfx_item.flags() & ~Qt.ItemIsSelectable) # Fixed layer
        
        # We don't need text, we will set custom widgets
        layers_list.addItem(audio_item)
        layers_list.addItem(sfx_item)
        
        
        lbl_audio = QLabel("Audio")
        lbl_audio.setStyleSheet(f"color: {THEME_COLORS['primary_green']}; font-weight: bold; padding: 5px;")
        
        lbl_sfx = QLabel("Sound Effect")
        lbl_sfx.setStyleSheet(f"color: {THEME_COLORS['primary_green']}; font-weight: bold; padding: 5px;")
        
        audio_item.setSizeHint(lbl_audio.sizeHint())
        sfx_item.setSizeHint(lbl_sfx.sizeHint())
        
        layers_list.setItemWidget(audio_item, lbl_audio)
        layers_list.setItemWidget(sfx_item, lbl_sfx)
        
        # 2. Add to the right panel (Tracks layout)
        audio_track = AudioTrackComponent()
        sfx_track = SoundEffectTrackComponent()
        
        # Insert before the stretch at the bottom
        count = tracks_layout.count()
        if count > 0:
            tracks_layout.insertWidget(count - 1, audio_track)
            tracks_layout.insertWidget(count - 1, sfx_track)
        else:
            tracks_layout.addWidget(audio_track)
            tracks_layout.addWidget(sfx_track)
