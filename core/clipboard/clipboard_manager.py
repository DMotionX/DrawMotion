import copy
import uuid
from PySide6.QtCore import QObject, Signal

class ClipboardManager(QObject):
    clipboard_changed = Signal()
    
    def __init__(self, workspace):
        super().__init__()
        self.workspace = workspace
        self.clipboard_data = None
        self.clipboard_type = None

    def has_content(self):
        return self.clipboard_data is not None
        
    def copy(self, item):
        if not item: return
        
        if hasattr(item, 'to_dict'):
            self.clipboard_data = item.to_dict()
            self.clipboard_type = item.__class__.__name__
            self.clipboard_changed.emit()
            
    def cut(self, item):
        if not item: return
        self.copy(item)
        
        from core.commands import RemoveItemCommand
        cmd = RemoveItemCommand(self.workspace.scene, item, self.workspace.user_items, f"Cut {self.clipboard_type}")
        self.workspace.undo_stack.push(cmd)
        
        self.workspace.distribute_global_time(respect_board_duration=False)
        self.workspace.items_changed.emit(self.workspace.get_current_scene_items())

    def duplicate(self, item, target_board=None):
        if not item: return
        self.copy(item)
        self.paste(target_board)
        
    def paste(self, target_board=None):
        if not self.has_content(): return
        
        if target_board is None:
            if not self.workspace.artboards: return
            target_board = self.workspace.artboards[self.workspace.current_scene_index]
            
        data = copy.deepcopy(self.clipboard_data)
        
        # New unique ID
        import time
        new_id = f"item_{int(time.time()*1000)}_{uuid.uuid4().hex[:8]}"
        data['id'] = new_id
        
        # Offset slightly
        if 'transform' in data:
            data['transform']['x'] += 20
            data['transform']['y'] += 20
        elif 'pos_x' in data:
            data['pos_x'] += 20
            data['pos_y'] += 20
            
        # Reconstruct based on type
        item_type = self.clipboard_type
        item = None
        
        try:
            if item_type == "AnimatedImageItem":
                from graphics.animated_image_item import AnimatedImageItem
                item = AnimatedImageItem.from_dict(data)
            elif item_type == "EditableTextNode":
                self.logger.warning("EditableTextNode was deprecated and removed. Skipping clipboard paste.")
            elif item_type == "AnimatedStrokeItem":
                from graphics.animated_stroke_item import AnimatedStrokeItem
                item = AnimatedStrokeItem.from_dict(data)
            elif item_type == "SVGCanvasItem":
                from asset_library.engine.svg_canvas_item import SVGCanvasItem
                item = SVGCanvasItem.from_dict(data)
            elif item_type in ("WriteToImageGraphicsItem", "WriteToAnimatedImageItem"):
                from components.write_to_image.graphics_item import WriteToImageGraphicsItem
                item = WriteToImageGraphicsItem.from_dict(data)
                item.canvas_workspace = self.workspace
            elif item_type == "MindMapNodeItem":
                from components.mind_map_builder.models import MindMapNodeModel
                from components.mind_map_builder.node_item import MindMapNodeItem
                flat_data = {k: v for k, v in data.items() if k not in ['transform', 'appearance', 'timing', 'type']}
                if 'transform' in data:
                    flat_data['pos_x'] = data['transform'].get('x', 0)
                    flat_data['pos_y'] = data['transform'].get('y', 0)
                    flat_data['scale_w'] = data['transform'].get('scale_w', 1.0)
                    flat_data['scale_h'] = data['transform'].get('scale_h', 1.0)
                    flat_data['rotation'] = data['transform'].get('rotation', 0.0)
                model = MindMapNodeModel(**flat_data)
                item = MindMapNodeItem(model, self.workspace)
        except Exception as e:
            print(f"Error during paste deserialization: {e}")
            return
            
        if not item: return
        
        # Apply auto placement
        item.anim_delay = self.workspace._calculate_auto_placement_delay(target_board)
        item.setParentItem(target_board)
        
        from core.commands import AddItemCommand
        cmd = AddItemCommand(self.workspace.scene, item, self.workspace.user_items, f"Paste {item_type}")
        self.workspace.undo_stack.push(cmd)
        
        self.workspace.distribute_global_time(respect_board_duration=False)
        self.workspace.items_changed.emit(self.workspace.get_current_scene_items())
        
        self.workspace.scene.clearSelection()
        item.setSelected(True)
