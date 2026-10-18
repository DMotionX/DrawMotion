# Workspace and Timeline Synchronization

## Concept
The timeline in DrawMotion (`TimelinePanel`) and the actual visual canvas (`Workspace`) must remain perfectly synchronized. The Workspace acts as the Single Source of Truth (SSOT). The Timeline is purely a reactive view of the Workspace data.

## Mechanism

### 1. The Artboard State
The Workspace maintains a list of `SceneArtboardItem` objects. Each artboard contains an ordered list of its child graphical items (text, images, shapes). This structural hierarchy is what defines the temporal sequence.

### 2. Signal Propagation
Whenever a change occurs in the Workspace (e.g., adding an item, deleting an item, changing an item's duration via the Inspector), the Workspace emits a specific signal, usually `items_changed`.

### 3. Reactive Rebuilding
The Timeline panel connects to the `items_changed` signal. When triggered, the Timeline does not attempt to selectively update UI elements. Instead, it fully rebuilds its UI mapping based on the current state of the Workspace.

1.  It iterates through all `artboards` in the Workspace.
2.  For each artboard, it creates a `SceneBlock` in the UI.
3.  For each child item in the artboard, it creates a `LayerBlock` (for scenes) or `TransitionBlock` (for element timing).

## Auto-Sequential Placement

To simplify the user experience, the system enforces sequential placement of items by default (unless manually overridden).

**Algorithm:**
When a new item is added to an artboard:
1.  The system queries the current artboard for the sum of all durations of existing items.
2.  Let this sum be `T_total`.
3.  The new item's internal start time (delay) is set to `T_total`.
4.  The new item's duration is set to a default (e.g., based on text length or a 3.0s image default).
5.  The artboard's total duration is expanded to accommodate the new item.
6.  The timeline is rebuilt, perfectly placing the new item immediately after the previous one finishes drawing.

## Mathematical Formula for Sequence
For an ordered set of items `I_0, I_1, ..., I_n` in a scene:

*   `Delay(I_k) = Sum(Duration(I_j)) for j = 0 to k-1`
*   `Scene_Duration = Sum(Duration(I_k)) for all k in scene`

By adhering to this model, we guarantee that no two elements write simultaneously unless explicitly commanded by the user, mimicking a real human drawing process on a whiteboard.
