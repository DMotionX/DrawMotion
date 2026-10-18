# Security Policy and Responsible Disclosure

The DrawMotion team takes the security of our desktop application, dependencies, and user data seriously. We welcome responsible collaboration with security researchers and developers to identify and remediate potential vulnerabilities.

---

## Supported Versions

Only the latest release versions receive active security updates and vulnerability patches:

| Version | Supported | Security Status                       |
|:--------|:----------|:--------------------------------------|
| 1.7.x   | Yes       | Currently supported & actively patched |
| < 1.7   | No        | End of Life (Upgrade strongly advised) |

---

## Scope for Security Researchers

We encourage security testing and vulnerability reporting in the following areas:

### In Scope
* Command Injection Defenses: Spawning external subprocesses (e.g. FFmpeg, FFprobe) and argument escaping.
* Path Traversal and Arbitrary File Writes: Asset caching, project saving/loading (`.wip`), and template imports.
* Malicious File Deserialization: Parsing untrusted SVG/XML vector files or custom project dictionaries.
* Privilege Escalation: Inno Setup installer scripts and process permission limits.
* Crash Exploitation: Memory safety bugs, buffer overflows, or segmentation faults in C++ Qt extensions.

### Out of Scope
* Attacks requiring physical access to an unlocked developer workstation.
* Denial of Service via intentionally malformed local user configurations.
* Social engineering or phishing targeting repository maintainers.

---

## Reporting a Vulnerability (Responsible Disclosure)

> [!CAUTION]
> Do NOT file public GitHub Issues for suspected security vulnerabilities or zero-day exploits.  
> Public disclosure before a fix is released endangers users.

Please report all vulnerabilities using one of our private channels:

1. **GitHub Private Vulnerability Reporting (Preferred):**
   * Navigate to the **Security** tab of the repository.
   * Click on **"Report a vulnerability"** to open a confidential discussion draft directly with the maintainers.

2. **Security Contact:**
   * Contact the project lead directly at: `easysoft.dv2team@gmail.com`
   * Please include:
     * A clear description of the vulnerability and attack vector.
     * Proof of Concept (PoC) scripts or reproduction steps.
     * Potential impact assessment and suggested mitigation.

---

## Response and Remediation SLA

* **Initial Acknowledgement:** Within 48 hours of receiving your report.
* **Triage and Validation:** Within 5 business days with an assigned severity rating.
* **Patch Deployment:** Critical issues aim for remediation within 14 calendar days.
* **Coordinated Disclosure:** We coordinate public credit and disclosure with you after the fix is published in an official release.

---

## Safe Harbor Policy

We consider security research conducted under this policy to be authorized. We will not pursue legal action against researchers who:
* Act in good faith to avoid privacy violations, destruction of data, and service disruption.
* Keep discovered vulnerabilities confidential until the patch is publicly deployed.
* Comply with applicable local and international laws.
