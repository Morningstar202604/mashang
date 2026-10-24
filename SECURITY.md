# Security Policy · 安全策略

## Supported versions

| Version | Supported |
|---|---|
| 0.4.x | ✅ Active |
| 0.3.x | ⚠️ Security fixes only |
| < 0.3 | ❌ |

## Reporting a vulnerability

Please **do not open a public issue** for security problems.

- Preferred: GitHub private advisory — <https://github.com/badhope/mashang/security/advisories/new>
- Alternative: email `bigbad338@outlook.com` with subject `[SECURITY] mashang`.

We aim to acknowledge within **72 hours** and to ship a fix or mitigation within **14 days** for confirmed issues. Please include: affected version, platform (Android build / web client), reproduction steps, and impact.

## Threat model

Mashang runs **user-authored code on the user's own device**. It is a learning sandbox, not a security boundary against the device owner.

| Surface | Mitigation |
|---|---|
| Python code execution | Per-run fresh namespace, `sys.settrace` watchdog (8 s), stdout/stderr capped at 1 MiB, `input()` served from a queue — see `app/src/main/python/runner.py` |
| JavaScript code execution | Rhino interpreter with `ClassShutter` denying all Java class access; instruction-count watchdog — see `app/src/main/java/com/pyneon/academy/js/JsBridge.kt` |
| Web client | Pyodide runs in a **Web Worker**; runaway execution is terminated by the parent after 15 s; all user/course text is inserted with `textContent` (no `innerHTML` for user data) |
| Content distribution | HTTPS only, 5 MiB response cap, pack-id allowlist, canonical-path check, SHA-256 for catalog and every pack |
| Secrets | Signing credentials come from environment variables / CI secrets; `keystore/` and `local.properties` are git-ignored; the repo has no private key material |

### Known limitations (by design)

- The sandbox prevents accidental damage and runaway loops; it is **not** a hardened container. A determined user can still consume CPU/memory on their own device.
- On the web client, Python code can reach browser globals through Pyodide's `js` module. Do not paste untrusted lessons into a session where you are signed into sensitive sites.
- `import` of arbitrary stdlib modules is allowed (teaching requirement); file writes go to the app's private sandbox on Android.

## Out of scope

- Issues requiring physical access to an unlocked device
- Denial of service against your own device with intentionally malicious code
- Third-party dependencies with no exploitable path in this project (report upstream, but tell us too)
