# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 0.1.x   | ✅ |

## Reporting a Vulnerability

**Please do not report security vulnerabilities through public GitHub issues.**

Instead, please report them via email to:
- **Primary**: jan-hendrik.wendisch@deutschebahn.com
- **Secondary**: volker.kuehn@deutschebahn.com

Include the following information:
- Description of the vulnerability
- Steps to reproduce
- Potential impact
- Suggested fix (if any)

## Response Timeline

- **Acknowledgment**: Within 48 hours
- **Initial assessment**: Within 5 business days
- **Status updates**: Weekly until resolved

## Security Measures

Our repository includes:
- Automated dependency vulnerability scanning (Dependabot)
- SAST scanning with Ruff security rules
- SBOM generation and vulnerability analysis (Syft + Grype)
- OpenSSF Scorecard security assessment

## Disclosure Policy

We follow responsible disclosure:
1. Vulnerabilities are fixed before public disclosure
2. Credit given to reporters (unless anonymity requested)
3. Security advisories published for confirmed issues
