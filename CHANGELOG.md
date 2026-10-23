# DrawMotion Changelog

All notable changes to this project are documented in this file.

This project adheres to Semantic Versioning (`MAJOR.MINOR.PATCH`).

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
* **Centralized Author Governance (`AUTHORS`):** Added a top-level `AUTHORS` file establishing full legal authorship coverage for the entire repository tree under GPLv3, documenting Mohamed Fadl as Founder & Lead Architect and EASY SOFT TEAM as the contributing community. This single-file approach protects all source files without requiring per-file modification.
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
