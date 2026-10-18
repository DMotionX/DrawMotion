# Application Security Architecture

This document summarizes the core defensive mechanisms implemented in DrawMotion to ensure data integrity and host system protection.

---

## 1. Subprocess Execution Hardening

DrawMotion relies on external utilities (such as FFmpeg and FFprobe) for media encoding and probe operations. To prevent command injection:
* All process invocations use explicit argument lists rather than shell strings.
* Direct shell execution (`shell=True`) is prohibited across all export pipelines.
* Dynamic parameters (such as output filenames, audio sample rates, and bitrates) are validated against strict type checks before process spawning.

---

## 2. File System Path Validation and Traversal Defense

When importing external assets (images, SVGs, audio tracks) or loading project archives (`.wip` files):
* File paths are resolved and checked to ensure they reside within valid user directories or designated application workspaces.
* Absolute path resolution verifies that canonical paths do not break out of expected root directories using path traversal sequences (`../`).
* On Windows, project file naming filters out reserved device names (`CON`, `PRN`, `AUX`, `NUL`, `COM1-9`, `LPT1-9`).

---

## 3. Data Deserialization Safety

Project loading utilizes a JSON-based data serialization layer:
* Native Python `pickle` is strictly avoided to eliminate arbitrary code execution vectors.
* Project structures are parsed using standard JSON decoders and mapped to typed internal models with field boundary checks.

---

## 4. Crash Containment and Fault Isolation

* `qInstallMessageHandler` captures fatal internal Qt errors before unhandled C++ exceptions terminate the process abruptly.
* The watchdog circuit breaker halts infinite restart cascades if repeated startup faults occur.
