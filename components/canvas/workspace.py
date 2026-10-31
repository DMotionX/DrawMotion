"""
Purpose: Main drawing area where animation is previewed.
Features: Uses QGraphicsView/QGraphicsScene to render paths and items. Includes a resizable Artboard/Scene frame.
"""
from PySide6.QtWidgets import QGraphicsView, QGraphicsScene, QFrame, QVBoxLayout, QGraphicsRectItem, QGraphicsItem
from PySide6.QtCore import Qt, QRectF, QPointF, QTimer, Signal, QVariantAnimation
from PySide6.QtGui import QColor, QPen, QPainter, QBrush, QCursor, QMouseEvent, QUndoStack
from PySide6.QtGui import QColor, QPen, QPainter, QBrush, QCursor, QMouseEvent, QUndoStack, QPixmap
from enum import Enum, auto

from graphics.text.text_node_model import TextNodeModel
from graphics.text.text_controller import TextController

from core.commands import AddItemCommand
from graphics.animated_stroke_item import AnimatedStrokeItem
from graphics.hand_item import HandItem
from core.settings_manager import SettingsManager

from graphics.animated_image_item import AnimatedImageItem
from core.animator_engine import AnimatorEngine

from graphics.artboard_item import SceneArtboardItem
from asset_library.engine.svg_canvas_item import SVGCanvasItem

class ToolMode(Enum):
    SELECT = auto()
    PAN = auto()
    ERASER = auto()
    SHAPE = auto()
    TEXT = auto()
    WRITE_TO_IMAGE = auto()
    MIND_MAP = auto()

from .view import CustomGraphicsView

class CanvasWorkspace(QFrame):
    scene_added = Signal(int)
    scene_deleted = Signal(int)
    zoom_changed = Signal(int)
    item_selected = Signal(object) # Emits the AnimatedStrokeItem
    items_changed = Signal(list) # Emits the list of user_items
    audio_items_changed = Signal(list) # Emits the list of audio_items
    animation_progress = Signal(float) # Emits current time in seconds
    item_loading_state_changed = Signal(bool)
    tool_mode_changed = Signal(str)
    
    def __init__(self):
        super().__init__()
        self.setObjectName("CenterWorkspace")
        self._first_show = True
        self.current_scene_index = 0
        self.current_mode = ToolMode.SELECT
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        self.scene = QGraphicsScene()
        # Darker gray background for the infinite workspace outside the artboard
        self.scene.setBackgroundBrush(QColor("#1A1D1A")) 
        self.scene.selectionChanged.connect(self._on_selection_changed)
        
        self.undo_stack = QUndoStack(self)
        self.undo_stack.indexChanged.connect(self._on_undo_changed)
        
        self.artboards = []
        self.user_items = []
        self.audio_items = []
        
        self.add_new_scene() # Adds the first default artboard
        
        # Give an "infinite" canvas feel so the user can pan around (allows ~40 scenes without clipping)
        self.scene.setSceneRect(QRectF(-50000, -50000, 100000, 100000))
        
        # Central Animator Engine
        self.hand_item = HandItem()
        self.hand_item.setZValue(9999) # Make sure hand is always on top of EVERYTHING
        self.hand_item.hide()
        self.scene.addItem(self.hand_item)
        
        from components.write_to_image.hand_manager import WritingHandItem
        self.writing_hand_item = WritingHandItem()
        self.writing_hand_item.setZValue(9999)
        self.writing_hand_item.hide()
        self.scene.addItem(self.writing_hand_item)
        
        self.animator_engine = AnimatorEngine(self.hand_item, self, writing_hand_item=self.writing_hand_item)
        self.animator_engine.progress_updated.connect(self.animation_progress.emit)
        self.animator_engine.progress_updated.connect(self._on_progress_updated)
        
        # Central Audio Engine
        from core.audio_engine.audio_engine import AudioEngine
        self.audio_engine = AudioEngine(self)
        self.animator_engine.progress_updated.connect(self.audio_engine.on_progress_updated)
        
        # Clipboard Manager
        from core.clipboard.clipboard_manager import ClipboardManager
        self.clipboard = ClipboardManager(self)
        
        self.view = CustomGraphicsView(self, self.scene)
        self.view.setRenderHint(QPainter.RenderHint.Antialiasing | QPainter.RenderHint.SmoothPixmapTransform)
        
        # 🚀 Phase 4: Hybrid Rendering (Multi-pass / GPU Acceleration)
        # Check if the user enabled the Beta GPU option
        settings = SettingsManager()
        use_gpu = settings.get("use_gpu_acceleration", False)
        
        if use_gpu:
            try:
                from PySide6.QtOpenGLWidgets import QOpenGLWidget
                from PySide6.QtGui import QSurfaceFormat
                
                gl_format = QSurfaceFormat()
                gl_format.setSamples(4) # Anti-aliasing
                
                gl_widget = QOpenGLWidget()
                gl_widget.setFormat(gl_format)
                
                # Apply the OpenGL widget as the viewport
                self.view.setViewport(gl_widget)
                
                # Full viewport update is necessary for OpenGL to avoid artifacting
                self.view.setViewportUpdateMode(QGraphicsView.ViewportUpdateMode.FullViewportUpdate)
                print("[Hybrid Engine]: GPU Hardware Acceleration Enabled (Beta).")
            except Exception as e:
                print(f"[Hybrid Engine]: Failed to initialize GPU: {e}. Falling back to CPU.")
                self.view.setViewportUpdateMode(QGraphicsView.ViewportUpdateMode.SmartViewportUpdate)
        else:
            # Safe CPU Mode
            self.view.setViewportUpdateMode(QGraphicsView.ViewportUpdateMode.SmartViewportUpdate)
            print("[Hybrid Engine]: CPU Safe Mode Enabled.")
        
        # Allow dragging the canvas around (panning)
        self.view.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
        
        layout.addWidget(self.view)
        
        # Transition system — must be created AFTER self.view exists
        from core.transitions import TransitionManager
        self.transition_manager = TransitionManager(self.view)
        
    def _on_progress_updated(self, time_sec: float):
        if not hasattr(self, 'scene_windows'):
            return
            
        for window in self.scene_windows:
            # 1. Handle Scene Camera Focus — instant jump during playback (no animation)
            if window['start'] <= time_sec < window['end']:
                if self.current_scene_index != window['scene_index']:
                    self.focus_on_artboard(window['scene_index'], animated=False)
                    
            # 2. Handle Transitions
            if window['transition_start'] < time_sec < window['transition_end'] and not window['transition_played']:
                window['transition_played'] = True
                self._play_transition_for_window(window)
                
    def reset_transition_flags(self):
        if hasattr(self, 'scene_windows'):
            for window in self.scene_windows:
                window['transition_played'] = False
                
    def _play_transition_for_window(self, window):
        prev_idx = window['scene_index'] - 1
        if prev_idx < 0 or prev_idx >= len(self.artboards): return
        
        transition_type = getattr(self.artboards[prev_idx], 'transition_type', None)
        if not transition_type or transition_type == "None": return
        
        color = getattr(self.artboards[prev_idx], 'transition_color', '#000000') or '#000000'
        t_dur = getattr(self.artboards[prev_idx], 'transition_duration', 1.0)
        
        # Hide the hand immediately when a transition starts
        if hasattr(self, 'animator_engine'):
            self.animator_engine.hand_item.hide()
            self.animator_engine.hand_item.set_ink_active(False)
            
        self.transition_manager.play_transition(
            transition_type,
            color=color,
            duration_sec=t_dur,
            on_scene_start=lambda: self.focus_on_artboard(window['scene_index'], animated=False)
        )
        
    def _on_transition_requested(self, scene_index: int, transition_type: str):
        # Deprecated: Now handled by absolute time in _on_progress_updated
        pass
        
    def _on_scene_changed(self, scene_index: int):
        # scene_index is 1-based, convert to 0-based for list access
        target_idx = max(0, scene_index - 1)
        self.focus_on_artboard(target_idx)

    def showEvent(self, event):
        super().showEvent(event)
        if self._first_show and self.artboards:
            self._first_show = False
            # Center instantly on the first show without animation to guarantee correct layout
            self.current_scene_index = 0
            self.view.centerOn(self.artboards[0].sceneBoundingRect().center())
        
    def _on_selection_changed(self):
        try:
            items = self.scene.selectedItems()
            if items:
                self.item_selected.emit(items[0])
            else:
                self.item_selected.emit(None)
        except RuntimeError:
            pass
            
    def add_new_scene(self):
        # Prevent UI lag from Inspector trying to update while scenes are shifting
        self.scene.clearSelection()
        
        x_offset = 0
        if self.artboards:
            last_board = self.artboards[-1]
            x_offset = last_board.x() + last_board.rect().width() + 400 # 400px gap
            
        settings = SettingsManager()
        
        # Load from Settings
        saved_ratio = settings.get("canvas_size", "16:9")
        ratio_map = {
            "16:9": (1920, 1080), 
            "1:1": (1080, 1080), 
            "9:16": (1080, 1920), 
            "4:3": (1024, 768)
        }
        w, h = ratio_map.get(saved_ratio, (1920, 1080))
            
        new_board = SceneArtboardItem(QRectF(0, 0, w, h))
        new_board.duration = 2.0
        new_board.setPos(x_offset, 0)
        self.scene.addItem(new_board)
        self.artboards.append(new_board)
        
        self.update_scene_indices()
        
        index = len(self.artboards) - 1
        self.scene_added.emit(index)
        
        if hasattr(self, 'view') and not getattr(self, '_first_show', False):
            # Only auto-focus if this is a newly added scene by user after app has started
            self.focus_on_artboard(index)
            
    def delete_scene(self, index: int):
        if 0 <= index < len(self.artboards):
            board = self.artboards.pop(index)
            
            # Remove all user items that belong to this board to prevent C++ deleted object errors
            items_to_remove = [item for item in self.user_items if item.parentItem() == board]
            for item in items_to_remove:
                if item in self.user_items:
                    self.user_items.remove(item)
                    
            self.scene.removeItem(board)
            self.update_scene_indices()
            self.scene_deleted.emit(index)
            
            # Re-focus on the nearest available artboard
            if self.artboards:
                new_focus = max(0, index - 1)
                self.focus_on_artboard(new_focus)
            else:
                # If all scenes deleted, let the timeline clear out
                self.items_changed.emit([])

    def clear_all(self):
        """Clears all artboards, items, and audio nodes. Leaves the workspace completely empty."""
        self.animator_engine.stop()
        self.audio_engine.stop_all()
        
        # Remove items from scene
        for item in self.user_items:
            self.scene.removeItem(item)
        self.user_items.clear()
        
        # Remove artboards backwards to notify UI safely
        for i in range(len(self.artboards) - 1, -1, -1):
            board = self.artboards[i]
            self.scene.removeItem(board)
            self.scene_deleted.emit(i)
        self.artboards.clear()
        
        self.audio_items.clear()
        self.audio_engine.clear_tracks()
        self.undo_stack.clear()
        self.current_scene_index = 0
        
        # Reset animator engine completely
        self.animator_engine.current_time_sec = 0.0
        self.animator_engine.total_time_passed = 0.0
        self.animator_engine.sync_queue([], force_recompile=True)
        self.animator_engine.schedule = []
        
        # Force the UI to reset the timer label to 00:00.0 / 00:00.0
        self.animation_progress.emit(0.0)
        
        # Emit empty lists to clear timeline completely
        self.items_changed.emit([])
        self.audio_items_changed.emit([])

    def initialize_new_project(self):
        """Used when starting a completely new project. Clears everything and adds a default scene."""
        self.clear_all()
        
        # Create a fresh clean artboard for the new project
        self.add_new_scene()
        self.focus_on_artboard(0, animated=False)
        
        # Distribute time so timeline rebuilds with the new scene
        self.distribute_global_time(respect_board_duration=True)
        
        # Auto-fit the canvas to the user's screen
        self.reset_zoom()

    def update_scene_indices(self):
        for idx, board in enumerate(self.artboards):
            board.scene_index = idx + 1
            board.total_scenes = len(self.artboards)
            board.update() # Force repaint
            
    def focus_on_artboard(self, index: int, animated: bool = True):
        """
        Move the camera to the given artboard.
        
        Args:
            animated: If True (default), performs a smooth 600ms camera pan — used
                      for manual scene selection (sidebar clicks, user navigation).
                      If False, jumps instantly — used during automatic playback to
                      avoid animation spam and jitter.
        """
        if not hasattr(self, 'view'): return
        if 0 <= index < len(self.artboards):
            old_index = getattr(self, 'current_scene_index', -1)
            self.current_scene_index = index
            
            if old_index != index:
                QTimer.singleShot(0, lambda: self.items_changed.emit(self.user_items))
                
            target_board = self.artboards[index]
            target_pos = target_board.sceneBoundingRect().center()
            
            if animated:
                # Guard: don't start a new animation if one is already running
                if getattr(self, '_animating_camera', False):
                    return
                
                viewport_rect = self.view.viewport().rect()
                current_pos = self.view.mapToScene(viewport_rect.center())
                
                self._animating_camera = True
                self.cam_anim = QVariantAnimation(self)
                self.cam_anim.setDuration(600)  # Smooth 600ms pan
                self.cam_anim.setStartValue(current_pos)
                self.cam_anim.setEndValue(target_pos)
                self.cam_anim.valueChanged.connect(self.view.centerOn)
                self.cam_anim.finished.connect(self._on_cam_anim_finished)
                self.cam_anim.start()
            else:
                # Instant snap — used during playback and project initialization
                if hasattr(self, 'cam_anim') and self.cam_anim.state() == QVariantAnimation.State.Running:
                    self.cam_anim.stop()
                    self._animating_camera = False
                self.view.centerOn(target_pos)
            
            # Update timeline for the new scene
            self.items_changed.emit(self.get_current_scene_items())

    def _on_cam_anim_finished(self):
        self._animating_camera = False

    def _on_item_plan_started(self):
        self.item_loading_state_changed.emit(True)

    def _on_item_plan_ready(self):
        self.item_loading_state_changed.emit(False)
            
    def set_scene_duration_and_scale(self, board, new_dur):
        """
        Sets the scene duration and scales all animated items inside it 
        so their total duration matches the new scene duration.
        """
        new_dur = max(2.0, float(new_dur))
        board.duration = new_dur
        board.user_defined_duration = new_dur
        
        scene_items = [item for item in self.user_items if item.parentItem() == board]
        anim_items = [item for item in scene_items if hasattr(item, '_anim_duration')]
        
        if anim_items:
            # Calculate current total duration of items
            total_dur = 0.0
            for item in anim_items:
                item_dur = getattr(item, 'anim_duration', None)
                if item_dur is None:
                    item_dur = getattr(item, '_anim_duration', 8.0)
                if hasattr(item, 'get_item_progress_offset'):
                    item_dur += item.get_item_progress_offset()
                total_dur += item_dur
                
            if total_dur > 0:
                scale_factor = new_dur / total_dur
                for item in anim_items:
                    old_item_dur = getattr(item, 'anim_duration', None)
                    if old_item_dur is None:
                        old_item_dur = getattr(item, '_anim_duration', 8.0)
                        
                    # Apply scale to each item — do NOT set board.duration again inside distribute
                    item.anim_duration = max(0.1, old_item_dur * scale_factor)
                    
        # Use respect_board_duration=True so distribute_global_time won't overwrite
        # the new board.duration we just set above with the old items' total
        self.distribute_global_time(respect_board_duration=True)

    def distribute_global_time(self, respect_board_duration=False):
        """
        Distributes absolute delay times across all scenes and their items.
        Offloads the heavy calculation to AsyncEngine to prevent UI lag.
        """
        if not self.artboards: return
        
        from core.async_engine.engine import AsyncEngine
        
        def calculate_times():
            # Work on snapshots to avoid thread collisions if UI modifies them
            boards = list(self.artboards)
            items = list(self.user_items)
            
            current_time = 0.0
            new_scene_windows = []

            for i, board in enumerate(boards):
                try:
                    t_dur = 0.0
                    if current_time > 0 and i > 0:
                        prev_board = boards[i - 1]
                        t_type = getattr(prev_board, 'transition_type', None)
                        if t_type and t_type != "None":
                            t_dur = getattr(prev_board, 'transition_duration', 1.0)
                        else:
                            t_dur = 0.0
                        current_time += t_dur
                        
                    scene_items = [item for item in items if getattr(item, 'parentItem', lambda: None)() == board]
                    anim_items = [item for item in scene_items if hasattr(item, '_anim_duration')]
                    
                    total_items_duration = 0.0
                    if anim_items:
                        temp_start = 0.0
                        for item in anim_items:
                            item_dur = getattr(item, 'anim_duration', getattr(item, '_anim_duration', 8.0))
                            if hasattr(item, 'get_item_progress_offset'):
                                item_dur += item.get_item_progress_offset()
                            item.anim_delay = temp_start
                            temp_start += item_dur
                            
                        from core.scheduler import SmartScheduler
                        temp_scheduler = SmartScheduler(hand_speed=500)
                        # This compile is the heavy CPU operation
                        temp_schedule = temp_scheduler.compile(anim_items)
                        
                        if temp_schedule:
                            total_items_duration = temp_schedule[-1]['end']
                            for action in temp_schedule:
                                if action['type'] == 'draw' and action['item']:
                                    action['item'].anim_delay = action['start']
                    
                    DEFAULT_SCENE_DUR = 2.0
                    if not anim_items:
                        # Empty scene (all items removed or fresh): restore/maintain default 2.0s
                        user_dur = getattr(board, 'user_defined_duration', None)
                        if user_dur is not None and user_dur >= DEFAULT_SCENE_DUR:
                            actual_dur = user_dur
                        else:
                            actual_dur = DEFAULT_SCENE_DUR
                        board.duration = actual_dur
                    else:
                        if respect_board_duration:
                            actual_dur = max(DEFAULT_SCENE_DUR, getattr(board, 'duration', total_items_duration))
                        else:
                            actual_dur = max(DEFAULT_SCENE_DUR, total_items_duration)
                            board.duration = actual_dur
                    
                    new_scene_windows.append({
                        'scene_index': i,
                        'start': current_time,
                        'end': current_time + actual_dur,
                        'transition_start': current_time - t_dur if t_dur > 0 else 0.0,
                        'transition_end': current_time if t_dur > 0 else 0.0,
                        'transition_played': False
                    })
                    
                    if anim_items:
                        for item in anim_items:
                            item.anim_delay += current_time
                            
                    current_time += actual_dur
                except Exception as e:
                    # Ignore deleted items
                    pass
                    
            self.scene_windows = new_scene_windows
            
            # This triggers UI updates (must be marshaled by Qt to main thread)
            sorted_items = sorted(items, key=lambda x: (getattr(x, 'anim_delay', 0.0), getattr(x, 'zValue', lambda: 0)()))
            self.animator_engine.sync_queue(sorted_items, force_recompile=True)
            self.items_changed.emit(items)
            
        # Run synchronously on the main thread to prevent C++ segmentation faults!
        calculate_times()

    def get_current_scene_items(self):
        if not self.artboards:
            return []
        target_board = self.artboards[self.current_scene_index]
        
        valid_items = []
        for item in list(self.user_items):
            try:
                # This will raise RuntimeError if the C++ object is deleted
                if item.parentItem() == target_board:
                    valid_items.append(item)
            except RuntimeError:
                # Object was deleted natively, remove from tracking
                self.user_items.remove(item)
                
        return valid_items
            
    def add_audio_node(self, file_path: str, layer_name: str):
        from core.audio_engine.audio_node import AudioNodeModel
        node = AudioNodeModel(file_path, layer_name)
        
        # Calculate auto-sequential delay for audio
        layer_audio = [item for item in self.audio_items if item.layer_name == layer_name]
        max_end_time = 0.0
        for item in layer_audio:
            end = item.anim_delay + item.anim_duration
            if end > max_end_time:
                max_end_time = end
        
        node.anim_delay = max_end_time
        self.audio_items.append(node)
        
        self.items_changed.emit(self.user_items) # Trigger timeline refresh
        self.audio_items_changed.emit(self.audio_items) # Update library
        return node
        
    def remove_audio_node(self, node):
        if node in self.audio_items:
            self.audio_items.remove(node)
            
            # Remove the matching track from AudioEngine safely via signal
            if hasattr(self, 'audio_engine'):
                self.audio_engine.remove_track(node.file_path)
                        
            # Defer the UI rebuild to prevent lag while memory is being cleaned up
            from PySide6.QtCore import QTimer
            QTimer.singleShot(0, lambda: self.items_changed.emit(self.user_items))
            QTimer.singleShot(0, lambda: self.audio_items_changed.emit(self.audio_items))
            
    def _calculate_auto_placement_delay(self, target_board) -> float:
        items_in_scene = [item for item in self.user_items if item.parentItem() == target_board]
        if not items_in_scene:
            return 0.0
            
        max_end_time = 0.0
        for item in items_in_scene:
            delay = getattr(item, 'anim_delay', getattr(item, '_anim_delay', 0.0))
            dur = getattr(item, 'anim_duration', getattr(item, '_anim_duration', 0.0))
            end_time = delay + dur
            if end_time > max_end_time:
                max_end_time = end_time
                
        return max_end_time + 0.1
            
    def preview_item_motion(self, item):
        """
        Executes a targeted, isolated motion preview for a single item.
        Does not disrupt the rest of the project or audio tracks.
        """
        if not item:
            return
            
        # Stop any active global playback
        self.animator_engine.stop()
        
        # Determine parent scene artboard if any
        parent_board = item.parentItem()
        if parent_board in self.artboards:
            target_idx = self.artboards.index(parent_board)
            if self.current_scene_index != target_idx:
                self.focus_on_artboard(target_idx, animated=False)
                
        # Synchronize queue with the item's scene items
        scene_items = self.get_current_scene_items()
        if item not in scene_items and item in self.user_items:
            scene_items = [item]
        elif not scene_items:
            scene_items = [item]
            
        self.animator_engine.sync_queue(scene_items, force_recompile=True)
        
        # Locate the action in compiled schedule
        target_act = None
        for act in self.animator_engine.schedule:
            if act.get('type') == 'draw' and act.get('item') is item:
                target_act = act
                break
                
        if target_act:
            self.animator_engine.play_range(target_act['start'], target_act['end'])
        else:
            delay = float(getattr(item, 'anim_delay', getattr(item, '_anim_delay', 0.0)))
            dur = float(getattr(item, 'anim_duration', getattr(item, '_anim_duration', 1.5)))
            self.animator_engine.play_range(delay, delay + dur)

    def add_item_to_scene(self, item):
        if not self.artboards: return
        target_board = self.artboards[self.current_scene_index]
        item.setParentItem(target_board)
        self.user_items.append(item)
        self.items_changed.emit(self.user_items)

    def add_image_from_path(self, file_path: str):
        if not self.artboards:
            return
            
        target_board = self.artboards[self.current_scene_index]
        
        pixmap = QPixmap(file_path)
        if pixmap.isNull():
            return
            
        import os
        filename = os.path.basename(file_path)
        
        from core.drawing_engine.smart_bridge.router import create_smart_item
        img_item = create_smart_item(file_path, pixmap)
        
        img_item.image_path = file_path # CRITICAL FIX: Ensure image is saved with project
        img_item.draw_order = len(self.get_current_scene_items()) + 1
        
        # Use the standard 8.0s hardcoded default for new images
        if hasattr(img_item, 'set_anim_duration'):
            img_item.set_anim_duration(8.0)
        else:
            img_item.anim_duration = 8.0
            
        img_item.anim_delay = self._calculate_auto_placement_delay(target_board)
        
        # Remove timestamp prefix if it exists (added by db_service)
        display_name = filename.split('_', 1)[-1] if '_' in filename else filename
        img_item.layer_name = display_name[:15]
        
        # Force camera to focus on the active scene before adding
        self.focus_on_artboard(self.current_scene_index)
        
        # [Phase 8 FIX]: Smart Image Scaling (Zero-Risk)
        # Calculate optimal scale relative to the artboard (target: ~50% of canvas)
        board_rect = target_board.boundingRect()
        img_rect = img_item.boundingRect()
        
        target_w = board_rect.width() * 0.5
        target_h = board_rect.height() * 0.5
        
        scale_x = target_w / img_rect.width() if img_rect.width() > 0 else 1.0
        scale_y = target_h / img_rect.height() if img_rect.height() > 0 else 1.0
        
        optimal_scale = min(scale_x, scale_y)
        img_item.setScale(optimal_scale)
        
        # Always place perfectly in the mathematical center of the active scene
        local_center = board_rect.center()
        
        img_scale = optimal_scale
        center_x = local_center.x() - ((img_rect.width() * img_scale) / 2)
        center_y = local_center.y() - ((img_rect.height() * img_scale) / 2)
        
        # We removed the strict clamping here so that images are not forced to the top edge when they are larger than the artboard.
        
        img_item.setPos(center_x, center_y)
        img_item.setParentItem(target_board)
        
        cmd = AddItemCommand(self.scene, img_item, self.user_items, "Add Image")
        self.undo_stack.push(cmd)
        
        # Distribute time among all images in the scene automatically
        self.distribute_global_time(respect_board_duration=False)
        
        self.items_changed.emit(self.get_current_scene_items())
        
        if hasattr(img_item, 'plan_started') and hasattr(img_item, 'plan_ready'):
            img_item.plan_started.connect(self._on_item_plan_started)
            img_item.plan_ready.connect(self._on_item_plan_ready)
        
        # START ANALYSIS IMMEDIATELY
        if hasattr(img_item, 'build_plan_async'):
            img_item.build_plan_async()
        elif hasattr(img_item, 'update_plan'):
            img_item.update_plan()

    def add_svg_from_path(self, file_path: str):
        if not self.artboards:
            return
            
        target_board = self.artboards[self.current_scene_index]
        
        import os
        filename = os.path.basename(file_path)
        
        svg_item = SVGCanvasItem(file_path)
        
        # Minimal properties for timeline compatibility in MVP
        svg_item.anim_duration = 2.0
        svg_item.anim_delay = self._calculate_auto_placement_delay(target_board)
        svg_item.layer_name = filename[:15]
        svg_item.draw_order = len(self.get_current_scene_items()) + 1
        
        # Force camera to focus on the active scene before adding
        self.focus_on_artboard(self.current_scene_index)
        
        # [Phase 8 FIX]: Smart Image Scaling for SVGs
        board_rect = target_board.boundingRect()
        svg_rect = svg_item.boundingRect()
        
        target_w = board_rect.width() * 0.5
        target_h = board_rect.height() * 0.5
        
        scale_x = target_w / svg_rect.width() if svg_rect.width() > 0 else 1.0
        scale_y = target_h / svg_rect.height() if svg_rect.height() > 0 else 1.0
        
        optimal_scale = min(scale_x, scale_y)
        svg_item.setScale(optimal_scale)
        
        # Always place perfectly in the mathematical center of the active scene
        local_center = board_rect.center()
        
        svg_scale = optimal_scale
        center_x = local_center.x() - ((svg_rect.width() * svg_scale) / 2)
        center_y = local_center.y() - ((svg_rect.height() * svg_scale) / 2)
        
        svg_item.setPos(center_x, center_y)
        svg_item.setParentItem(target_board)
        
        cmd = AddItemCommand(self.scene, svg_item, self.user_items, "Add SVG")
        self.undo_stack.push(cmd)
        
        self.item_loading_state_changed.emit(True)
        svg_item.plan_ready.connect(self._on_item_plan_ready)
        svg_item.build_plan_async()
        
        self.distribute_global_time(respect_board_duration=False)
        self.items_changed.emit(self.get_current_scene_items())

    def set_tool_mode(self, mode: str):
        mode_map = {
            "Select": ToolMode.SELECT,
            "Pan": ToolMode.PAN,
            "Eraser": ToolMode.ERASER,
            "Shape": ToolMode.SHAPE,
            "Text": ToolMode.TEXT,
            "WriteToImage": ToolMode.WRITE_TO_IMAGE,
            "MindMap": ToolMode.MIND_MAP
        }
        self.current_mode = mode_map.get(mode, ToolMode.SELECT)
        
        # Update view drag mode based on tool
        if hasattr(self, 'view'):
            if self.current_mode == ToolMode.PAN:
                self.view.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
            elif self.current_mode == ToolMode.SELECT:
                self.view.setDragMode(QGraphicsView.DragMode.RubberBandDrag)
            else:
                self.view.setDragMode(QGraphicsView.DragMode.NoDrag)
                
            if self.current_mode in (ToolMode.TEXT, ToolMode.WRITE_TO_IMAGE):
                self.view.setCursor(Qt.CursorShape.IBeamCursor)
            elif self.current_mode == ToolMode.SELECT:
                self.view.setCursor(Qt.CursorShape.ArrowCursor)
                
        self.tool_mode_changed.emit(mode)
            # Pan cursor is handled by ScrollHandDrag automatically

    def fit_canvas(self):
        if not self.artboards: return
        # Calculate bounding rect of all artboards
        rect = self.artboards[0].sceneBoundingRect()
        for ab in self.artboards[1:]:
            rect = rect.united(ab.sceneBoundingRect())
            
        # Add 10% padding
        rect.adjust(-rect.width()*0.1, -rect.height()*0.1, rect.width()*0.1, rect.height()*0.1)
        self.view.fitInView(rect, Qt.AspectRatioMode.KeepAspectRatio)
        
        # Calculate new zoom level
        current_scale = self.view.transform().m11()
        self.zoom_changed.emit(int(current_scale * 100))

    def zoom_in(self):
        if not hasattr(self, 'view'): return
        self.is_fit_mode = False
        self.view.scale(1.2, 1.2)
        self._emit_zoom()

    def zoom_out(self):
        if not hasattr(self, 'view'): return
        self.is_fit_mode = False
        self.view.scale(1.0 / 1.2, 1.0 / 1.2)
        self._emit_zoom()
        
    def reset_zoom(self):
        """Now used as fit_to_screen instead of absolute 100% to support all monitors."""
        self.fit_to_screen()
        
    def fit_to_screen(self):
        if not hasattr(self, 'view') or not self.artboards: 
            return
        
        board = self.artboards[self.current_scene_index]
        viewport_rect = self.view.viewport().rect()
        
        margin = 40
        vw = viewport_rect.width() - margin * 2
        vh = viewport_rect.height() - margin * 2
        
        if vw <= 0 or vh <= 0:
            return
            
        bw = board.rect().width()
        bh = board.rect().height()
        
        if bw <= 0 or bh <= 0:
            return
            
        scale_w = vw / bw
        scale_h = vh / bh
        best_scale = min(scale_w, scale_h)
        
        # Guard: don't start a new animation if one is already running
        if getattr(self, '_animating_camera', False) and hasattr(self, 'cam_anim') and self.cam_anim.state() == QVariantAnimation.State.Running:
            self.cam_anim.stop()
            self._animating_camera = False

        self.view.resetTransform()
        self.view.scale(best_scale, best_scale)
        self.view.centerOn(board.sceneBoundingRect().center())
        
        self.is_fit_mode = True
        self.zoom_changed.emit(0) # 0 means "Fit"
        
    def _emit_zoom(self):
        # Calculate current zoom percentage based on m11 (horizontal scaling)
        zoom_level = int(self.view.transform().m11() * 100)
        self.zoom_changed.emit(zoom_level)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        # Handle dynamic resize (e.g. moving across multi-monitors)
        if getattr(self, 'is_fit_mode', True):
            # Defer execution to let Qt update viewport rects first
            from PySide6.QtCore import QTimer
            QTimer.singleShot(50, self.fit_to_screen)

    def mousePressEvent(self, event: QMouseEvent):
        super().mousePressEvent(event)
        
        # Handle Write-To-Image Tool
        if self.current_mode == ToolMode.WRITE_TO_IMAGE:
            view_pos = self.view.mapFromParent(event.pos())
            self.trigger_write_to_image_at_view_pos(view_pos)
            
    def trigger_write_to_image_at_view_pos(self, view_pos):
        if not self.artboards or self.current_scene_index < 0 or self.current_scene_index >= len(self.artboards):
            return
            
        target_board = self.artboards[self.current_scene_index]
        scene_pos = self.view.mapToScene(view_pos)
        board_click_pos = target_board.mapFromScene(scene_pos)
        
        from components.write_to_image import WriteToImageModel, TextEditorWidget, WriteToImageGraphicsItem
        
        model = WriteToImageModel(
            id=f"wti_{id(self)}_{int(scene_pos.x())}",
            name="Text Image",
            pos_x=board_click_pos.x(),
            pos_y=board_click_pos.y(),
            font_size=42,
            duration=0.0  # Let text_editor calculate it based on text length
        )
        editor = TextEditorWidget(view_pos.x(), view_pos.y(), existing_model=model, parent=self.view, center_in_view=False)
        
        def _on_finish(updated_model):
            if updated_model and updated_model.image_path:
                item = WriteToImageGraphicsItem(updated_model, canvas_workspace=self)
                # Auto placement
                item.anim_delay = self._calculate_auto_placement_delay(target_board)
                # Add to target board
                item.setParentItem(target_board)

                # Smart Text Auto-Fit: Proportion to active artboard (target: ~50-60% of artboard width)
                board_rect = target_board.boundingRect()
                text_rect = item.boundingRect()
                if text_rect.width() > 0 and board_rect.width() > 0:
                    desired_scale_w = (board_rect.width() * 0.55) / text_rect.width()
                    desired_scale_h = (board_rect.height() * 0.35) / text_rect.height() if text_rect.height() > 0 else desired_scale_w
                    optimal_scale = min(desired_scale_w, desired_scale_h)
                    optimal_scale = max(1.0, min(optimal_scale, 5.0))
                    item.setScale(optimal_scale)
                    if hasattr(item, 'model') and item.model:
                        item.model.scale_w = optimal_scale
                        item.model.scale_h = optimal_scale

                    # Place at user's click position on target_board, clamped within board_rect
                    pos_x = board_click_pos.x()
                    pos_y = board_click_pos.y()
                    
                    scaled_w = text_rect.width() * optimal_scale
                    scaled_h = text_rect.height() * optimal_scale
                    
                    max_x = max(0.0, board_rect.width() - scaled_w)
                    max_y = max(0.0, board_rect.height() - scaled_h)
                    
                    clamped_x = max(0.0, min(pos_x, max_x))
                    clamped_y = max(0.0, min(pos_y, max_y))
                    
                    item.setPos(clamped_x, clamped_y)
                    if hasattr(item, 'model') and item.model:
                        item.model.pos_x = clamped_x
                        item.model.pos_y = clamped_y

                if item.scene() is None:
                    self.scene.addItem(item)
                self.user_items.append(item)
                self.distribute_global_time(respect_board_duration=False)
                self.items_changed.emit(self.get_current_scene_items())
        
        editor.editing_finished.connect(_on_finish)
        editor.show()
        editor.setFocus()
        
        # Switch back to select mode automatically
        self.set_tool_mode("Select")
        # Need to update UI button if possible, but for now we just change mode internally.
            
        # [FROZEN: CWE] Disable Text Mode Node Creation
        # if self.current_mode == ToolMode.TEXT:
        
    def add_mind_map_node(self, shape_type: str, view_pos):
        if not self.artboards:
            return
            
        target_board = self.artboards[self.current_scene_index]
        scene_pos = self.view.mapToScene(view_pos)
        
        from components.mind_map_builder.models import MindMapNodeModel
        from components.mind_map_builder.node_item import MindMapNodeItem
        
        model = MindMapNodeModel(
            id=f"mm_{id(self)}_{int(scene_pos.x())}",
            name="Mind Map Node",
            pos_x=scene_pos.x(),
            pos_y=scene_pos.y(),
            shape_type=shape_type,
            text="New Idea",
            width=150.0,
            height=80.0
        )
        
        node_item = MindMapNodeItem(model, canvas_workspace=self)
        node_item.anim_delay = self._calculate_auto_placement_delay(target_board)
        node_item.setParentItem(target_board)
        self.scene.addItem(node_item)
        self.user_items.append(node_item)
        self.distribute_global_time(respect_board_duration=False)
        self.items_changed.emit(self.get_current_scene_items())
        
        self.set_tool_mode("Select")

        #     # Setup connections
        #     controller.workspace = self
        #     
        #     # 3. Add to scene
        #     text_node.setParentItem(target_board)
        #     self.user_items.append(text_node)
        #     self.items_changed.emit(self.user_items)
        #     
        #     # Select it immediately so the blue box is visible during drag
        #     self.scene.clearSelection()
        #     text_node.setSelected(True)
        #     
        #     # 4. Save state for potential Area Text dragging
        #     self._drawing_text_node = text_node
        #     self._drawing_text_start_pos = scene_pos
        pass
            
    def mouseMoveEvent(self, event: QMouseEvent):
        super().mouseMoveEvent(event)
        # [FROZEN: CWE] Disable Text Node resizing
        # if self.current_mode == ToolMode.TEXT and getattr(self, '_drawing_text_node', None):
        #     view_pos = self.view.mapFromParent(event.pos())
        #     scene_pos = self.view.mapToScene(view_pos)
        #     
        #     # Calculate width (only dragging to the right for now)
        #     drag_dist = scene_pos.x() - self._drawing_text_start_pos.x()
        #     if drag_dist > 20:
        #         width = max(50, drag_dist)
        #         self._drawing_text_node.model.fixed_width = width
        #         self._drawing_text_node.setTextWidth(width)
        #     else:
        #         self._drawing_text_node.model.fixed_width = -1
        #         self._drawing_text_node.setTextWidth(-1)
        #         
        #     self._drawing_text_node.sync_from_model()
        pass
            
    def mouseReleaseEvent(self, event: QMouseEvent):
        super().mouseReleaseEvent(event)
        # [FROZEN: CWE] Disable Text Node release mode
        # if self.current_mode == ToolMode.TEXT and getattr(self, '_drawing_text_node', None):
        #     text_node = self._drawing_text_node
        #     self._drawing_text_node = None
        #     
        #     # Switch back to select mode and activate edit state
        #     self.set_tool_mode("Select")
        #     text_node.controller.set_state(text_node, "editing")
        #     
        #     # Force focus so user can type immediately
        #     from PySide6.QtCore import QTimer
        #     QTimer.singleShot(0, lambda: text_node.setFocus())
        pass


    def _on_undo_changed(self, idx=None):
        self.distribute_global_time(respect_board_duration=True)
        self.items_changed.emit(self.get_current_scene_items())
        
    def delete_selected_items(self):
        items_to_delete = [item for item in self.user_items if item.isSelected()]
        if not items_to_delete: return
        for item in items_to_delete:
            self.delete_item(item)
            
    def delete_timeline_item(self, item):
        if "AudioNodeModel" in item.__class__.__name__:
            self.remove_audio_node(item)
        else:
            self.delete_item(item)
            
    def delete_item(self, item):
        if item in self.user_items:
            self.user_items.remove(item)
            self.scene.removeItem(item)
            if hasattr(self, 'animator_engine') and self.animator_engine:
                if hasattr(self.animator_engine, 'hand_item') and self.animator_engine.hand_item:
                    self.animator_engine.hand_item.hide()
                if hasattr(self.animator_engine, 'writing_hand_item') and self.animator_engine.writing_hand_item:
                    self.animator_engine.writing_hand_item.hide()
            
            # If all items are deleted, stop any ongoing playback and reset playhead to 0
            if not self.user_items:
                if hasattr(self, 'animator_engine') and self.animator_engine:
                    self.animator_engine.stop()
                if hasattr(self, 'animation_progress'):
                    self.animation_progress.emit(0.0)
            
            # Redistribute time among remaining items
            self.distribute_global_time(respect_board_duration=False)
            
            # Immediately resync the animator engine queue to match the remaining items
            items_to_animate = list(self.user_items)
            if hasattr(self, 'animator_engine') and self.animator_engine:
                self.animator_engine.sync_queue(items_to_animate, force_recompile=True)
            
            self.items_changed.emit(items_to_animate)
            
    def play_animation(self):
        if not self.artboards: return
        
        self.animator_engine.stop()
        self.reset_transition_flags()
        
        # Sort items strictly by scene index, then by original insertion to maintain cross-scene flow
        sorted_items = sorted(self.user_items, key=lambda x: (getattr(x.parentItem(), 'scene_index', 0), self.user_items.index(x)))
        
        self.animator_engine.sync_queue(sorted_items)
            
        self.animator_engine.play()

    def seek_animation(self, time_sec: float):
        self.reset_transition_flags()
        sorted_items = sorted(self.user_items, key=lambda x: (getattr(x.parentItem(), 'scene_index', 0), self.user_items.index(x)))
        self.animator_engine.sync_queue(sorted_items)
        self.animator_engine.seek_only(time_sec)

    def play_scene_animation(self, scene_index: int, start_time: float = None, duration: float = None):
        """Plays animation preview and synchronized audio strictly for a specific scene."""
        if not self.artboards or scene_index < 0 or scene_index >= len(self.artboards):
            return
            
        self.animator_engine.stop()
        self.reset_transition_flags()
        
        # Focus canvas viewport on this artboard
        self.focus_on_artboard(scene_index)
        
        # Sort items strictly by scene index, then by insertion order
        sorted_items = sorted(self.user_items, key=lambda x: (getattr(x.parentItem(), 'scene_index', 0), self.user_items.index(x)))
        self.animator_engine.sync_queue(sorted_items)
        
        # If start_time or duration not explicitly passed, compute accurately from scene sequence
        if start_time is None or duration is None:
            curr_t = 0.0
            for i, board in enumerate(self.artboards):
                if i > 0 and curr_t > 0:
                    prev_b = self.artboards[i - 1]
                    t_type = getattr(prev_b, 'transition_type', None)
                    t_dur = getattr(prev_b, 'transition_duration', 1.0) if (t_type and t_type != "None") else 0.2
                    curr_t += t_dur
                b_dur = getattr(board, 'duration', 8.0)
                if i == scene_index:
                    start_time = curr_t
                    duration = b_dur
                    break
                curr_t += b_dur
                
        start_time = max(0.0, float(start_time or 0.0))
        end_time = start_time + max(0.5, float(duration or 8.0))
        
        self.animator_engine.play_range(start_time, end_time)


