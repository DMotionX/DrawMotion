<div align="center">

# DrawMotion
### Open-Source Vector Animation and Whiteboard Studio

[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](LICENSE)
[![Python Version](https://img.shields.io/badge/Python-3.12-3776AB.svg?logo=python&logoColor=white)](https://www.python.org/)
[![GUI Framework](https://img.shields.io/badge/GUI-PySide6%20(Qt6)-41CD52.svg?logo=qt&logoColor=white)](https://wiki.qt.io/Qt_for_Python)
[![Platform Support](https://img.shields.io/badge/Platform-Windows%20%7C%20Linux-lightgrey.svg)]()
[![Code Style](https://img.shields.io/badge/Code%20Style-Black%20%2F%20PEP8-000000.svg)](https://github.com/psf/black)

<p align="center">
  <b>DrawMotion</b> is a high-performance desktop studio for creating whiteboard video animations, expressive handwriting dynamics, and synchronized audiovisual presentations powered by <b>PySide6 (Qt)</b> and <b>Python 3.12</b>.
</p>

[Quickstart](#quickstart-run-locally) • [Key Features](#key-features) • [About the Creator & Team](#about-the-creator-and-easy-soft-team) • [Documentation](docs/README.md) • [Contributing](CONTRIBUTING.md) • [Security Policy](SECURITY.md)

</div>

---

## About the Creator and EASY SOFT Team

DrawMotion was conceived, engineered, and founded by **Mohamed Fadl** as Founder and Lead Engineer, developed under the banner of the **EASY SOFT TEAM**.

EASY SOFT is an independent non-profit software team dedicated to fighting digital monopolies by engineering high-speed, local-first vector animation software that respects user privacy and creative sovereignty.

### Connect and Join the Community
We actively invite Python developers, Qt engineers, animators, and beta testers to follow our official channels, share feedback, and help develop DrawMotion:

* **Official Facebook Page:** [EASY SOFT Team Official](https://www.facebook.com/profile.php?id=61592234934862&locale=ar_AR)
* **Official Website:** [drawmotion-web.vercel.app](https://drawmotion-web.vercel.app/)
* **Founder on X / Twitter:** [@MohamedFad19757](https://x.com/MohamedFad19757)
* **GitHub Repository:** [MohamedFadl2344/DrawMotion](https://github.com/MohamedFadl2344)
* **Support and Inquiries:** `easysoft.dv2team@gmail.com`

---

## Key Features

* **Physics-Based Handwriting Engine:** Mathematical models simulating authentic human pen movement (Steady, Minimum Jerk, Natural Human, Organic Sketch, and Stop & Go).
* **Dynamic Vector Path Tracing:** Automatic parsing and sequential tracing of SVG vectors and raster images with real-time stroke revelation (`dashOffset` animation).
* **Dual-Layer Anti-Aliased Typography:** High-resolution display layer decoupled from stroke masks, ensuring crisp anti-aliasing even when rendering real-time drop shadows and glow effects.
* **Multitrack Audio Waveform and Timeline Sync:** Multitrack timeline with audio waveform rendering, timeline scrubbing, and scene duration management.
* **Zero-Leak Data Serialization:** Memory-safe clipboard and undo/redo architecture based on stateless JSON data serialization (SSOT).
* **Production-Hardened Boot Lifecycle:** Built-in watchdog circuit breaker (`max_allowed_failures = 3`), C++ signal trapping via `qInstallMessageHandler`, and unbuffered crash reporting.

---

## Quickstart (Run Locally)

Run DrawMotion on your local machine:

### Prerequisites
* Python 3.12 (64-bit)
* Git

### 1. Clone the Repository
```bash
git clone https://github.com/MohamedFadl2344/DrawMotion.git
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

## Repository Structure

```text
DrawMotion/
|-- .github/              # Automated CI/CD, security audits and issue templates
|-- assets/               # Application assets, fonts and stock graphics
|-- bin/                  # Bundled binaries (FFmpeg and helper utilities)
|-- build_assets/         # Windows Inno Setup installer scripts and icons
|-- components/           # Core UI components (Timeline, Inspector, Canvas, LeftPanel)
|-- core/                 # Business logic, writing algorithms and recovery engines
|-- docs/                 # Engineering and architectural documentation
|-- graphics/             # Custom QGraphicsScene and rendering artboards
|-- models/               # Domain data models and state containers
|-- resources/            # Application branding, SVG/ICO icon sets and styles
|-- services/             # Background export workers and audio engines
|-- tests/                # Automated pytest suite, test fixtures and manual scripts
`-- utils/                # Helper utilities and OS compatibility bridges
```

---

## Documentation

In-depth technical documentation is available in the [`docs/`](docs/README.md) directory:
* [Core Engineering Principles](docs/architecture/core_principles.md)
* [Rendering Pipeline](docs/architecture/rendering_pipeline.md)
* [Physics-Based Writing Algorithms](docs/architecture/physics_algorithms.md)
* [Security Architecture](docs/architecture/security.md)
* [Development Roadmap](docs/ROADMAP.md)
* [Legal Policies and EULA](docs/Legal_Policies.md)

---

## Contributing

We welcome contributions from developers, animators, and designers.
Please review our [Contribution Guidelines](CONTRIBUTING.md) to learn how to set up your environment, write tests, and submit Pull Requests.

All participants are expected to adhere to our [Code of Conduct](CODE_OF_CONDUCT.md).

---

## Security Policy

If you discover a potential security vulnerability in DrawMotion, please review our [Security Policy](SECURITY.md) and report it responsibly via our private channels.

---

## License

DrawMotion is licensed under the **GNU General Public License v3.0 (GPLv3)**.  
See the [LICENSE](LICENSE) file for complete terms and conditions.
