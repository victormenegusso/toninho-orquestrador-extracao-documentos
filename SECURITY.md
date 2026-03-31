# Security Policy

## Reporting a Vulnerability

If you discover a security vulnerability in this project, please report it responsibly.

**Do NOT open a public issue for security vulnerabilities.**

Instead, please send a detailed report to the project maintainers via a private channel. Include:

- Description of the vulnerability
- Steps to reproduce
- Potential impact
- Suggested fix (if any)

We will acknowledge receipt within 48 hours and provide a detailed response within 5 business days.

## Security Tools

This project uses automated security tools as part of the development workflow:

| Tool | Purpose | When |
|------|---------|------|
| [Bandit](https://bandit.readthedocs.io/) | Static security analysis for Python | Pre-commit hook + CI |
| [pip-audit](https://pypi.org/project/pip-audit/) | Dependency vulnerability scanning | Pre-commit hook + CI |
| [Pre-commit hooks](https://pre-commit.com/) | Detect secrets, debug statements, private keys | Every commit |

## Security Practices

- **No secrets in code**: Use environment variables via `.env` (see `.env.example`)
- **Dependency auditing**: `make audit` checks for known vulnerabilities
- **Static analysis**: `make security` runs Bandit against the codebase
- **Pre-commit checks**: Automatic detection of private keys and debug statements
- **CI enforcement**: All security checks run in GitHub Actions before merge

## Supported Versions

| Version | Supported |
|---------|-----------|
| Latest  | ✅         |

## Dependencies

Security-relevant dependencies are regularly updated. Run `make audit` to check for known vulnerabilities in the dependency tree.
