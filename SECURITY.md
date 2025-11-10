# Security Policy

## Supported Versions

We release security updates for the following versions:

| Version | Supported          |
| ------- | ------------------ |
| 1.0.x   | :white_check_mark: |
| < 1.0   | :x:                |

## Reporting a Vulnerability

**Please do not report security vulnerabilities through public GitHub issues.**

Instead, please report them via one of the following methods:

### Preferred Method: GitHub Security Advisory

1. Go to the [Security tab](https://github.com/abrahamahn/mpsm/security)
2. Click "Report a vulnerability"
3. Fill out the security advisory form

### Alternative: Email

Send an email to: [your.email@example.com]

Include:
- Type of vulnerability
- Steps to reproduce
- Potential impact
- Suggested fix (if any)

## Response Timeline

- **Initial Response**: Within 48 hours
- **Status Update**: Within 7 days
- **Fix Timeline**: Depends on severity
  - **Critical**: Within 7 days
  - **High**: Within 30 days
  - **Medium**: Within 90 days
  - **Low**: Next release cycle

## Security Measures

### Current Security Practices

- **Dependency Scanning**: Automated with Dependabot
- **Code Scanning**: Static analysis in CI/CD
- **Secret Scanning**: Enabled on repository
- **Access Control**:
  - Registry operations require admin rights
  - File operations validate paths
  - Input sanitization for user paths

### Known Security Considerations

1. **Windows Registry Access**
   - Requires administrator privileges
   - Creates backups before modifications
   - Validates registry keys before access

2. **File System Operations**
   - Path traversal prevention
   - Permission checks before file moves
   - Dry-run mode available for testing

3. **Plugin Scanning**
   - No automatic plugin execution
   - Metadata extraction only (PE headers)
   - Sandboxed file operations

## Disclosure Policy

When we receive a security report:

1. We will confirm receipt within 48 hours
2. We will investigate and provide a status update within 7 days
3. We will work on a fix in a private security advisory
4. We will release a patched version
5. We will publicly disclose the vulnerability after the patch is released

## Security Best Practices for Users

### Safe Usage

- **Always backup** before running organize commands
- **Use dry-run mode** first: `mpsm organize --dry-run`
- **Review changes** in dry-run output before applying
- **Run as administrator** only when necessary
- **Keep MPSM updated** to the latest version

### Registry Safety

```bash
# Backup before making changes
mpsm registry backup

# Review what will change
mpsm organize --dry-run

# Apply changes only after review
mpsm organize --approve

# Restore if needed
mpsm registry restore --backup-id <id>
```

### File Organization Safety

```bash
# Always use dry-run first
mpsm organize --dry-run

# Review the output carefully

# Only proceed if satisfied
mpsm organize --approve
```

## Security Updates

Security updates will be:
- Announced in release notes
- Tagged with `security` label in GitHub
- Listed in CHANGELOG.md
- Documented in commit messages with `SECURITY:` prefix

## Security Checklist for Contributors

Before submitting code that:

- [ ] Accesses the Windows registry
- [ ] Moves or modifies files
- [ ] Processes user input
- [ ] Executes external commands

Please ensure:

- [ ] Input validation is implemented
- [ ] Path traversal is prevented
- [ ] Error handling is robust
- [ ] Permissions are checked
- [ ] Changes are reversible (backups)
- [ ] Dry-run mode is available
- [ ] Tests include security edge cases

## Vulnerability Severity Levels

### Critical
- Remote code execution
- Privilege escalation
- Data loss without recovery
- Widespread impact

### High
- Local code execution
- Data corruption with difficult recovery
- Security feature bypass
- High impact on confidentiality/integrity

### Medium
- Denial of service
- Information disclosure
- Moderate impact on availability

### Low
- Minor information disclosure
- Low impact issues
- Security improvements

## Credit

We will credit security researchers who responsibly disclose vulnerabilities:
- In release notes
- In CHANGELOG.md
- In security advisories

Thank you for helping keep MPSM and its users safe!
