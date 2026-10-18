from PySide6.QtCore import Qt

class TextController:
    """
    Controller Layer: Manages the State Machine and Interaction Logic.
    States: idle -> selected -> editing -> committed
    """
    def __init__(self):
        self.current_state = "idle"
        
    def on_mouse_press(self, node, event):
        """Handle single clicks (selection)"""
        if self.current_state == "idle":
            self.set_state(node, "selected")
            
        elif self.current_state == "selected":
            # Pass through for dragging handles or moving
            pass
            
    def on_double_click(self, node, event):
        """Handle double clicks (enter edit mode)"""
        if self.current_state in ["idle", "selected"]:
            self.set_state(node, "editing")
            
    def on_focus_out(self, node, event):
        """When user clicks away from the text box"""
        if self.current_state == "editing":
            self.commit(node)
        else:
            self.set_state(node, "idle")
            
    def on_text_changed(self, node):
        """Fired when keyboard input changes the text"""
        if self.current_state == "editing":
            new_text = node.toPlainText()
            node.model.update_text(new_text)
            # DO NOT call sync_from_model() here! It causes massive lag during typing
            # because it recalculates QTextLayout and fonts on every keystroke.
            
    def set_state(self, node, state: str):
        if self.current_state == state:
            return
            
        self.current_state = state
        
        if state == "idle":
            node.setTextInteractionFlags(Qt.TextInteractionFlag.NoTextInteraction)
            node.clearFocus()
            
        elif state == "selected":
            node.setTextInteractionFlags(Qt.TextInteractionFlag.NoTextInteraction)
            
        elif state == "editing":
            node.setTextInteractionFlags(Qt.TextInteractionFlag.TextEditorInteraction)
            node.setFocus()
            
        node.update() # Trigger repaint for bounding box changes
        
    def commit(self, node):
        """Finalize editing"""
        self.on_text_changed(node)
        
        # Now that typing is done, perform the heavy layout sync once
        node.sync_from_model()
        node.build_plan_async()
        
        # If text is completely empty after edit, we might want to delete the node.
        # This can be signaled to the workspace manager.
        if not node.model.text.strip():
            self.set_state(node, "idle")
            # EditableTextNode's focusOutEvent will emit empty_text_unfocused
            return
            
        self.set_state(node, "selected")
        
        # Update timeline
        if hasattr(self, 'workspace') and self.workspace:
            self.workspace.items_changed.emit(self.workspace.get_current_scene_items())
