from PySide6.QtGui import QUndoCommand

class AddItemCommand(QUndoCommand):
    def __init__(self, scene, item, user_items_list, description="Add Item"):
        super().__init__(description)
        self.scene = scene
        self.item = item
        self.user_items_list = user_items_list
        self.parent_item = item.parentItem()
        # Save the original duration of the artboard before adding the item
        self.prev_duration = getattr(self.parent_item, 'duration', 2.0) if self.parent_item else 2.0

    def redo(self):
        # Adding to the actual UI scene happens when we set parent to artboard
        # But we need to ensure it's in the user_items list
        if self.item not in self.user_items_list:
            self.user_items_list.append(self.item)
        if not self.item.scene():
            # if parent is artboard, it's already in the scene implicitly, but just to be safe
            self.scene.addItem(self.item)
        if self.parent_item and self.item.parentItem() != self.parent_item:
            self.item.setParentItem(self.parent_item)

    def undo(self):
        if self.item in self.user_items_list:
            self.user_items_list.remove(self.item)
        if self.item.scene() == self.scene:
            self.scene.removeItem(self.item)
        # Restore the original duration of the artboard
        if self.parent_item and hasattr(self.parent_item, 'duration'):
            self.parent_item.duration = self.prev_duration

class RemoveItemCommand(QUndoCommand):
    def __init__(self, scene, item, user_items_list, description="Remove Item"):
        super().__init__(description)
        self.scene = scene
        self.item = item
        self.user_items_list = user_items_list
        self.parent_item = item.parentItem()
        # Save the original duration of the artboard before removing the item
        self.prev_duration = getattr(self.parent_item, 'duration', 2.0) if self.parent_item else 2.0

    def redo(self):
        if self.item in self.user_items_list:
            self.user_items_list.remove(self.item)
        if self.item.scene() == self.scene:
            self.scene.removeItem(self.item)
        # Restore the original duration of the artboard if we are redoing a remove (meaning it might have shrunk)
        # Actually, for redo of remove, it's best to let distribute_global_time handle it later, 
        # but we can optionally restore the duration it had right after removal if we tracked it.
        # For simplicity, we just leave redo as is, since distribute_global_time usually recalculates on remove.

    def undo(self):
        if self.item not in self.user_items_list:
            self.user_items_list.append(self.item)
        if not self.item.scene():
            self.scene.addItem(self.item)
        if self.parent_item and self.item.parentItem() != self.parent_item:
            self.item.setParentItem(self.parent_item)
        # Restore the original duration of the artboard when the item is brought back
        if self.parent_item and hasattr(self.parent_item, 'duration'):
            self.parent_item.duration = self.prev_duration
