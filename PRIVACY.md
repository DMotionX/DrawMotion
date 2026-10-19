# DrawMotion Privacy Policy

**Last Updated:** October 2026
**Official Repository:** [https://github.com/DMotionX/DrawMotion](https://github.com/DMotionX/DrawMotion)
**Official Website:** [https://drawmotion-web.vercel.app/](https://drawmotion-web.vercel.app/)
**Contact:** [easysoft.dv2team@gmail.com](mailto:easysoft.dv2team@gmail.com)

---

## Overview

DrawMotion ("the Software") is an open-source desktop application developed by **Mohamed Fadl** and the **EASY SOFT TEAM** and distributed under the [GNU General Public License v3.0 (GPLv3)](LICENSE).

This Privacy Policy explains how DrawMotion handles your data when you use the Software.

---

## 1. Core Principle: Strict Local-First Architecture

DrawMotion is engineered from the ground up on a **strict Local-First architecture**. Your creative work, privacy, and data sovereignty are paramount.

- **All project files**, vector drawing paths, timeline configurations, imported assets (images, audio, fonts), and rendered video animations are **processed and stored strictly on your local disk**.
- We have **zero access** to your projects, files, or creative output.

---

## 2. Zero Data Collection & Zero Telemetry

DrawMotion **does NOT**:

- Collect, harvest, monitor, sell, or profile your personal information
- Embed background analytics, trackers, or behavioral telemetry
- Use user fingerprinting or session profiling of any kind
- Transmit your project files, creative work, or device data to any server

---

## 3. 100% Offline Capable

DrawMotion functions fully without an active internet connection. No internet access is required to create, edit, animate, or export your projects.

---

## 4. Network Communication (Updates Only)

The **only** automated network communication performed by DrawMotion occurs when you explicitly check for software updates:

- DrawMotion makes a secure **HTTPS GET request** to the official GitHub Releases API:
  `https://api.github.com/repos/DMotionX/DrawMotion/releases/latest`
- The request retrieves only the latest version tag and release changelog text.
- Standard hosting providers (GitHub) may process technical routing metadata (IP address, User-Agent) as required for operational routing. We do not link this metadata to your personal identity, nor do we retain, sell, or share it.

---

## 5. Full Trust Capability Disclosure (`runFullTrust`)

DrawMotion requests the `runFullTrust` capability on Windows to:

- Execute the bundled **FFmpeg** multimedia processing utility for video and audio export
- Access the **local file system** to save project files (`.dm`) and export media (MP4, GIF, PNG)
- Utilize **local GPU hardware acceleration** for rendering vector graphics and animations

DrawMotion does **not** use this capability to access network resources, transmit data externally, or perform any operation beyond local creative production.

---

## 6. Support Communications

If you voluntarily contact us via email ([easysoft.dv2team@gmail.com](mailto:easysoft.dv2team@gmail.com)), we receive only the technical details you choose to share. This information is used exclusively to diagnose bugs and provide technical assistance. It is never shared with third parties.

---

## 7. Open Source Transparency

DrawMotion is fully open-source under the GNU GPLv3 license. You can inspect the complete source code, including all network communication logic, at any time:

👉 [https://github.com/DMotionX/DrawMotion](https://github.com/DMotionX/DrawMotion)

---

## 8. Changes to This Policy

Any updates to this Privacy Policy will be committed directly to the official repository and reflected in the version changelog. The effective date at the top of this document will be updated accordingly.

---

## 9. Contact

For privacy inquiries or concerns:

**EASY SOFT TEAM — Founded by Mohamed Fadl**
📧 [easysoft.dv2team@gmail.com](mailto:easysoft.dv2team@gmail.com)
🐦 [@MohamedFad19757](https://x.com/MohamedFad19757)
🔗 [https://github.com/DMotionX/DrawMotion](https://github.com/DMotionX/DrawMotion)
