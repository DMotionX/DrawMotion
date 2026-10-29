# Contributing to DrawMotion

Thank you for your interest in contributing to DrawMotion. We are building an open-source vector animation and whiteboard video studio, and community contributions are welcome.

---

## Recent Architectural Updates & Solved Issues (v1.7.13)

To help contributors understand the current state of the application and recent developments, here is an overview of the latest bug fixes and functional enhancements:

### Solved Issues & Bug Fixes
* **Standalone Projects Hub Runtime Integrity:** Resolved an issue where the Projects Hub would fail to launch when running standalone compiled packages or portable builds on external media. The runtime environment now provisions all necessary styling and layout libraries automatically, guaranteeing flawless Projects Hub operation across all deployment targets and external drives.
* **Background Worker Graceful Teardown:** Resolved an issue where closing the Projects Hub welcome window could terminate the application while background update checks were active, eliminating thread destruction warnings and ensuring 100% clean, silent process exit.
* **Playback Crash Shield & Dialog Flood Elimination:** Resolved a critical issue where an unhandled error during animation playback would trigger a rapid-fire loop of modal error popups (~60 times per second), completely freezing the application and preventing users from closing the dialog or quitting via the terminal. The animation engine now automatically halts playback immediately upon any failure, cleanly hides all hands, safely resets state, and the global error system suppresses duplicate stacked popups while enabling immediate termination via Ctrl+C.
* **Paragraph Editor Recursion & Freezing Fix:** Fixed a severe issue where multiline typing or pressing the Enter key in the paragraph editor could trigger recursive layout recalculations and freeze the user interface. Typing, line breaks, and automatic text direction detection (supporting both Arabic and English) now run smoothly without recursive locking.
* **Drawing Hand Leak Elimination:** Fixed an issue where the whiteboard drawing hand would linger or flash briefly during transitions between images or scene boundaries. The drawing hand is now strictly hidden during non-drawing transits while preserving natural continuity across continuous drawing strokes.
* **Multi-Text Hand Continuity:** Ensured smooth, uninterrupted writing transitions across consecutive text elements without the hand disappearing prematurely or resetting unexpectedly.
* **Motion Entrance Physics Parameter Fix:** Resolved a playback crash that occurred when playing animations configured with motion entrance effects (like physical bounce and hand drag), restoring seamless animation execution.
* **Canvas Center Overlap Collision Fix:** Eliminated an issue where newly created text elements automatically centered themselves directly on top of existing artwork and images in the workspace.

### Core Enhancements & Functional Improvements
* **Interactive Studio Reload & Startup Splash Screen:** Introduced a high-performance, frameless startup reload screen that appears instantly (in under 50ms) when launching the application. Designed with modern studio aesthetics, it features an animated emerald capsule progress bar, live user-friendly status updates tailored for animators and creators, and a seamless cinematic dissolve transition directly into the Projects Hub.
* **Natural Mouse-Click Text Placement:** Clicking anywhere on the canvas with the Text tool now opens the paragraph editor exactly at the clicked position, and the resulting text element is placed precisely where clicked, complete with intelligent screen-edge clamping to keep the input box fully visible.
* **In-Place Text Editing on Double-Click:** Double-clicking an existing text item on the canvas now opens the text editor in place directly over the element, rather than disorientingly pulling the editor to the center of the viewport.
* **Ergonomic Drawing Hand Scaling:** Updated the default whiteboard drawing hand size to an ergonomic standard (2.0) that naturally matches artwork dimensions, with live responsive updates when adjusting size settings in real time.
* **High-Fidelity Text Rendering:** Upgraded text image generation with crisp rendering flags, an optimal default font size (42pt), and proportional canvas auto-fitting.
* **Full Isolation Between Writing and Drawing Hands:** Completely decoupled the whiteboard drawing hand mechanics from the physics-based handwriting system, ensuring adjustments to one never compromise the other.
* **Strict Image Isolation Guarantee:** Kept all image addition, centering, and scaling behaviors completely untouched, ensuring total stability across the media workflow.
* **Full Automated Test Coverage:** Expanded repository test coverage to comprehensive automated suites verifying startup lifecycle, Projects Hub readiness, kinematics, text placement, and crash resilience with a 100% pass rate.

---

## Development Setup

### 1. Prerequisites
* Python 3.12 (64-bit)
* Git
* Python virtual environment (`venv`)

### 2. Fork and Clone
1. Fork the repository on GitHub.
2. Clone your personal fork locally:
   ```bash
   git clone https://github.com/<your-username>/DrawMotion.git
   cd DrawMotion
   ```
3. Set the upstream remote:
   ```bash
   git remote add upstream https://github.com/DMotionX/DrawMotion.git
   ```

### 3. Environment Setup
```bash
# Windows
python -m venv venv
.\venv\Scripts\activate

# Linux / macOS
python3 -m venv venv
source venv/bin/activate

# Install dependencies and test runners
pip install --upgrade pip
pip install -r requirements.txt
pip install pytest pytest-qt
```

### 4. Running the Application Locally
```bash
python main.py
```

---

## Running Automated Tests

Before submitting any code changes, ensure automated tests pass cleanly:

```bash
# Run test suite
pytest -v
```

When introducing new algorithms or core features, please write corresponding tests inside the `tests/` directory.

---

## Coding Standards and Architectural Rules

To maintain high code quality and prevent runtime crashes, all contributors must observe these rules:

1. **Strict SSOT (Single Source of Truth):**
   * UI components (e.g. `TimelinePanel`) must never hold independent canonical item lists. State flows from `Workspace` to UI via Qt signals (`items_changed`).
2. **Stateless Cloning:**
   * Never use `copy.deepcopy()` on `QGraphicsItem` instances. Always serialize via `item.to_dict()` and reconstruct using `from_dict()`.
3. **Dual-Layer Rendering Integrity:**
   * Visual effects (`QGraphicsEffect`) must only be applied to static display layers, never to dynamically animating stroke paths.
4. **Code Style and Formatting:**
   * Adhere to PEP 8 standards.
   * Use clear variable and function names.
   * Add type annotations (`typing`) where appropriate.
5. **No Hardcoded Absolute Paths:**
   * Always reference assets using `Path(__file__).resolve().parent` or project root relative anchors.

---

## Git Branching and Commit Conventions

### Branch Naming
* Features: `feat/feature-name` (e.g., `feat/timeline-snapping`)
* Fixes: `fix/bug-description` (e.g., `fix/svg-stroke-calculation`)
* Documentation: `docs/update-guide`

### Commit Message Format
We follow the Conventional Commits specification:
* `feat: add magnetic timeline block snapping`
* `fix: prevent crash when rendering unclosed SVG paths`
* `docs: clarify local setup instructions in README`
* `test: add unit test for dual-layer composition mode`
* `refactor: optimize physics stroke interpolation`

---

## Submitting a Pull Request (PR)

1. Ensure your local branch is up-to-date with `upstream/main`:
   ```bash
   git fetch upstream
   git rebase upstream/main
   ```
2. Run test suites locally (`pytest -v`).
3. Push your branch to your GitHub fork:
   ```bash
   git push origin feat/your-feature
   ```
4. Open a Pull Request against the `main` branch.
5. Fill out the PR template completely, describing the rationale, testing steps, and screenshots if UI changes were made.
