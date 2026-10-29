"""
Purpose: The Synchronization Bridge (Animator Engine).
Features: Manages a sequence of animations, orchestrating the HandItem and multiple AnimatedStrokeItems in order.
"""
from PySide6.QtCore import QObject, QTimer, Signal, QPointF, Qt
from graphics.animated_stroke_item import AnimatedStrokeItem
from graphics.hand_item import HandItem
from core.scheduler import SmartScheduler
from core.settings_manager import SettingsManager
from core.audio_engine.sfx_engine import SFXSyncEngine
import math

class AnimatorEngine(QObject):
    finished = Signal()
    playback_started = Signal(bool)
    progress_updated = Signal(float) # Emits current time in seconds
    playback_error = Signal(str) # Emits error message on unhandled exception during playback
    
    def __init__(self, hand_item: HandItem, parent=None, writing_hand_item=None):
        super().__init__(parent)
        self.hand_item = hand_item
        self.writing_hand_item = writing_hand_item
        self.queue = []
        self.scheduler = SmartScheduler(hand_speed=500)
        self.schedule = []
        self.current_index = -1
        self._play_end_time = None
        self._pending_start_time = None
        self._pending_end_time = None
        
        self.sfx_engine = SFXSyncEngine(self)
        
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._update_loop)
        
        self.total_time_passed = 0.0
        self._items_pending = []

    def _is_text_item(self, item) -> bool:
        if item is None:
            return False
        if "WriteTo" in item.__class__.__name__:
            return True
        if hasattr(item, 'model') and getattr(item.model, 'item_type', '') == 'write_to_image':
            return True
        return False

    def _is_stroke_item(self, item) -> bool:
        if item is None:
            return False
        return "AnimatedStrokeItem" in item.__class__.__name__


    def get_eased_progress(self, progress: float) -> float:
        if progress <= 1.0:
            return -(math.cos(math.pi * progress) - 1) / 2
        else:
            t = progress - 1.0
            return 1.0 + (-(math.cos(math.pi * t) - 1) / 2)

    def clear_queue(self):
        self.queue.clear()
        self.current_index = -1
        self.schedule = []
        
    def sync_queue(self, new_items, force_recompile=False):
        """Only clear and compile if the items actually changed, unless forced."""
        if not force_recompile and len(self.queue) == len(new_items):
            if all(a is b for a, b in zip(self.queue, new_items)):
                schedule_dirty = False
                for action in self.schedule:
                    if action.get('type') == 'draw' and action.get('item'):
                        it = action['item']
                        dur = getattr(it, 'anim_duration', getattr(it, '_anim_duration', 8.0))
                        if abs((action['end'] - action['start']) - dur) > 0.01:
                            schedule_dirty = True
                            break
                if not schedule_dirty:
                    return False # No change
        
        self.queue.clear()
        self.queue.extend(new_items)
        self.current_index = -1
        
        if not self.queue:
            self.hand_item.hide()
            if self.writing_hand_item:
                self.writing_hand_item.hide()
            self.schedule = []
        else:
            self.schedule = self.scheduler.compile(self.queue)
            
        return True

    def seek_only(self, time_sec: float):
        """Fast seek without clearing queue or recompiling unless needed."""
        self.timer.stop()
        self.seek(time_sec)

    def add_item(self, item: AnimatedStrokeItem):
        self.queue.append(item)

    def play(self):
        if not self.queue: return
        self._play_end_time = None
        self._pending_start_time = None
        self._pending_end_time = None
        
        # Trigger background plan building for items that support it (images, text)
        items_pending = []
        for item in self.queue:
            if hasattr(item, 'build_plan_async') and not getattr(item, '_plan_loaded', False):
                if hasattr(item, 'plan_ready'):
                    item.build_plan_async()
                    items_pending.append(item)
        
        if items_pending:
            # Wait for all plans to be ready, then play
            self._items_pending = list(items_pending)
            for item in items_pending:
                item.plan_ready.connect(self._on_image_plan_ready)
            return  # Don't start yet — _on_image_plan_ready will trigger _start_play
        
        self._start_play()

    def play_range(self, start_time: float, end_time: float):
        """Plays only a specific time slice (e.g. current scene) from start_time to end_time."""
        if not self.queue: return
        self._pending_start_time = max(0.0, float(start_time))
        self._pending_end_time = float(end_time)
        
        items_pending = []
        for item in self.queue:
            if hasattr(item, 'build_plan_async') and not getattr(item, '_plan_loaded', False):
                if hasattr(item, 'plan_ready'):
                    item.build_plan_async()
                    items_pending.append(item)
                    
        if items_pending:
            self._items_pending = list(items_pending)
            for item in items_pending:
                item.plan_ready.connect(self._on_image_plan_ready)
            return
            
        self._start_play_range(self._pending_start_time, self._pending_end_time)

    def _on_image_plan_ready(self, *args):
        """Called when an image's background plan finishes."""
        sender = self.sender()
        if sender in self._items_pending:
            try:
                sender.plan_ready.disconnect(self._on_image_plan_ready)
            except Exception:
                pass
            self._items_pending.remove(sender)
        if not self._items_pending:
            if getattr(self, '_pending_end_time', None) is not None:
                self._start_play_range(self._pending_start_time, self._pending_end_time)
            else:
                self._start_play()

    def _get_item_artboard_rect(self, item):
        from PySide6.QtCore import QRectF
        if item and item.scene():
            sc = item.scene()
            ws = sc.parent()
            if hasattr(ws, 'artboards') and ws.artboards:
                for ab in ws.artboards:
                    if ab.sceneBoundingRect().intersects(item.sceneBoundingRect()):
                        return ab.sceneBoundingRect()
                return ws.artboards[0].sceneBoundingRect()
            for it in sc.items():
                if type(it).__name__ == "SceneArtboardItem":
                    return it.sceneBoundingRect()
            return sc.sceneRect()
        return QRectF(0, 0, 1920, 1080)

    def _get_hand_size(self) -> float:
        try:
            return float(SettingsManager().get("hand_size", 2.0))
        except (ValueError, TypeError):
            return 2.0

    def _compute_drawing_hand_scale(self, current_item) -> float:
        try:
            hand_size = float(SettingsManager().get("hand_size", 2.0))
        except (ValueError, TypeError):
            hand_size = 2.0

        # Normalized base scale: default setting 2.0 maps to natural 1.0 in scene space (~500px wide)
        hand_base = hand_size / 2.0

        raw_scale = 1.0
        if current_item is not None:
            if hasattr(current_item, 'scale') and callable(current_item.scale):
                raw_scale = float(current_item.scale())
            elif hasattr(current_item, 'scale') and not callable(current_item.scale):
                raw_scale = float(current_item.scale)

        if current_item is not None and "SVGCanvasItem" in current_item.__class__.__name__:
            # Normalize scale to match a typical 1000px image's scale space
            raw_scale = (current_item.boundingRect().width() / 1000.0) * raw_scale

        # Balanced proportional factor bounded within [0.80, 1.25]
        # Prevents extreme hand shrinking on small images and extreme bloating on large images
        proportional_factor = max(0.80, min(1.25, raw_scale * 3.0)) if raw_scale > 0 else 1.0

        return hand_base * proportional_factor

    def _start_play(self):
        # Compile timeline into execution schedule
        self.schedule = self.scheduler.compile(self.queue)
        self._play_end_time = None
        
        # Reset all items
        for item in self.queue:
            if getattr(item, 'entrance_mode', 'draw') == 'motion':
                from core.motion_engine import MotionEngine
                MotionEngine.capture_target_transform(item)
                item.setOpacity(0.0)
            else:
                item.set_progress(0.0)
            
        self.current_index = 0
        self.total_time_passed = 0.0
        
        # Show appropriate hand based on first item
        first_item = self.queue[0] if self.queue else None
        if self._is_text_item(first_item) and self.writing_hand_item:
            self.hand_item.hide()
            if SettingsManager().get("writing_hand_style", "style_01") != "none":
                self.writing_hand_item.show()
        else:
            if self.writing_hand_item:
                self.writing_hand_item.hide()
            if SettingsManager().get("hand_style", "default") != "none":
                self.hand_item.show()
                
        self.playback_started.emit(True)
        self.timer.start(16) # ~60fps

    def _start_play_range(self, start_time: float, end_time: float):
        """Initializes and runs playback bounded strictly within [start_time, end_time]."""
        self._pending_start_time = None
        self._pending_end_time = None
        self._play_end_time = float(end_time)
        
        # Compile timeline into execution schedule
        self.schedule = self.scheduler.compile(self.queue)
        
        # Synchronize items and playhead state up to start_time
        self.total_time_passed = float(start_time)
        self.seek(self.total_time_passed)
        
        # Determine the first active action at start_time
        self.current_index = len(self.schedule)
        for idx, action in enumerate(self.schedule):
            if action['end'] > self.total_time_passed:
                self.current_index = idx
                break
                
        current_action = self.schedule[self.current_index] if (0 <= self.current_index < len(self.schedule)) else None
        active_item = current_action.get('item') if current_action else None
        
        # If scrubbing/starting inside a move-hand transit:
        if not active_item and current_action and current_action.get('type') == 'move-hand':
            to_item = current_action.get('to_item')
            from_item = current_action.get('from_item')
            is_text_transit = current_action.get('is_text_transition')
            if is_text_transit is None:
                is_text_transit = self._is_text_item(from_item) and self._is_text_item(to_item)
            if is_text_transit or self._is_text_item(to_item):
                # Between text frames, hand MUST be strictly hidden!
                self.hand_item.hide()
                if self.writing_hand_item:
                    self.writing_hand_item.hide()
                self.playback_started.emit(True)
                self.timer.start(16)
                return
            else:
                active_item = to_item

        if self._is_text_item(active_item) and self.writing_hand_item:
            self.hand_item.hide()
            if SettingsManager().get("writing_hand_style", "style_01") != "none":
                self.writing_hand_item.show()
        else:
            if self.writing_hand_item:
                self.writing_hand_item.hide()
            if SettingsManager().get("hand_style", "default") != "none":
                self.hand_item.show()
                
        self.playback_started.emit(True)
        self.timer.start(16)
        
    def stop(self):
        self.is_exporting = False
        self._play_end_time = None
        self._pending_start_time = None
        self._pending_end_time = None
        self.timer.stop()
        self.playback_started.emit(False)
        self.hand_item.hide()
        if hasattr(self, 'writing_hand_item') and self.writing_hand_item:
            self.writing_hand_item.hide()
        if hasattr(self.hand_item, 'set_drag_mode'):
            self.hand_item.set_drag_mode(False)
        self.hand_item.set_ink_active(False)
        self.current_index = -1
        
        self.sfx_engine.reset()
        if hasattr(self, '_played_motion_sfx_hints'):
            self._played_motion_sfx_hints.clear()
        self._last_sfx_action = None
        
        # [PHASE 1 FIX]: Restore all items to fully visible state using queue, NOT schedule
        if hasattr(self, 'queue') and self.queue:
            for current_item in self.queue:
                try:
                    if getattr(current_item, 'entrance_mode', 'draw') == 'motion':
                        from core.motion_engine import MotionEngine
                        MotionEngine.reset_item(current_item)
                    else:
                        is_image = "AnimatedImageItem" in current_item.__class__.__name__ or "SVGCanvasItem" in current_item.__class__.__name__ or "WriteToImageGraphicsItem" in current_item.__class__.__name__ or "MindMap" in current_item.__class__.__name__
                        max_progress = 1.0 if is_image else 2.0
                        current_item.set_progress(max_progress)
                except Exception:
                    pass
        
    def shutdown(self):
        """Safely stops timer and terminates underlying SFX worker thread."""
        try:
            self.stop()
            if hasattr(self, 'sfx_engine') and self.sfx_engine:
                self.sfx_engine.shutdown()
        except Exception:
            pass

    def _update_loop(self):
        try:
            self._step_internal(16)
        except Exception as e:
            # Bulletproof exception shield against infinite timer storms:
            # 1. Stop timer immediately so no subsequent ticks can re-enter
            self.timer.stop()
            # 2. Halt playback cleanly, hide hands, restore item states
            try:
                self.stop()
            except Exception:
                pass
            # 3. Log traceback safely
            import traceback
            traceback.print_exc()
            # 4. Emit clean error signal
            self.playback_error.emit(str(e))
        
    def reset_for_export(self):
        """Prepare engine for manual frame-by-frame stepping"""
        self.stop()
        self.is_exporting = True
        if not self.queue: return False
        
        self.schedule = self.scheduler.compile(self.queue)
        
        for item in self.queue:
            if getattr(item, 'entrance_mode', 'draw') == 'motion':
                from core.motion_engine import MotionEngine
                MotionEngine.capture_target_transform(item)
                item.setOpacity(0.0)
            else:
                item.set_progress(0.0)
            
        self.current_index = 0
        self.total_time_passed = 0.0
        if SettingsManager().get("hand_style", "default") != "none":
            self.hand_item.show()
        return True
        
    def step_manual(self, delta_ms=16):
        """Advance time by delta_ms and update state. Returns True if animation continues, False if finished."""
        return self._step_internal(delta_ms)
        
    def get_sfx_schedule(self):
        sfx_events = []
        if not self.schedule: return []
        import os
        
        sfx_dir = getattr(self.sfx_engine, 'sfx_dir', None)
        if not sfx_dir and hasattr(self.sfx_engine, '_worker'):
            sfx_dir = getattr(self.sfx_engine._worker, 'sfx_dir', None)
        if not sfx_dir:
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            sfx_dir = os.path.join(base_dir, 'assets', 'sfx', 'draw')

        for action in self.schedule:
            if action['type'] == 'draw':
                item = action['item']
                sfx_name = getattr(item, 'sfx_name', 'None')
                sfx_vol = getattr(item, 'sfx_volume', 100)
                if sfx_name != 'None' and sfx_dir:
                    sfx_path = os.path.join(sfx_dir, sfx_name)
                    if os.path.exists(sfx_path):
                        sfx_events.append({
                            'file_path': sfx_path,
                            'start_time': action['start'],
                            'duration': action['end'] - action['start'],
                            'volume': sfx_vol
                        })
        return sfx_events

    def seek(self, time_sec: float, show_hand_when_stopped: bool = False):
        if not self.queue:
            return
            
        if not self.schedule:
            self.schedule = self.scheduler.compile(self.queue)
            
        self.total_time_passed = time_sec
        self.progress_updated.emit(self.total_time_passed)
        
        self.current_index = len(self.schedule)
        self.hand_item.hide()
        self.sfx_engine.on_pen_up()
        
        for idx, action in enumerate(self.schedule):
            if action['type'] == 'draw':
                current_item = action['item']
                entrance_mode = getattr(current_item, 'entrance_mode', 'draw')
                if entrance_mode == 'motion':
                    from core.motion_engine import MotionEngine
                    MotionEngine.ensure_item_motion_cached(current_item)
                    if time_sec >= action['end']:
                        MotionEngine.reset_item(current_item)
                    elif time_sec <= action['start']:
                        current_item.setOpacity(0.0)
                else:
                    is_image = "AnimatedImageItem" in current_item.__class__.__name__ or "SVGCanvasItem" in current_item.__class__.__name__ or "WriteToImageGraphicsItem" in current_item.__class__.__name__ or "MindMap" in current_item.__class__.__name__
                    max_progress = 1.0 if is_image else 2.0
                    
                    if time_sec >= action['end']:
                        current_item.set_progress(max_progress)
                    elif time_sec <= action['start']:
                        current_item.set_progress(0.0)
                    
            if action['start'] <= time_sec < action['end']:
                self.current_index = idx
                
                action_duration = action['end'] - action['start']
                action_progress = (time_sec - action['start']) / action_duration if action_duration > 0 else 1.0
                
                if action['type'] == 'draw':
                    current_item = action['item']
                    entrance_mode = getattr(current_item, 'entrance_mode', 'draw')
                    if entrance_mode == 'motion':
                        if self.writing_hand_item:
                            self.writing_hand_item.hide()
                        from core.motion_engine import MotionEngine
                        artboard_rect = self._get_item_artboard_rect(current_item)
                        hand_to_pass = self.hand_item if SettingsManager().get("hand_style", "default") != "none" else None
                        MotionEngine.apply_motion_frame(
                            item=current_item,
                            hand_item=hand_to_pass,
                            time_sec=time_sec,
                            start_time=action['start'],
                            action_duration=action_duration,
                            artboard_rect=artboard_rect,
                            hand_size_setting=self._get_hand_size()
                        )
                    else:
                        is_text = self._is_text_item(current_item)
                        is_image = "AnimatedImageItem" in current_item.__class__.__name__ or "SVGCanvasItem" in current_item.__class__.__name__ or is_text or "MindMap" in current_item.__class__.__name__
                        max_progress = 1.0 if is_image else 2.0
                        
                        item_progress = action_progress * max_progress
                        eased_progress = item_progress if is_image else self.get_eased_progress(item_progress)
                        current_item.set_progress(eased_progress)
                        
                        if is_text and self.writing_hand_item:
                            self.hand_item.hide()
                            if eased_progress <= 1.0:
                                item_style = getattr(getattr(current_item, 'model', None), 'writing_hand_style', None) or SettingsManager().get("writing_hand_style", "default")
                                if item_style != "none":
                                    local_tip = current_item.get_tip_position()
                                    scene_tip = current_item.mapToScene(local_tip)
                                    self.writing_hand_item.update_position(scene_tip, item=current_item, is_writing=True)
                                else:
                                    self.writing_hand_item.hide()
                            else:
                                self.writing_hand_item.hide()
                        else:
                            if self.writing_hand_item:
                                self.writing_hand_item.hide()
                                
                            # Fix: Always default to right hand for all drawing (user preference)
                            # This prevents the left hand from showing unexpectedly on RTL objects
                            if hasattr(self.hand_item, 'set_drag_mode'):
                                self.hand_item.set_drag_mode(False)
                            self.hand_item.set_hand_type("right")
                            
                            if eased_progress <= 1.0:
                                # Only show if user hasn't chosen 'none'
                                if SettingsManager().get("hand_style", "default") != "none":
                                    self.hand_item.show()
                                
                                # Scale hand based on item and global hand_size setting
                                hand_scale = self._compute_drawing_hand_scale(current_item)
                                self.hand_item.setScale(hand_scale)
                                
                                local_tip = current_item.get_tip_position()
                                scene_tip = current_item.mapToScene(local_tip)
                                self.hand_item.setPos(scene_tip)
                        
                elif action['type'] == 'move-hand':
                    from_item = action.get('from_item')
                    to_item = action.get('to_item')
                    # Hand only moves across screen for pure stroke-to-stroke drawing.
                    # Between images, drawings, or text, hand hides completely during transit to prevent shrinking artifacts.
                    if self._is_stroke_item(from_item) and self._is_stroke_item(to_item):
                        if self.writing_hand_item:
                            self.writing_hand_item.hide()
                        if SettingsManager().get("hand_style", "default") != "none":
                            self.hand_item.show()
                        self.hand_item.set_ink_active(False)
                        eased = self.get_eased_progress(action_progress)
                        from_pos = action['from_pos']
                        to_pos = action['to_pos']
                        curr_x = from_pos.x() + (to_pos.x() - from_pos.x()) * eased
                        curr_y = from_pos.y() + (to_pos.y() - from_pos.y()) * eased
                        self.hand_item.setPos(QPointF(curr_x, curr_y))
                    else:
                        self.hand_item.hide()
                        if hasattr(self.hand_item, 'set_ink_active'):
                            self.hand_item.set_ink_active(False)
                        if self.writing_hand_item:
                            self.writing_hand_item.hide()
                elif action['type'] == 'delay':
                    self.hand_item.hide()
                    if self.writing_hand_item:
                        self.writing_hand_item.hide()
            elif time_sec < action['start'] and idx < self.current_index:
                self.current_index = idx
                
        # Force hide hand if scrubbing while stopped (video preview illusion)
        if not self.timer.isActive() and not show_hand_when_stopped:
            self.hand_item.hide()
            if self.writing_hand_item:
                self.writing_hand_item.hide()
            self.sfx_engine.on_pen_up()
                
    def _step_internal(self, delta_ms):
        if self._play_end_time is not None and self.total_time_passed >= self._play_end_time:
            self.stop()
            self.finished.emit()
            return False

        if self.current_index < 0 or self.current_index >= len(self.schedule):
            self.stop()
            self.finished.emit()
            return False
            
        action = self.schedule[self.current_index]
        if getattr(self, '_last_sfx_action', None) is not action:
            self._last_sfx_action = action
            if not hasattr(self, '_played_motion_sfx_hints'):
                self._played_motion_sfx_hints = set()
            else:
                self._played_motion_sfx_hints.clear()

        delta_sec = delta_ms / 1000.0
        self.total_time_passed += delta_sec
        self.progress_updated.emit(self.total_time_passed)
        
        if self.total_time_passed < action['start']:
            return True # Waiting for start time
            
        action_duration = action['end'] - action['start']
        
        if action_duration <= 0:
            action_progress = 1.0
        else:
            action_progress = (self.total_time_passed - action['start']) / action_duration
            
        if action_progress > 1.0:
            action_progress = 1.0
            
        if action['type'] == 'draw':
            current_item = action['item']
            entrance_mode = getattr(current_item, 'entrance_mode', 'draw')
            if entrance_mode == 'motion':
                from core.motion_engine import MotionEngine
                artboard_rect = self._get_item_artboard_rect(current_item)
                hand_to_pass = self.hand_item if SettingsManager().get("hand_style", "default") != "none" else None
                sol = MotionEngine.apply_motion_frame(
                    item=current_item,
                    hand_item=hand_to_pass,
                    time_sec=self.total_time_passed,
                    start_time=action['start'],
                    action_duration=action_duration,
                    artboard_rect=artboard_rect,
                    hand_size_setting=self._get_hand_size()
                )
                if not getattr(self, 'is_exporting', False) and sol:
                    sfx_hint = sol.get("sfx_hint")
                    m_settings = getattr(current_item, 'motion_settings', {}) or {}
                    chosen_sfx = m_settings.get("sfx", "none")
                    if chosen_sfx and chosen_sfx.lower() not in ("none", "silent") and sfx_hint:
                        if sfx_hint not in getattr(self, '_played_motion_sfx_hints', set()):
                            self._played_motion_sfx_hints.add(sfx_hint)
                            sound_to_play = None
                            if sfx_hint == "whoosh" and chosen_sfx == "whoosh":
                                sound_to_play = "whoosh"
                            elif sfx_hint == "impact":
                                sound_to_play = chosen_sfx
                            if sound_to_play:
                                sfx_vol = float(getattr(current_item, 'sfx_volume', 100))
                                self.sfx_engine.play_motion_sfx(sound_to_play, sfx_vol)
            else:
                is_text = self._is_text_item(current_item)
                is_image = "AnimatedImageItem" in current_item.__class__.__name__ or "SVGCanvasItem" in current_item.__class__.__name__ or is_text
                max_progress = 1.0 if is_image else 2.0
                
                item_progress = action_progress * max_progress
                eased_progress = item_progress if is_image else self.get_eased_progress(item_progress)
                current_item.set_progress(eased_progress)
                
                if is_text and self.writing_hand_item:
                    self.hand_item.hide()
                    self.hand_item.set_ink_active(False)
                    
                    if 0.01 <= action_progress <= 1.0 and eased_progress <= 1.0:
                        if not getattr(self, 'is_exporting', False):
                            sfx_name = getattr(current_item, 'sfx_name', 'None')
                            sfx_vol = getattr(current_item, 'sfx_volume', 100)
                            self.sfx_engine.on_pen_down(sfx_name, sfx_vol)
                            
                        item_style = getattr(getattr(current_item, 'model', None), 'writing_hand_style', None) or SettingsManager().get("writing_hand_style", "default")
                        if item_style != "none":
                            local_tip = current_item.get_tip_position()
                            scene_tip = current_item.mapToScene(local_tip)
                            self.writing_hand_item.update_position(scene_tip, item=current_item, is_writing=True)
                        else:
                            self.writing_hand_item.hide()
                    else:
                        self.sfx_engine.on_pen_up()
                        self.writing_hand_item.hide()
                else:
                    if self.writing_hand_item:
                        self.writing_hand_item.hide()
                        
                    if hasattr(self.hand_item, 'set_drag_mode'):
                        self.hand_item.set_drag_mode(False)
                    
                    ink_color = Qt.GlobalColor.black
                    if hasattr(current_item, 'base_pen'):
                        ink_color = current_item.base_pen.color()
                    elif hasattr(current_item, '_color'):
                        ink_color = current_item._color
                    elif hasattr(current_item, 'pen') and callable(current_item.pen):
                        ink_color = current_item.pen().color()
                    self.hand_item.set_ink_color(ink_color)
                    
                    if 0.01 <= action_progress <= 1.0 and eased_progress <= 1.0:
                        if not getattr(self, 'is_exporting', False):
                            sfx_name = getattr(current_item, 'sfx_name', 'None')
                            sfx_vol = getattr(current_item, 'sfx_volume', 100)
                            self.sfx_engine.on_pen_down(sfx_name, sfx_vol)
                        
                        if not self.hand_item.isVisible():
                            # Only show hand if user hasn't chosen 'none'
                            if SettingsManager().get("hand_style", "default") != "none":
                                self.hand_item.show()

                        hand_scale = self._compute_drawing_hand_scale(current_item)
                        self.hand_item.setScale(hand_scale)
                        
                        local_tip = current_item.get_tip_position()
                        scene_tip = current_item.mapToScene(local_tip)
                        self.hand_item.setPos(scene_tip)
                        
                        # Active ink dot while actively drawing before final lift
                        if action_progress < 0.99:
                            self.hand_item.set_ink_active(True)
                        else:
                            self.hand_item.set_ink_active(False)
                            self.sfx_engine.on_pen_up()
                    else:
                        self.sfx_engine.on_pen_up()
                        if self.hand_item.isVisible():
                            self.hand_item.hide()
                        self.hand_item.set_ink_active(False)
                            
        elif action['type'] == 'move-hand':
            self.sfx_engine.on_pen_up()
            from_item = action.get('from_item')
            to_item = action.get('to_item')
            # Hand only moves across screen for pure stroke-to-stroke drawing.
            # Between images, drawings, or text, hand hides completely during transit to prevent shrinking artifacts.
            if self._is_stroke_item(from_item) and self._is_stroke_item(to_item):
                if self.writing_hand_item:
                    self.writing_hand_item.hide()
                self.hand_item.set_ink_active(False)
                if not self.hand_item.isVisible() and SettingsManager().get("hand_style", "default") != "none":
                    self.hand_item.show()
                from_pos = action['from_pos']
                to_pos = action['to_pos']
                eased = self.get_eased_progress(action_progress)
                curr_x = from_pos.x() + (to_pos.x() - from_pos.x()) * eased
                curr_y = from_pos.y() + (to_pos.y() - from_pos.y()) * eased
                self.hand_item.setPos(QPointF(curr_x, curr_y))
            else:
                self.hand_item.hide()
                self.hand_item.set_ink_active(False)
                if self.writing_hand_item:
                    self.writing_hand_item.hide()
            
        elif action['type'] == 'delay':
            self.sfx_engine.on_pen_up()
            self.hand_item.hide()
            if self.writing_hand_item:
                self.writing_hand_item.hide()
            self.hand_item.set_ink_active(False)
            
        if action_progress >= 1.0:
            if action['type'] == 'draw':
                self.sfx_engine.on_pen_up()
                self.hand_item.set_ink_active(False)
                if getattr(action['item'], 'entrance_mode', 'draw') == 'motion':
                    from core.motion_engine import MotionEngine
                    MotionEngine.reset_item(action['item'])
                    self.hand_item.hide()
                if self._is_text_item(action['item']) and self.writing_hand_item:
                    self.writing_hand_item.hide()
            elif action['type'] == 'move-hand':
                self.hand_item.hide()
                self.hand_item.set_ink_active(False)
                if self.writing_hand_item:
                    self.writing_hand_item.hide()
            self.current_index += 1
            
        return True
