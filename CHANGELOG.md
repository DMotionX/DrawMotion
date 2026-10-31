# DrawMotion Changelog

All notable changes to this project are documented in this file.

This project adheres to Semantic Versioning (`MAJOR.MINOR.PATCH`).

## [1.7.14] - 2026-10-31

### Piece-by-Piece Semantic Drawing Isolation, Timeline Stability Shield & Native Security Engine

This release introduces an authentic whiteboard drawing experience by ensuring every distinct piece and object is drawn 100% completely before moving to the next, fixes timeline scene block shrinkage and playhead desynchronization upon deleting items, hardens project archive security against Zip-Slip attacks, and adds rich interactive visual demonstrations to project documentation.

#### Core Drawing Experience & Whiteboard Engine (تجربة رسم السبورة البيضاء الواقعية)
* **Piece-by-Piece Object Isolation (رسم كل عنصر وتلوينه 100% أولاً):**
  - **Solid Reveal Algorithm:** Eliminated unnatural vertical slab slicing where multiple objects on screen were partially filled at the same time. The drawing hand now completes each semantic object (e.g. Laptop, then Arduino, then Arrows, then LEDs) 100% before lifting off the canvas and transitioning to the next item.
  - **Clean Outline Algorithm:** Isolated independent vector contours and shapes so that outlines for each object are drawn continuously without erratic jumping back and forth across the canvas. Added smooth in-air flight paths between distinct pieces.
  - **Professional CAD Assembly:** Restructured structural CAD rendering so that each mechanical object completes all its assembly phases (outer chassis, primary components, connectors, and fine traces) in sequence before moving to other canvas elements.
  - **Organic Sketch Algorithm:** Grouped independent visual clusters to ensure artistic sketches are rendered object by object with natural, continuous hand motions.
  - **Natural Hand Velocity:** Fixed excessive hand speed during fill operations, ensuring consistent drawing speeds and natural transitions between visual elements.

#### Timeline & Canvas Stability (استقرار شريط التايم لاين والمشاهد)
* **Scene Duration Shrinkage Elimination:** Fixed an issue where deleting an image or text element caused the scene timeline block to shrink to half a second (0.5s), causing text clipping (`Sc...`). Empty scenes now maintain a clean, stable 2.0-second baseline duration.
* **Automatic Playhead & Timer Resynchronization:** When all items in a scene are deleted, the red playhead line and digital timer automatically return to the start of the scene (`00:00.0 / 00:02.0`) instead of remaining frozen at the end of the deleted media.
* **Timeline Block Drag Constraints:** Enforced a minimum duration of 2.0 seconds when resizing scene blocks directly on the timeline, preventing accidental collapsing of scenes.
* **Preservation of User-Defined Durations:** Manually customized scene durations set via right-click are now preserved even after items are removed or modified.

#### Security & System Protection (محرك الأمان وحماية النظام)
* **Fast In-Memory Protection:** Integrated ultra-fast in-memory validation that prevents application freezing or lag while checking file paths and inputs.
* **Project Archive Shield (Zip-Slip Protection):** Added security safeguards against malicious or corrupted `.dmproj` archives, preventing files from being written outside the project directory.
* **Windows Reserved Name Guard:** Added automatic filtering for reserved Windows system names (`CON`, `PRN`, `AUX`, `NUL`, `COM1-9`, `LPT1-9`) to prevent OS-level deadlocks.

#### Visual Documentation & Demos (التوثيق المرئي والعروض التوضيحية)
* **Live Studio Demonstrations:** Embedded high-resolution animated demonstrations (GIFs) in the project documentation showcasing the full Whiteboard Studio workflow and the natural physics handwriting engine.

---

## [1.7.13] - 2026-10-28

### Robust Playback Crash Shield, Natural Click-Based Text Placement, Transit Hand Isolation & Core Stability

This release delivers major stability and usability breakthroughs across the animation studio: an automated fail-safe playback crash shield that eliminates infinite error popup loops, mouse-click based text placement avoiding artboard center collisions, strict transit hand hiding between scenes and media, and complete decoupling of drawing hand and handwriting mechanics.

#### Bug Fixes & Stability
* **Playback Crash Shield & Anti-Storm Guard:** Solved the critical issue where unhandled runtime errors during animation playback triggered rapid-fire modal error dialogs (~60 FPS) that froze the application. The playback loop now immediately halts its timer, cleanly hides hands, resets state, and the global error tracker suppresses duplicate stacked popups while allowing instant terminal termination via Ctrl+C.
* **Paragraph Editor Recursion Elimination:** Resolved an issue where pressing Enter or typing multiline text triggered cascading layout updates, preventing editor freezing and guaranteeing seamless Arabic and English typing.
* **Scene & Media Transit Hand Leak Fix:** Fixed the whiteboard drawing hand briefly flashing or lingering during scene-to-scene and image-to-image transitions, guaranteeing hands remain strictly invisible when moving between distinct visual elements.
* **Multi-Text Hand Continuity:** Maintained uninterrupted writing hand transitions across sequential text elements without unexpected hand disappearing or premature resets.
* **Motion Entrance Parameter Resolution:** Fixed playback crashes when using motion entrance modes (such as physical bounce or drag) by restoring required hand scaling parameters in kinematics solvers.

#### Key Enhancements & Usability
* **Natural Mouse-Click Text Placement:** Clicking with the Text tool on the canvas now opens the paragraph editor directly at the mouse cursor position, and the rendered text item is placed exactly where the user clicked, complete with intelligent boundary clamping to keep input boxes within view.
* **Direct In-Place Text Editing:** Double-clicking an existing text item now opens the paragraph editor directly over the item itself, rather than disorientingly forcing it to the screen center.
* **Ergonomic Drawing Hand Scale Normalization:** Updated the default whiteboard drawing hand size to 2.0 to naturally match standard canvas dimensions, with real-time responsive updates when adjusted in project settings.
* **High-Resolution Font Rendering:** Upgraded text rendering quality with optimized default sizing (42pt) and intelligent canvas proportions.
* **Strict Image Isolation:** Guaranteed that image addition, placement, and centering mechanics remain 100% untouched and safe from unintended side effects.
* **Comprehensive Test Suite:** Expanded automated test validation across the entire repository to 80 unit tests with a 100% pass rate.

---

## [1.7.12] - 2026-10-23

### Studio-Grade Visual Quality, Cross-Platform POSIX Paths, Project Persistence Engine & Portable Distribution

This release introduces high-fidelity canvas ingestion preserving native multi-megapixel asset resolution, studio-grade FFmpeg video rendering with visually lossless encoding, complete cross-platform path centralization and POSIX execution permissions for Linux, a triple-layer self-healing project persistence architecture that permanently eliminates image loss and engine freezing, and a standalone portable diagnostic packaging pipeline.

#### Studio-Grade Visual Fidelity & Video Export Engine
* **High-Fidelity Canvas Ingestion (4096px Safety Ceiling):** Eliminated aggressive downscaling of raw assets to 1080p upon canvas insertion in `AnimatedImageItem`. Native resolution is now preserved up to an industrial 4096px safety ceiling, allowing standard 1080p, 2K, and 4K assets to maintain pristine sharpness during zoom and transformation.
* **Studio-Grade FFmpeg Encoding:** Upgraded video export parameters in `FFmpegManager` from default high compression to visually lossless studio settings (`-crf 17`, `-tune animation`, `-preset medium`, `-pix_fmt yuv420p`, `-color_range pc`), eliminating banding artifacts, muddy gradients, and compression blur on animated vector strokes.
* **Premultiplied Alpha Anti-Aliasing:** Enforced `Format_ARGB32_Premultiplied` across compositing and scribble mask buffers, permanently fixing jagged pixelated borders on transparent PNG graphics.

#### Cross-Platform Architecture & POSIX Permissions (Linux/Windows)
* **Centralized Path Resolution (`utils/paths.py`):** Unified AppData and XDG Base Directory specification compliance (`~/.local/share/drawmotion` on Linux, `%LOCALAPPDATA%\DrawMotion` on Windows), removing ad-hoc hardcoded directory lookups across 5 core modules (`ffmpeg_manager.py`, `project_manager.py`, `library_widget.py`, `recovery_dialog.py`, `lifecycle_tracker.py`).
* **POSIX Execution Permissions (`+x`):** Enforced `stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH` on extracted FFmpeg binaries under POSIX/Linux environments, preventing `Permission denied` (`errno 13`) export crashes on Linux desktops and AppImage containers.
* **GitHub Actions CI Linux Workflow:** Introduced `.github/workflows/ci-linux-tests.yml` running headless pytest validation under Ubuntu 24.04 with Xvfb, auditing cross-platform paths, static asset case sensitivity against ext4 filesystems, and POSIX permissions.

#### Robust Project Persistence & Fail-Safe Restore Engine
* **Triple-Layer Asset Packaging Fallback:** Overhauled `ProjectManager._pack_and_save()` to eliminate asset dropouts when moving or saving projects:
  - *Level 1 (Direct Disk Path):* Copies verified asset from disk.
  - *Level 2 (Recursive Asset Library Scan):* Automatically searches library subdirectories (e.g., `task2/`) by filename if the source was relocated.
  - *Level 3 (In-Memory Live Pixmap Extraction):* Captures the full-resolution uncorrupted `_pixmap` directly from RAM (`canvas_item._pixmap.save()`) if the original file was deleted from disk, making missing image assets mathematically impossible.
* **Smart Asset Resolver & Self-Healing Loader:** Upgraded `ProjectManager.load_project_file()` with `_resolve_asset_path()` to transparently repair legacy project archives referencing absolute or moved paths.
* **Zero-Wait Visual Display:** Reconstructed canvas items immediately display their native pixmap (`set_progress(1.0)`), eliminating blank/white screens on project open.
* **Non-Blocking Background Plan Calculation (60 FPS):** Wired `plan_started` and `plan_ready` signals and triggered asynchronous background vector calculations via `build_plan_async()` on a dedicated `QThread`, preventing UI/timeline freezing upon project loading.
* **Windows File-Lock Resilience (`[WinError 32]`):** Protected project cache extraction by catching locked file exceptions and dynamically isolating concurrent sessions into dedicated `ActiveProject_<uuid>` directories.

#### Diagnostic Standalone Distribution & Portable Packaging
* **Zero-Installer Portable Packaging:** Automated Nuitka standalone compilation producing `DrawMotion-Diagnostic-v1.7.12-Portable.zip` (~184 MB), bundled with all required PySide6 plugins, C++ runtimes, and documentation.
* **Bundled FFmpeg & Security Binaries:** Guaranteed inclusion of `bin/ffmpeg.exe` and `core/security_engine/bin/scanner.exe` directly inside the portable distribution root.
* **Interactive Diagnostic Launcher (`Debug_DrawMotion.bat`):** Integrated real-time log tailing displaying the last 15 lifecycle events from `startup_lifecycle.log` directly in the command prompt upon exit.
* **Offline-Resilient Updater:** Verified that `core/updater.py` and `SilentUpdateChecker` fail gracefully without crashes or modal blocks when running offline.

#### Automated Testing Suite
* **Comprehensive Automated Tests (`tests/test_project_assets_persistence.py`):** Added 5 dedicated test cases verifying direct disk packaging, library subfolder recovery, in-memory RAM pixmap extraction, instant visual rendering, and legacy project self-healing.
* **Complete Pytest Suite Validation:** All 23 test cases in the test suite pass cleanly (22 passed, 1 skipped for Linux POSIX permissions on Windows).

---

## [1.7.11] - 2026-10-19

### Microsoft Store Publishing Alignment, Open-Source Purge & Author Governance

This release aligns the MSIX packaging manifest and application UI with the official Microsoft Partner Center individual developer identity, provisions the standard Privacy Policy required for `runFullTrust` capability, introduces centralized author governance, and purges all legacy closed-source labeling from the application.

#### Microsoft Store & MSIX
* **Privacy Policy Provisioned (`PRIVACY.md`):** Added a standards-compliant, zero-telemetry privacy policy to satisfy the mandatory Microsoft Store `runFullTrust` capability requirement. Policy is accessible at `https://github.com/DMotionX/DrawMotion/blob/main/PRIVACY.md`.
* **Microsoft Store Identity Alignment:** Updated `build_assets/msstore/AppxManifest.xml` with the official `Package/Identity/Name` and `Package/Identity/Publisher` values issued by Microsoft Partner Center, enabling the unsigned MSIX to pass identity validation upon submission.
* **MSIX Checksum:** Extended `.github/workflows/build-msstore.yml` to generate and attach a dedicated `checksum_msstore.txt` (SHA-256) for the Store package.

#### Open-Source Brand & Legal Purge
* **Removed "Closed-Source Freeware" Labels:** Updated in-app legal dialog (`components/help_dialogs.py`) to replace the legacy `Closed-Source Freeware` badge and proprietary EULA language with the accurate `Free & Open Source (GNU GPLv3)` designation.
* **GitHub Link Modernization:** Updated the official GitHub social tile in the Settings → Updates hub (`components/settings/components/update_settings.py`) to point to the authoritative open-source repository: `https://github.com/DMotionX/DrawMotion`.

#### Author Governance & Legal Protection
* **Centralized Author Governance (`AUTHORS`):** Added a top-level `AUTHORS` file establishing full legal authorship coverage for the entire repository tree under GPLv3, documenting Mohamed Fadl as Founder & Lead Architect and DrawMotion Team as the contributing community. This single-file approach protects all source files without requiring per-file modification.
* **Runtime Version Synchronization:** Synchronized version `1.7.11` across `core/updater.py`, `core/serialization/serializer.py`, Inno Setup scripts, and Microsoft Store manifests.

---

## [1.7.10] - 2026-10-19

### Multi-Platform Packaging Expansion, Direct Linux Installers & XML Staging Fix

This release expands cross-platform Linux delivery with direct, uncompressed installers (`AppImage` and `.deb`), resolves the Microsoft Store MakeAppx XML syntax error, excludes developer artifacts from release channels, and enforces hermetic isolation between development and production environments.

#### Linux Direct Distribution Packages
* **Universal Standalone AppImage (`DrawMotion-x86_64.AppImage`):** Automated creation of a single-file, zero-extraction executable bundle running directly across all major Linux distributions (Ubuntu, Debian, Fedora, Arch, Mint, openSUSE).
* **Native Debian/Ubuntu Package (`DrawMotion_amd64.deb`):** Generated a direct installer package with automated system menu registration, desktop icons (`/usr/share/applications/drawmotion.desktop`), and standard `/opt/DrawMotion` directory deployment.
* **Universal System Call Abstraction:** Replaced Windows-exclusive `os.startfile` with Qt's `QDesktopServices.openUrl` in recovery dialogs, ensuring crash and diagnostic logs open natively on Linux desktops.

#### CI/CD Pipeline & Packaging Fixes
* **MSIX Manifest XML Declaration Integrity:** Replaced case-insensitive PowerShell replacement with targeted .NET regex and UTF-8 encoding in `.github/workflows/build-msstore.yml`, preserving the mandatory W3C `<?xml version="1.0" encoding="utf-8"?>` declaration and eliminating MakeAppx error `C00CEE40`.
* **Public Release Stream Sanitization:** Excluded developer diagnostic ZIP archive (`DrawMotion_DeveloperEdition.zip`) from public release assets to prevent user confusion and maintain clean release channels.

#### Core Engine & Environment Isolation
* **Hermetic Dev/Prod Isolation:** Hardened `utils.paths.is_frozen_build()` to reliably detect compiled runtime environments using `builtins.__compiled__`, `sys.__nuitka_version__`, and executable inspections, permanently preventing user asset and database leakage between `DrawMotion-Dev` and `DrawMotion`.
* **Runtime Version Synchronization:** Synchronized version `1.7.10` across `core/updater.py`, `core/serialization/serializer.py`, Inno Setup scripts, and Microsoft Store manifests.

---

## [1.7.9] - 2026-10-19

### CI/CD Packaging Pipeline Hardening & Multi-Platform Compatibility

This maintenance release resolves multi-platform CI build failures across Windows Store (MSIX) and Linux Ubuntu 24.04 environments, hardens repository security boundaries, and synchronizes application engine versioning.

#### CI/CD & Build Infrastructure
* **MSIX Store Packaging Staging Fix:** Resolved directory collision error (`Item already exists`) in `.github/workflows/build-msstore.yml` during layout staging by safely overlaying visual assets into the existing Nuitka application distribution assets hierarchy.
* **Linux Modern Runner Compatibility (Ubuntu 24.04 LTS):** Fixed package dependency failures in `.github/workflows/build-linux.yml` by dynamically adapting to the ALSA library migration (`libasound2t64` with automatic fallback to `libasound2`), preventing apt-get failure on noble runners.
* **Inno Setup & Release Workflow Harmonization:** Synchronized build scripts and release automation with explicit version parameterization (`v1.7.9`) across Windows developer, production installer, Linux binary, and Microsoft Store packages.

#### Security & Repository Hygiene
* **Code-Signing Certificate Isolation:** Verified and enforced that all digital certificate signing operations run strictly through encrypted CI secrets (`CERT_BASE64` and `CERT_PASSWORD`), with complete exclusion of private keys, certificates (`.pfx`, `.p12`, `.cer`, `.crt`), and temporary decryption artifacts from git tracking.
* **Workspace Artifact Sanitization:** Isolated developer-only local scripts (`build_diagnostic_local.bat`, `fixed_install.md`) and pre-build cache directories (`assets/uploads`, `assets/library`, `*.sqlite`) from upstream remote pushes.
* **Legal and Distribution Governance:** Documented repository retention and deployment rules for build recipe templates, license specifications, and application store manifests.

#### Core Engine & Version Synchronization
* **Runtime Version Bump:** Synchronized application version `1.7.9` across the internal update checker (`core/updater.py`), JSON project state serializer (`core/serialization/serializer.py`), Windows Inno Setup scripts, and Microsoft Store AppxManifest.

---

## [1.7.8] - 2026-10-17

### Initial Official Open-Source Release

This release establishes the baseline open-source architecture of DrawMotion with a fully hardened startup lifecycle, multi-algorithm vector animation engine, and cross-platform build pipelines.

#### Core Engine and Drawing Systems
* **Physics-Based Handwriting Algorithms:** Integrated five distinct mathematical stroke simulation models (Steady, Minimum Jerk, Natural Human, Organic Sketch, and Stop & Go) replicating realistic human handwriting dynamics.
* **Vector Path Tracing:** Automatic parsing and sequential tracing of SVG vectors and raster images with dynamic stroke revelation (`dashOffset` animation).
* **Dual-Layer Anti-Aliased Typography:** High-resolution display layer decoupled from stroke masks, ensuring crisp anti-aliasing even when rendering real-time drop shadows and glow effects.
* **Multitrack Timeline:** Dynamic timeline with audio waveform rendering, audio scrubbing, and scene duration management.
* **Stateless Data Serialization:** Memory-safe clipboard and scene persistence based on JSON serialization, eliminating pointer corruption and memory leaks across scene duplication.

#### Platform Stability and Fault Isolation
* **Native C++ Signal Trapping:** Registered `qInstallMessageHandler` prior to `QApplication` instantiation to capture low-level Qt messages (`qFatal`, `qCritical`, `qWarning`) directly to persistent logs (`%LOCALAPPDATA%\DrawMotion\Logs\qt_messages.log`).
* **Python Fault Handler:** Enabled unbuffered `faulthandler` directed to `%LOCALAPPDATA%\DrawMotion\Logs\crash_faulthandler.log` with module-level global handles.
* **Watchdog Circuit Breaker:** Implemented a startup failure cap (`max_allowed_failures = 3`) to permanently prevent infinite restart loops.
* **Qt Plugin Bundling:** Explicitly bundled Qt image and icon engines (`imageformats`, `iconengines`, `sensible`, `multimedia`) in Nuitka compilation to prevent segmentation faults during vector rendering.
* **Direct Public Updates:** Configured automated update checking querying official releases from `DMotionX/DrawMotion` with fast parallel multi-stream downloads.
