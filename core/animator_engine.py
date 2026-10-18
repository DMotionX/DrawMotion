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
    progress_updated = Signal(float) # Emits current time in seconds
    
    def __init__(self, hand_item: HandItem, parent=None):
        super().__init__(parent)
        self.hand_item = hand_item
        self.queue = []
        self.scheduler = SmartScheduler(hand_speed=500)
        self.schedule = []
        self.current_index = -1
        
        self.sfx_engine = SFXSyncEngine(self)
        
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._update_loop)
        
        self.total_time_passed = 0.0
        self._items_pending = []

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
            self._start_play()

    def _start_play(self):
        # Compile timeline into execution schedule
        self.schedule = self.scheduler.compile(self.queue)
        
        # Reset all items
        for item in self.queue:
            item.set_progress(0.0)
            
        self.current_index = 0
        self.total_time_passed = 0.0
        # Only show hand if the user hasn't chosen 'none'
        if SettingsManager().get("hand_style", "default") != "none":
            self.hand_item.show()
        self.timer.start(16) # ~60fps
        
    def stop(self):
        self.is_exporting = False
        self.timer.stop()
        self.hand_item.hide()
        self.hand_item.set_ink_active(False)
        self.current_index = -1
        
        self.sfx_engine.reset()
        
        # [PHASE 1 FIX]: Restore all items to fully visible state using queue, NOT schedule
        if hasattr(self, 'queue') and self.queue:
            for current_item in self.queue:
                is_image = "AnimatedImageItem" in current_item.__class__.__name__ or "SVGCanvasItem" in current_item.__class__.__name__ or "WriteToImageGraphicsItem" in current_item.__class__.__name__ or "MindMap" in current_item.__class__.__name__
                max_progress = 1.0 if is_image else 2.0
                current_item.set_progress(max_progress)
        
    def _update_loop(self):
        self._step_internal(16)
        
    def reset_for_export(self):
        """Prepare engine for manual frame-by-frame stepping"""
        self.stop()
        self.is_exporting = True
        if not self.queue: return False
        
        self.schedule = self.scheduler.compile(self.queue)
        
        for item in self.queue:
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

    def seek(self, time_sec: float):
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
                    is_image = "AnimatedImageItem" in current_item.__class__.__name__ or "SVGCanvasItem" in current_item.__class__.__name__ or "WriteToImageGraphicsItem" in current_item.__class__.__name__ or "MindMap" in current_item.__class__.__name__
                    max_progress = 1.0 if is_image else 2.0
                    
                    # Fix: Always default to right hand for all drawing (user preference)
                    # This prevents the left hand from showing unexpectedly on RTL objects
                    self.hand_item.set_hand_type("right")
                    
                    item_progress = action_progress * max_progress
                    eased_progress = item_progress if is_image else self.get_eased_progress(item_progress)
                    current_item.set_progress(eased_progress)
                    
                    if eased_progress <= 1.0:
                        # Only show if user hasn't chosen 'none'
                        if SettingsManager().get("hand_style", "default") != "none":
                            self.hand_item.show()
                        
                        # Scale hand based on item and global hand_size setting
                        item_scale = current_item.scale()
                        if "SVGCanvasItem" in current_item.__class__.__name__:
                            # Normalize scale to match a typical 1000px image's scale space
                            item_scale = (current_item.boundingRect().width() / 1000.0) * item_scale
                        elif hasattr(current_item, 'model') and getattr(current_item.model, 'item_type', '') == 'write_to_image':
                            # Smart scale based on text height so larger fonts get a slightly larger hand
                            # and it correctly respects the global hand_size setting
                            item_scale = (current_item.boundingRect().height() / 250.0) * item_scale
                            
                        try:
                            hand_size = float(SettingsManager().get("hand_size", 3.0))
                        except (ValueError, TypeError):
                            hand_size = 3.0
                            
                        self.hand_item.setScale(hand_size * item_scale)
                        
                        local_tip = current_item.get_tip_position()
                        scene_tip = current_item.mapToScene(local_tip)
                        self.hand_item.setPos(scene_tip)
                        
                elif action['type'] == 'move-hand':
                    self.hand_item.show()
                    eased = self.get_eased_progress(action_progress)
                    from_pos = action['from_pos']
                    to_pos = action['to_pos']
                    curr_x = from_pos.x() + (to_pos.x() - from_pos.x()) * eased
                    curr_y = from_pos.y() + (to_pos.y() - from_pos.y()) * eased
                    self.hand_item.setPos(QPointF(curr_x, curr_y))
                elif action['type'] == 'delay':
                    self.hand_item.hide()
            elif time_sec < action['start'] and idx < self.current_index:
                self.current_index = idx
                
        # Force hide hand if scrubbing while stopped (video preview illusion)
        if not self.timer.isActive():
            self.hand_item.hide()
            self.sfx_engine.on_pen_up()
                
    def _step_internal(self, delta_ms):
        if self.current_index < 0 or self.current_index >= len(self.schedule):
            self.stop()
            self.finished.emit()
            return False
            
        action = self.schedule[self.current_index]
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
            is_image = "AnimatedImageItem" in current_item.__class__.__name__ or "SVGCanvasItem" in current_item.__class__.__name__
            max_progress = 1.0 if is_image else 2.0
            
            ink_color = Qt.GlobalColor.black
            if hasattr(current_item, 'base_pen'):
                ink_color = current_item.base_pen.color()
            elif hasattr(current_item, '_color'):
                ink_color = current_item._color
            elif hasattr(current_item, 'pen') and callable(current_item.pen):
                ink_color = current_item.pen().color()
            self.hand_item.set_ink_color(ink_color)
            
            item_progress = action_progress * max_progress
            eased_progress = item_progress if is_image else self.get_eased_progress(item_progress)
            current_item.set_progress(eased_progress)
            
            if 0.01 <= action_progress <= 1.0 and eased_progress <= 1.0:
                if not getattr(self, 'is_exporting', False):
                    sfx_name = getattr(current_item, 'sfx_name', 'None')
                    sfx_vol = getattr(current_item, 'sfx_volume', 100)
                    self.sfx_engine.on_pen_down(sfx_name, sfx_vol)
                
                if not self.hand_item.isVisible():
                    # Only show hand if user hasn't chosen 'none'
                    if SettingsManager().get("hand_style", "default") != "none":
                        self.hand_item.show()
                    
                    # Snap immediately on first show and set proper scale
                    item_scale = current_item.scale()
                    if "SVGCanvasItem" in current_item.__class__.__name__:
                        item_scale = (current_item.boundingRect().width() / 1000.0) * item_scale
                    elif hasattr(current_item, 'model') and getattr(current_item.model, 'item_type', '') == 'write_to_image':
                        item_scale = (current_item.boundingRect().height() / 250.0) * item_scale
                        
                    try:
                        hand_size = float(SettingsManager().get("hand_size", 3.0))
                    except (ValueError, TypeError):
                        hand_size = 3.0
                    self.hand_item.setScale(hand_size * item_scale)
                    
                    local_tip = current_item.get_tip_position()
                    scene_tip = current_item.mapToScene(local_tip)
                    self.hand_item.setPos(scene_tip)
                else:
                    item_scale = current_item.scale()
                    if "SVGCanvasItem" in current_item.__class__.__name__:
                        item_scale = (current_item.boundingRect().width() / 1000.0) * item_scale
                    elif hasattr(current_item, 'model') and getattr(current_item.model, 'item_type', '') == 'write_to_image':
                        item_scale = (current_item.boundingRect().height() / 250.0) * item_scale
                        
                    try:
                        hand_size = float(SettingsManager().get("hand_size", 3.0))
                    except (ValueError, TypeError):
                        hand_size = 3.0
                    self.hand_item.setScale(hand_size * item_scale)
                    
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
            self.hand_item.set_ink_active(False)
            if not self.hand_item.isVisible():
                self.hand_item.show()

            from_pos = action['from_pos']
            to_pos = action['to_pos']
            
            eased = self.get_eased_progress(action_progress)
            curr_x = from_pos.x() + (to_pos.x() - from_pos.x()) * eased
            curr_y = from_pos.y() + (to_pos.y() - from_pos.y()) * eased
            self.hand_item.setPos(QPointF(curr_x, curr_y))
            
        elif action['type'] == 'delay':
            self.sfx_engine.on_pen_up()
            self.hand_item.hide()
            self.hand_item.set_ink_active(False)
            
        if action_progress >= 1.0:
            if action['type'] == 'draw':
                self.sfx_engine.on_pen_up()
                self.hand_item.set_ink_active(False)
            self.current_index += 1
            
        return True
