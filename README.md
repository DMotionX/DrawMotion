<div align="center">

# 🎬 DrawMotion Animation Studio
### The Open-Source Vector Animation & Whiteboard Studio Powered by Python & Qt

[![Microsoft Store](https://img.shields.io/badge/Microsoft%20Store-Available%20Now-0078D4?style=for-the-badge&logo=microsoft-store&logoColor=white)](https://apps.microsoft.com/detail/9NMVGFL73RH4)
[![Latest Release](https://img.shields.io/badge/Release-v1.7.11-2ea44f?style=for-the-badge&logo=github)](https://github.com/DMotionX/DrawMotion/releases)
[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg?style=for-the-badge)](LICENSE)

<br/>

[![Python Version](https://img.shields.io/badge/Python-3.12%2B-3776AB.svg?logo=python&logoColor=white)](https://www.python.org/)
[![GUI Framework](https://img.shields.io/badge/GUI-PySide6%20(Qt6.8)-41CD52.svg?logo=qt&logoColor=white)](https://wiki.qt.io/Qt_for_Python)
[![Platform Support](https://img.shields.io/badge/Platform-Windows%2010%2F11%20%7C%20Linux-lightgrey.svg?logo=windows)]()
[![Security Audit](https://github.com/DMotionX/DrawMotion/actions/workflows/security-audit.yml/badge.svg)](https://github.com/DMotionX/DrawMotion/actions/workflows/security-audit.yml)
[![Code Style](https://img.shields.io/badge/Code%20Style-Black%20%2F%20PEP8-000000.svg)](https://github.com/psf/black)

<p align="center">
  <b>DrawMotion</b> is a professional, high-performance desktop animation suite designed for creators, educators, and storytellers. Built with <b>PySide6 (Qt)</b> and <b>Python 3.12</b>, it enables seamless creation of whiteboard videos, organic handwriting animations, and synchronized audiovisual presentations with <b>zero telemetry and 100% local privacy</b>.
</p>

<p align="center">
  <a href="https://apps.microsoft.com/detail/9NMVGFL73RH4"><b>Download on Microsoft Store</b></a> •
  <a href="#key-features"><b>Key Features</b></a> •
  <a href="#quickstart-run-locally"><b>Developer Setup</b></a> •
  <a href="#repository-architecture"><b>Architecture</b></a> •
  <a href="#about-the-creator-and-easy-soft-team"><b>EASY SOFT Team</b></a> •
  <a href="docs/README.md"><b>Documentation</b></a> •
  <a href="CONTRIBUTING.md"><b>Contributing</b></a>
</p>

---

### 🖥️ Desktop Studio Showcase

<p align="center">
  <img src="assets/Screenshots%20(Desktop).png" alt="DrawMotion Animation Studio Interface" width="100%" style="border-radius: 10px; box-shadow: 0 10px 30px rgba(0,0,0,0.25);" />
</p>

<p align="center">
  <i>DrawMotion Studio running in Ultra-Dark Mode — featuring the dynamic vector canvas, multi-track timeline, audio waveform sync, and precision properties inspector.</i>
</p>

</div>

---

## ⚡ Quick Download & Installation

| Platform | Distribution Channel | Package Type | Status |
| :--- | :--- | :--- | :--- |
| **Windows 10 / 11** | [Microsoft Store](https://apps.microsoft.com/detail/9NMVGFL73RH4) | Verified Store Package (MSIX) | **Official & Recommended** |
| **Windows Standalone** | [GitHub Releases](https://github.com/DMotionX/DrawMotion/releases) | Standalone Installer (`.exe`) / Portable | Community Builds |
| **Linux (AppImage / DEB)**| [GitHub Releases](https://github.com/DMotionX/DrawMotion/releases) | Standalone Portable Package | Community Builds |
| **Source Code** | [GitHub Clone](#quickstart-run-locally) | Python 3.12 + PySide6 Environment | Open-Source Developers |

---

## ✨ Key Features

* 🖋️ **Physics-Based Handwriting Engine (`components/write_to_image`):** Advanced mathematical trajectories simulating authentic human kinematics (Minimum Jerk velocity profiles, 2/3 Power Law, and Ornstein-Uhlenbeck organic tremor).
* ⚡ **Dynamic Vector Path Tracing:** Automatic parsing and sequential tracing of SVG vectors and raster images with real-time stroke revelation (`dashOffset` animation).
* 🎨 **Dual-Layer Anti-Aliased Typography:** High-resolution display layer decoupled from stroke masks, ensuring crisp anti-aliasing even when rendering real-time drop shadows and glow effects.
* 🎵 **Multitrack Audio Waveform & Timeline Sync:** Frame-accurate multitrack timeline with audio waveform rendering, timeline scrubbing, and scene duration management.
* 🔒 **100% Local-First & Zero Telemetry:** Your creative assets, audio files, and scripts never leave your local machine. No mandatory cloud lock-in, no tracking, complete creative sovereignty.
* 🛡️ **Production-Hardened Boot Lifecycle:** Built-in watchdog circuit breaker (`max_allowed_failures = 3`), C++ signal trapping via `qInstallMessageHandler`, and unbuffered crash reporting.

---

## 🚀 Quickstart (Run Locally)

Run DrawMotion from source on your local machine:

### Prerequisites
* **Python 3.12 (64-bit)**
* **Git**

### 1. Clone the Repository
```bash
git clone https://github.com/DMotionX/DrawMotion.git
cd DrawMotion
```

### 2. Setup Virtual Environment
```bash
# Windows
python -m venv venv
.\venv\Scripts\activate

# Linux / macOS
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Launch Application
```bash
python main.py
```

---

## 📁 Repository Architecture

```text
DrawMotion/
|-- .github/              # Automated CI/CD, security audits (Bandit, pip-audit, TruffleHog)
|-- assets/               # Application assets, stock graphics, and documentation screenshots
|-- bin/                  # Bundled binaries (FFmpeg and helper utilities)
|-- build_assets/         # Windows Inno Setup installer scripts, icons, and MSIX manifests
|-- components/           # Core UI components
|   |-- canvas/           # High-DPI graphics rendering viewport
|   |-- timeline/         # Multi-track keyframe and audio scrubber
|   |-- inspector/        # Object transformation and visual properties editor
|   `-- write_to_image/   # Mathematical handwriting reveal engine
|-- core/                 # Business logic, writing algorithms, and recovery engines
|-- docs/                 # In-depth architectural documentation and engineering specs
|-- graphics/             # Custom QGraphicsScene and rendering artboards
|-- models/               # Domain data models and state containers (SSOT)
|-- resources/            # Application branding, SVG/ICO icon sets, and Dark Studio QSS styles
|-- services/             # Background export workers, FFmpeg pipelines, and audio engines
|-- tests/                # Automated pytest suite, regression fixtures, and integrity tests
`-- utils/                # Helper utilities and OS compatibility bridges
```

---

## 👥 About the Creator and EASY SOFT Team

DrawMotion was conceived, engineered, and founded by **Mohamed Fadl** as Founder and Lead Engineer, developed under the banner of the **EASY SOFT TEAM**.

EASY SOFT is an independent open-source software team dedicated to fighting digital monopolies by engineering high-speed, local-first creative software that respects user privacy and creative sovereignty.

### 🌐 Official Channels & Community
* **Official Microsoft Store:** [DrawMotion on Microsoft Store](https://apps.microsoft.com/detail/9NMVGFL73RH4)
* **Official Website:** [drawmotion-web.vercel.app](https://drawmotion-web.vercel.app/)
* **Official Facebook Page:** [EASY SOFT Team Official](https://www.facebook.com/profile.php?id=61592234934862&locale=ar_AR)
* **Founder on X / Twitter:** [@MohamedFad19757](https://x.com/MohamedFad19757)
* **GitHub Repository:** [DMotionX/DrawMotion](https://github.com/DMotionX/DrawMotion)
* **Support & Inquiries:** `easysoft.dv2team@gmail.com`

---

## 📚 Technical Documentation

In-depth technical and architectural documentation is available in the [`docs/`](docs/README.md) directory:
* [Core Engineering Principles](docs/architecture/core_principles.md)
* [Rendering Pipeline Architecture](docs/architecture/rendering_pipeline.md)
* [Physics-Based Writing Algorithms](docs/architecture/physics_algorithms.md)
* [Security Architecture & Sandboxing](docs/architecture/security.md)
* [Development Roadmap](docs/ROADMAP.md)
* [Legal Policies & EULA](docs/Legal_Policies.md)

---

## 🤝 Contributing

We welcome contributions from developers, animators, and designers.
Please review our [Contribution Guidelines](CONTRIBUTING.md) to learn how to set up your environment, write tests, and submit Pull Requests.

All participants are expected to adhere to our [Code of Conduct](CODE_OF_CONDUCT.md).

---

## 🛡️ Security & Privacy Policy

Security and user privacy are foundational principles of DrawMotion:
* **Zero Telemetry:** The application does not collect analytics, telemetry, or user data.
* **Automated CI Security Scans:** Every commit and pull request is scanned with Bandit (SAST), pip-audit (dependencies), and TruffleHog (secret leaks).
* **Responsible Disclosure:** If you discover a vulnerability, please review our [Security Policy](SECURITY.md) and report it responsibly via our private channels.

---

## 📄 License

DrawMotion is licensed under the **GNU General Public License v3.0 (GPLv3)**.  
See the [LICENSE](LICENSE) file for complete terms and conditions.
