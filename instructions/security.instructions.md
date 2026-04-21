---
name: "security"
description: "Language-agnostic secure coding standards based on OWASP Top 10"
applyTo: "**"
---

<!--
Adapted from the awesome-copilot project:

https://github.com/github/awesome-copilot/blob/main/instructions/security-and-owasp.instructions.md

The original is TypeScript-heavy; this version has been rewritten to be
language-agnostic and adapted to match the cobots instruction style.
- Scribs
-->

# Secure Coding Standards

Follow these guidelines to write secure code in any language. These standards are based on the [OWASP Top 10 (2025)](https://owasp.org/Top10/) and general secure coding principles.

## Severity Levels

* **CRITICAL** — Exploitable vulnerability. Must be fixed before merge.
* **IMPORTANT** — Significant risk. Should be fixed in the same sprint.
* **SUGGESTION** — Defense-in-depth improvement. Plan for a future iteration.

## OWASP Top 10 (2025) Quick Reference

| # | Category | Key Mitigation |
|---|----------|----------------|
| A01 | Broken Access Control | Auth middleware on every endpoint, RBAC, ownership checks |
| A02 | Security Misconfiguration | Security headers, no debug in prod, no default credentials |
| A03 | Software Supply Chain Failures | Dependency audits, lockfile integrity, SBOM |
| A04 | Cryptographic Failures | Strong hashing for passwords, TLS everywhere, no secrets in code |
| A05 | Injection | Parameterized queries, input validation, no raw HTML with user input |
| A06 | Insecure Design | Threat modeling, secure design patterns, abuse case testing |
| A07 | Authentication Failures | Rate-limit login, secure session management, MFA |
| A08 | Software or Data Integrity Failures | Signed artifacts, no insecure deserialization |
| A09 | Security Logging and Alerting Failures | Log security events, no PII in logs, active alerting |
| A10 | Mishandling of Exceptional Conditions | Handle all errors, no stack traces in prod, fail-secure |

## Injection Prevention

### SQL Injection (CRITICAL)

* Never concatenate or interpolate user input into SQL queries.
* Always use parameterized queries or prepared statements.

```sql
-- BAD: string concatenation
SELECT * FROM users WHERE id = '<user_input>';

-- GOOD: parameterized query (syntax varies by language/driver)
SELECT * FROM users WHERE id = ?;
```

### Command Injection (CRITICAL)

* Never pass user input directly into shell commands.
* Use argument arrays instead of shell string interpolation.
* Validate and allowlist input values wherever possible.
* Set timeouts and output size limits on subprocess execution.

### Cross-Site Scripting — XSS (CRITICAL)

* Never render unsanitized user input as HTML.
* Use text interpolation (not raw HTML injection) by default in templates.
* When raw HTML is required, sanitize with a trusted library (e.g., DOMPurify, Bleach).
* Set a strong `Content-Security-Policy` header.

### Server-Side Request Forgery — SSRF (CRITICAL)

* Never allow user-controlled URLs to be fetched without validation.
* Enforce scheme allowlists (`https:` only) and hostname allowlists.
* Resolve DNS and reject private/reserved IP ranges before making the request.
* Disable HTTP redirects or validate each redirect target.

### Path Traversal (CRITICAL)

* Resolve file paths and verify they remain within an allowed base directory.
* Never trust user-provided filenames or path components without validation.

### Template Injection (CRITICAL)

* Never use user input as a template source.
* User input should only be passed as data to predefined templates.

## Authentication

### Password Storage (CRITICAL)

* Never store passwords in plaintext or use fast hashes (MD5, SHA-1, SHA-256).
* Use a slow, salted, memory-hard algorithm: Argon2id (preferred), bcrypt, or scrypt.

### Token Management (CRITICAL)

* Always set expiration times on tokens (JWTs, session tokens, API keys).
* Enforce a specific signing algorithm — never allow `alg: none`.
* Store tokens in `httpOnly`, `secure`, `SameSite=strict` cookies — not in `localStorage`.

### Brute-Force Protection (CRITICAL)

* Rate-limit authentication endpoints (login, registration, password reset).
* Use exponential backoff or account lockout after repeated failures.

### Session Management (IMPORTANT)

* Regenerate session IDs on login to prevent session fixation.
* Invalidate all sessions on password change or privilege escalation.

### OAuth (CRITICAL)

* Always include a `state` parameter for CSRF protection.
* Use PKCE with S256 challenge method for public clients (SPAs, mobile apps).

## Authorization

### Access Control (CRITICAL)

* Apply authentication and authorization middleware to every protected endpoint.
* Never rely on client-side checks alone — always verify on the server.
* Check resource ownership (prevent IDOR): verify the requesting user owns the resource before returning or modifying it.

### Mass Assignment (CRITICAL)

* Never pass raw user input directly to create/update operations.
* Explicitly pick allowed fields from the request.

### Privilege Escalation (CRITICAL)

* Never trust role or permission fields from user input.
* Assign roles server-side based on business logic.

### Sensitive Operations (IMPORTANT)

* Require re-authentication (current password, MFA) before account deletion, email change, or other high-impact actions.

## Secrets Management

### No Hardcoded Secrets (CRITICAL)

* Never hardcode API keys, tokens, passwords, or connection strings in source code.
* Use environment variables, secret managers (Vault, AWS Secrets Manager, GitHub Secrets), or encrypted configuration files.

### Git Hygiene (CRITICAL)

* Add `.env`, `*.pem`, `*.key`, and other secret files to `.gitignore`.
* Never commit secrets to version control — even in "test" or "example" commits.
* If a secret is accidentally committed, rotate it immediately.

### Client-Side Exposure (CRITICAL)

* Never expose server-side secrets through client-facing environment variables, bundled assets, or public APIs.

### CI/CD Secrets (IMPORTANT)

* Use masked secrets in CI pipelines.
* Never echo or log environment variables that contain secrets.

## Cryptography

* Use TLS for all network communication.
* Prefer well-established libraries for cryptographic operations — never implement your own crypto.
* Use strong, current algorithms (AES-256, RSA-2048+, SHA-256+).
* Rotate keys and certificates on a regular schedule.

## Error Handling and Logging

### Error Responses (IMPORTANT)

* Never expose stack traces, SQL queries, or internal details in production error responses.
* Return generic error messages to clients; log detailed errors server-side.

### Security Logging (IMPORTANT)

* Log authentication attempts (success and failure), authorization failures, and input validation failures.
* Never log passwords, tokens, PII, or other sensitive data.
* Use correlation IDs to trace requests across services.
* Set up active alerting for anomalous patterns (e.g., repeated login failures).

## Dependencies

### Supply Chain Security (CRITICAL)

* Run dependency audits regularly (e.g., `npm audit`, `pip-audit`, `cargo audit`).
* Pin dependency versions and verify lockfile integrity.
* Review new dependencies before adding them — check for typosquatting, suspicious `postinstall` scripts, and known vulnerabilities.

### Updates (IMPORTANT)

* Keep dependencies up to date, especially for security patches.
* Use automated tools (Dependabot, Renovate) to track dependency updates.

## HTTP Security Headers

Apply the following headers on all HTTP responses in web applications:

* `Content-Security-Policy` — restrict sources of executable content.
* `Strict-Transport-Security` — enforce HTTPS (`max-age=31536000; includeSubDomains; preload`).
* `X-Content-Type-Options: nosniff` — prevent MIME-type sniffing.
* `X-Frame-Options: DENY` — prevent clickjacking (also use `frame-ancestors 'none'` in CSP).
* `Referrer-Policy: strict-origin-when-cross-origin` — limit referrer leakage.
* `Permissions-Policy` — disable unnecessary browser features (`camera=(), microphone=(), geolocation=()`).

## CORS

* Never use `Access-Control-Allow-Origin: *` with credentials.
* Explicitly allowlist trusted origins.

## Input Validation

* Validate all external input on the server, regardless of client-side validation.
* Use schema validation libraries (e.g., zod, joi, pydantic, serde) to enforce expected types and constraints.
* Reject unexpected fields — do not silently ignore them.

## Security Checklist

Before merging code, verify:

* [ ] **Injection**: All queries are parameterized; user input is never interpolated into commands, queries, or templates.
* [ ] **Authentication**: Tokens expire, passwords use strong hashing, login is rate-limited.
* [ ] **Authorization**: Every endpoint checks auth; resource ownership is verified.
* [ ] **Secrets**: No hardcoded secrets; `.gitignore` covers sensitive files.
* [ ] **Errors**: No stack traces or internal details leak to clients.
* [ ] **Dependencies**: Audit passes; no known vulnerabilities.
* [ ] **Headers**: Security headers are set on all responses.
* [ ] **Logging**: Security events are logged; no PII or secrets in logs.
