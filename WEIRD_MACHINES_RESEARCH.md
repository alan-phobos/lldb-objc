# Novel Weird Machines for iOS Exploitation Research

## Introduction

"Weird machines" are computational artifacts where code execution occurs outside the original specification of a program. When a system is moved into an unintended state, the software continues transforming broken states into new broken states, triggered by attacker-controlled inputs. This creates an emergent computational device capable of reaching CPU states the programmer never anticipated.

This research identifies novel attack surfaces beyond the well-known NSExpression/NSPredicate and font parser engines used in high-profile iOS exploits like FORCEDENTRY and Operation Triangulation.

---

## 1. WebKit JIT Compiler / DFG Optimization Bugs

JavaScript JIT compilers are rich weird machine targets due to their speculative optimization passes. The DFG (Data Flow Graph) and FTL (Faster Than Light) compilers in JavaScriptCore perform complex type inference that can be confused. CVE-2024-44308 exploited register corruption in Speculative JIT compilation, while CVE-2022-42856 abused type confusion in FTL optimization.

**Why it works:** JIT compilers must balance speed with correctness, making assumptions about types that can be violated. Common-Subexpression Elimination (CSE) bugs, incorrect bounds check elimination, and register allocation errors create exploitable conditions.

**Attack surface:** Safari, WKWebView in any app, embedded web content, JavaScript-heavy applications.

**References:**
- [Google Project Zero: JITSploitation](https://projectzero.google/2020/09/jitsploitation-one.html)
- [Exodus Intelligence: Safari DFG Bug](https://blog.exodusintel.com/2025/08/04/oops-safari-i-think-you-spilled-something/)
- [Jamf: CVE-2022-42856 Analysis](https://www.jamf.com/blog/webkit-vulnerability-cve-2022-42856-jamf-threat-labs-investigation/)

---

## 2. SQLite Virtual Machine / Query Oriented Programming (QOP)

SQLite's query engine is Turing-complete, and researchers have demonstrated "Query Oriented Programming" to exploit memory corruption vulnerabilities entirely through SQL. By hijacking database queries and exploiting virtual table interfaces (particularly RTREE), attackers achieved arbitrary code execution on iOS without requiring signed executables.

**Why it works:** SQLite databases are ubiquitous on iOS (used by iMessage, FaceTime, Contacts, etc.) and are not code-signed. Malicious database content persists across reboots and is queried by privileged processes.

**Attack surface:** Any application deserializing attacker-controlled SQLite databases, especially via airdrop, iMessage attachments, or backup restoration.

**References:**
- [Check Point Research: SELECT code_execution FROM * USING SQLite](https://research.checkpoint.com/2019/select-code_execution-from-using-sqlite/)
- [DEF CON 2019: SQLite Exploits](https://threatpost.com/sqlite-exploits-iphone-hack/147203/)

---

## 3. GPU Shader Compilers (Metal/ANGLE)

GPU shaders represent a powerful weird machine because they execute on separate hardware with minimal validation. The "ShadyShader" vulnerability (CVE-2023-40441) demonstrated that malicious WebGL shaders could overflow Apple's GPU, causing device crashes via infinite loops. More critically, uninitialized GPU register vulnerabilities allow leaking of previously executed shader data, including CNN outputs and LLM data.

**Why it works:** GPU access requires no user consent and shaders are JIT-compiled. Browser translation layers (ANGLE) convert GLSL to Metal Shading Language, creating complex parser chains. The AGX GPU's shader cache persists across applications.

**Attack surface:** Any web content with WebGL, embedded graphics in documents, GPU-accelerated ML inference.

**References:**
- [Imperva: ShadyShader Research](https://www.imperva.com/blog/shadyshader-crashing-apple-m-series-with-single-click/)
- [Whispering Pixels: Uninitialized GPU Registers](https://arxiv.org/html/2401.08881v1)
- [Talos: Apple Graphics Driver Exploitation](https://blog.talosintelligence.com/apple-gfx-deep-dive/)

---

## 4. Audio Codec Parsers (CoreAudio/APAC)

The recent CVE-2025-31200 demonstrated zero-click RCE through Apple's Positional Audio Codec (APAC) decoder. By exploiting a channel count mismatch between global layout metadata and remapping parameters, attackers achieved 16x out-of-bounds memory access. The vulnerability bypassed BlastDoor and enabled kernel escalation.

**Why it works:** Audio files are auto-processed by iMessage and other apps without user interaction. Complex audio formats (spatial audio, multichannel) require sophisticated parsing with numerous integer calculations vulnerable to overflow.

**Attack surface:** iMessage audio attachments, music files, podcast feeds, voice memos, any audio-enabled application.

**References:**
- [CVE-2025-31200 PoC Analysis](https://github.com/zhuowei/apple-positional-audio-codec-invalid-header)
- [Qualys: Apple iOS Zero-Day Analysis](https://threatprotect.qualys.com/2025/04/21/apple-releases-fixes-for-ios-zero-day-vulnerabilities-cve-2025-31200-cve-2025-31201/)

---

## 5. NSKeyedArchiver Serialization / Object Substitution

The NSCoding protocol enables powerful object substitution attacks where deserialized data can specify arbitrary classes. Recent Google Project Zero research revealed that NSDictionary serialization can leak ASLR addresses through pointer-keyed data structures, enabling memory layout disclosure without traditional memory corruption.

**Why it works:** Objective-C's dynamic runtime allows runtime type manipulation. Classes like NSPredicate/NSSortDescriptor can execute selectors, and deserialization occurs in many IPC contexts.

**Attack surface:** App extensions, XPC services, Handoff data, pasteboard content, any cross-process serialization.

**References:**
- [Google Project Zero: NSDictionary ASLR Leak](https://cyberpress.org/google-project-zero-nsdictionary-serialization-enables-aslr-address-disclosure-on-apple-oses/)
- [Snyk: Swift Deserialization Primer](https://snyk.io/blog/swift-deserialization-security-primer/)

---

## 6. X.509/ASN.1 Certificate Parsers

Certificate parsing inconsistencies between TLS libraries create semantic gaps exploitable for authentication bypass. Historical iOS vulnerabilities (CVE-2011-0228) allowed any end-entity certificate to sign further certificates due to unchecked Basic Constraints. The ASN.1 encoding's complexity and lack of maximum integer specifications enable integer overflow attacks.

**Why it works:** Certificate validation is security-critical but varies between implementations. ASN.1's flexibility allows malformed certificates that pass some parsers but not others, enabling man-in-the-middle attacks.

**Attack surface:** HTTPS connections, code signing validation, VPN authentication, S/MIME email.

**References:**
- [Fraunhofer: X.509 Parsing Security](https://www.cybersecurity.blog.aisec.fraunhofer.de/en/parsing-x-509-certificates-how-secure-are-tls-libraries/)
- [Recurity Labs: CVE-2011-0228](https://blog.recurity-labs.com/archives/2011/07/26/cve-2011-0228_ios_certificate_chain_validation_issue_in_handling_of_x_509_certificates/index.html)
- [TALOS-2017-0296: x509 Use-After-Free](https://vulners.com/talos/TALOS-2017-0296)

---

## 7. Mach IPC / Voucher System

The Mach messaging system's complexity creates numerous type confusion and use-after-free opportunities. The voucher subsystem, which handles bookkeeping and port translation, has been exploited in multiple iOS kernel vulnerabilities. Port replacement attacks in launchd (CVE-2018-4280) enabled sandbox escape and privilege escalation.

**Why it works:** Mach ports are kernel objects passed through complex IPC, and the voucher layer adds additional indirection. ISA pointers are not protected by PAC, enabling fake object injection even on modern devices.

**Attack surface:** XPC services, inter-process communication, exception handling, kernel-userspace boundaries.

**References:**
- [Synacktiv: CVE-2021-1782 Analysis](https://www.synacktiv.com/en/publications/analysis-and-exploitation-of-the-ios-kernel-vulnerability-cve-2021-1782)
- [Brandon Azad: CVE-2018-4280 Blanket](https://github.com/bazad/blanket)
- [Project Zero: Survey of iOS Kernel Exploits](https://projectzero.google/2020/06/a-survey-of-recent-ios-kernel-exploits.html)

---

## 8. Bluetooth Protocol Stack / Baseband Interfaces

Bluetooth protocol parsers represent an underexplored wireless attack surface. CVE-2023-45866 demonstrated authentication bypass allowing keystroke injection without user confirmation. Apple's proprietary ARI (Apple Remote Invocation) protocol interfaces with baseband chips and has been reverse-engineered for fuzzing. The BIAS attack affected 31 devices across all major Bluetooth versions.

**Why it works:** Bluetooth stacks parse complex protocol state machines with legacy compatibility requirements. Baseband processors run less-hardened code than application processors, and wireless attacks require no physical access.

**Attack surface:** Paired device impersonation, proximity-based attacks, AirDrop/Handoff interception, wireless keyboard/mouse injection.

**References:**
- [ARIstoteles: Apple Baseband Interface Research (ESORICS 2021)](https://dl.acm.org/doi/10.1007/978-3-030-88418-5_7)
- [CVE-2023-45866: Bluetooth Authentication Bypass](https://www.kaspersky.com/blog/bluetooth-vulnerability-android-ios-macos-linux/50038/)
- [BIAS: Bluetooth Impersonation Attacks](https://francozappa.github.io/about-bias/publication/antonioli-20-bias/antonioli-20-bias.pdf)

---

## Conclusion

These weird machines share common characteristics: complex state machines, Turing-complete or near-Turing-complete computational primitives, parsing of untrusted input, and execution in privileged contexts. Future research should examine:

- Emerging media codecs (AV1, HEIF containers)
- Machine learning model parsers (CoreML, ONNX)
- HomeKit/Matter protocol handlers
- Spatial computing formats (USDZ, Reality files)
- Neural Engine firmware interfaces

The defense-in-depth approach of BlastDoor, PAC, and sandboxing has raised the bar, but the fundamental attack surface of complex parsers processing untrusted data remains.
