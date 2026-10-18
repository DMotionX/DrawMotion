# Contributing to DrawMotion

Thank you for your interest in contributing to DrawMotion. We are building an open-source vector animation and whiteboard video studio, and community contributions are welcome.

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
   git remote add upstream https://github.com/MohamedFadl2344/DrawMotion.git
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
