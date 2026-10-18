# DrawMotion Development Roadmap

This document outlines realistic engineering milestones and high-priority features planned for upcoming versions of DrawMotion.

---

## 1. Timeline and Editing Enhancements

* **Magnetic Timeline Snapping:** Add snapping thresholds when dragging transition blocks and audio elements, eliminating inadvertent micro-gaps between scenes.
* **Scene Grouping:** Allow users to group related artboard items and manage their collective timeline duration as a unified compound block.
* **History Navigation:** Implement a visual undo and redo history panel allowing jump-to-state operations without repetitive shortcut keystrokes.

---

## 2. Audio and Video Workflow

* **Audio-Visual Duration Alignment:** Intelligent helper tools to suggest and adjust artboard durations to match imported audio track lengths.
* **Waveform Visualization Refinements:** Higher-density waveform rendering for precise syllable-level timeline scrubbing.
* **Transparent Video Export:** Support export with an alpha channel (WebM VP9 and Apple ProRes 4444) to allow direct overlay inside video editors like Premiere, DaVinci Resolve, and Final Cut.

---

## 3. Typography and Stroke Generation

* **Typewriter and Sequential Character Reveal:** Add character-by-character digital text reveal as a complementary effect to cursive handwriting stroke animation.
* **Complex Arabic Ligature Optimization:** Enhance path parsing algorithms to eliminate stroke artifacts when rendering complex calligraphic Arabic scripts.
* **Custom Hand Asset Importer:** Allow users to import custom pen, chalk, and stylus graphic assets with customizable anchor points.

---

## 4. Multi-Platform Distribution

* **Microsoft Store Package (MSIX):** Package and automate MSIX artifact generation for distribution through the Microsoft Store.
* **Linux Deployment:** Automate standalone AppImage and tarball releases on Linux (Ubuntu 22.04+).
