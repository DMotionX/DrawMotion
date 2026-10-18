# DrawMotion - Core Architectural Principles & System Design

This document details the fundamental engineering patterns and non-negotiable architectural invariants of the DrawMotion codebase.

---

## 1. Single Source of Truth (SSOT) Workspace Pattern

* **Principle:** The UI layer (including `TimelinePanel`, `InspectorPanel`, and `LeftPanel`) must never maintain an independent canonical state of project assets or timeline sequencing.
* **Architecture:** 
  - `Workspace` (wrapping `QGraphicsScene`) holds all `SceneArtboardItem`s, which in turn contain `LayerItem`s.
  - The `Workspace` emits the `items_changed` signal upon any user mutation (addition, deletion, reordering, duration adjustment).
  - The `TimelinePanel` subscribes reactively to `items_changed`, clears its temporary rendering blocks, and reconstructs its display dynamically via `_recalculate_scene_times()`.
* **Benefit:** Eliminates ghost blocks, timeline-scene desynchronization, and corrupted video export timelines.

---

## 2. Data-First Object Serialization (Zero-Memory-Leak Pattern)

* **Principle:** Never use `copy.deepcopy()` or direct C++ pointer cloning on `QGraphicsItem` subclasses.
* **Architecture:** 
  - `QGraphicsItem` hierarchies contain complex native Qt C++ signal-slot linkages and scene bindings. Cloning them directly in Python causes reference conflicts, double-free crashes, and segmentation faults.
  - In `core/clipboard/clipboard_manager.py`, items implement `to_dict()` to produce a pure JSON-serializable dictionary representation.
  - Cloning and pasting calls `from_dict()` on a fresh instance, assigning a new `uuid4()` identifier and attaching isolated signals with a visual offset.
* **Benefit:** 100% leak-free, stateless copy/paste/duplicate functionality across scenes.

---

## 3. Dual-Layer Text & Mask Rendering Pipeline

* **Principle:** Never apply heavy graphical effects (`QGraphicsDropShadowEffect`, glow filters, blur) directly to an actively animating vector path undergoing stroke truncation or `dashOffset` manipulation.
* **Architecture:**
  - Dynamic path modification disrupts Qt's sub-pixel anti-aliasing engine and causes severe pixelation (staircasing).
  - The `WriteToAnimatedImageItem` engine decouples animation calculation from raster output:
    1. **Display Layer:** A static, high-resolution pre-rendered text surface containing full typography anti-aliasing, color gradients, and graphical effects.
    2. **Base Layer (Mask):** An animating stroke path driven by physics algorithms.
    3. The Base Layer acts as a mask over the Display Layer using `QPainter.CompositionMode_DestinationIn`.
* **Benefit:** Crisp, studio-grade anti-aliased text rendering with zero pixelation or stutter during real-time animation.

---

## 4. Signal Trapping and Circuit Breaker Boot Resilience

* **Principle:** Desktop applications must survive underlying platform inconsistencies and capture fatal errors before hard aborts.
* **Architecture:**
  - `qInstallMessageHandler` is registered before `QApplication` instantiation to capture C++ level `qFatal` and `qCritical` logs into persistent storage (`qt_messages.log`).
  - `faulthandler` maintains an unbuffered crash log hook (`crash_faulthandler.log`).
  - A circuit breaker watchdog (`watchdog.py`) limits consecutive startup failures (`max_allowed_failures = 3`) to prevent infinite crash loops.
