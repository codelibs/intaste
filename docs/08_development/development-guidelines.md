# Assera Development & Contribution Guidelines

**Document Version:** 1.0
**Last Updated:** 2025-10-12
**Target:** Assera OSS Initial Version (UI: Next.js / API: FastAPI)

**Purpose:**
Define branch operations, coding standards, commit conventions, PR/review procedures, CI execution, and release procedures so external/internal contributors can develop/review/release with consistent quality.

---

## 1. Development Flow (Git / Branch Strategy)

- **Default branch:** `main` (always deployable)
- **Branch types:**
  - `feat/<scope>-<short>` New features
  - `fix/<scope>-<short>` Bug fixes
  - `docs/<scope>` Documentation
  - `chore/<scope>` Miscellaneous/tools/CI changes
- **Merge strategy:** **Squash & Merge** (commit formatting)
- **Tagging:** Apply `vX.Y.Z` tag at release time

---

## 2. Commit Conventions (Conventional Commits)

```
<type>(<scope>): <subject>

<body>

<footer>
```

- **type:** `feat|fix|docs|style|refactor|perf|test|build|ci|chore|revert`
- **Example:** `feat(api): add /assist/feedback endpoint`
- **Close:** Write references like `Fixes #123` in footer

---

## 3. Coding Standards

### 3.1 API (Python / FastAPI)

- **Formatter:** `black`, **Linter:** `ruff`, **Type:** `mypy` (strict optional)
- **Dependency management:** `uv` (`pyproject.toml`, `uv.lock` required)
- **Exceptions:** Convert to common error response schema (see design document)

### 3.2 UI (TypeScript / Next.js)

- **Formatter:** `prettier`, **Linter:** `eslint` (`@typescript-eslint`)
- **Type:** strict mode (`tsconfig.json`)
- **UI components:** Tailwind + shadcn/ui, comply with accessibility (aria)

---

## 4. Dependencies & Security

- **SBOM generation:** Attach `syft packages dir:. -o cyclonedx-json` to release deliverables (optional)
- **Vulnerability scanning:** Integrate `trivy fs .` into CI
- **Dependency updates:** Introduce Renovate/Bot (weekly)
- **Secret management:** Do not put actual values in `.env`. Use repository Secrets in CI

---

## 5. Testing Strategy

- **Unit:** API (pytest), UI (vitest)
- **Integration:** API + Fess mock (`responses`/`httpretty`, etc.)
- **E2E:** Playwright (UI→API→dummy search)
- **Load (optional):** k6/Locust (/assist p95, error rate)

---

## 6. CI/CD (GitHub Actions)

Assera uses GitHub Actions for automated testing, security scanning, and deployment. All workflows are defined in `.github/workflows/`.

### 6.1 CI Workflow (`ci.yml`)

**Trigger:** Push to `main`/`develop`, Pull Requests

**Jobs:**
- **API Lint & Type Check**: Runs ruff, black, and mypy on Python code
- **API Tests**: Executes pytest with coverage reporting
- **UI Lint & Type Check**: Runs ESLint, TypeScript, and Prettier checks
- **UI Unit Tests**: Runs vitest with coverage
- **UI E2E Tests**: Executes Playwright tests across browsers
- **Build API**: Builds Docker image for assera-api
- **Build UI**: Builds Docker image for assera-ui
- **Integration Test**: Full stack testing with Docker Compose
- **All Checks Passed**: Summary job that fails if any check fails

**Features:**
- Parallel job execution for faster feedback
- Caching for pip and npm dependencies
- Coverage reports uploaded to Codecov
- Docker layer caching for faster builds
- Integration testing with full service stack

**Duration:** ~5-10 minutes

### 6.2 Security Scan Workflow (`security.yml`)

**Trigger:** Push to `main`, PRs, Weekly schedule (Monday 00:00 UTC)

**Jobs:**
- **Dependency Scan**: Scans Python and Node dependencies for vulnerabilities (Trivy)
- **Docker Scan**: Scans Docker images for security issues (Trivy)
- **CodeQL Analysis**: Static code analysis for Python and JavaScript
- **Secret Scan**: Detects accidentally committed secrets (Gitleaks)
- **License Check**: Verifies dependency licenses compliance
- **Security Summary**: Aggregates results and reports status

**Features:**
- SARIF format results uploaded to GitHub Security tab
- Scheduled weekly scans
- Multiple security tools for comprehensive coverage
- License compliance checking

**Duration:** ~10-15 minutes

### 6.3 Docker Publish Workflow (`docker-publish.yml`)

**Trigger:** Tag push (`v*.*.*`), Manual dispatch

**Jobs:**
- **Build and Push API**: Builds multi-platform image for assera-api
- **Build and Push UI**: Builds multi-platform image for assera-ui
- **Update Docker Compose**: Creates PR to update image tags
- **Publish Summary**: Reports published image details

**Features:**
- Multi-platform builds (amd64, arm64)
- Images published to GitHub Container Registry (ghcr.io)
- Semantic versioning tags
- Automated PR for compose.yaml updates
- Post-build security scanning

**Duration:** ~15-20 minutes

**Image Tags:**
- `latest` - Latest stable release (main branch)
- `v1.2.3` - Specific version
- `v1.2` - Major.minor version
- `v1` - Major version

### 6.4 Release Workflow (`release.yml`)

**Trigger:** Tag push (`v*.*.*`)

**Jobs:**
- **Create Release**: Generates GitHub Release with changelog
- **Create Release Assets**: Packages distribution archives
- **Notify Release**: Sends release notification

**Features:**
- Automatic changelog generation from commit messages
- Categorized changes (Features, Bug Fixes, Docs, etc.)
- Distribution archives (tar.gz, zip)
- Docker image references in release notes
- Installation instructions

**Duration:** ~5 minutes

### 6.5 Monitoring and Alerts

**GitHub Actions:**
- View workflow runs in the Actions tab of your repository
- Failed runs send notifications to maintainers
- Security issues reported in Security tab

**Code Coverage:**
- Configure Codecov for your repository
- Coverage reports on PRs
- Trend analysis over time

**Security:**
- Security advisories in GitHub
- Dependabot alerts for vulnerabilities
- Weekly security scans

### 6.6 CI/CD Best Practices

1. **Keep CI Fast**
   - Use caching
   - Run tests in parallel
   - Optimize Docker builds

2. **Security First**
   - Never commit secrets
   - Review Dependabot PRs promptly
   - Address security scan findings

3. **Test Coverage**
   - Maintain >80% coverage
   - Write tests for new features
   - Test edge cases

4. **Documentation**
   - Update docs with code changes
   - Keep README current
   - Document breaking changes

5. **Clean History**
   - Write meaningful commit messages
   - Squash WIP commits
   - Keep commits focused

---

## 7. PR / Code Review

- **PR Template** (`.github/pull_request_template.md`)
  - Background/Purpose / Changes / Screenshots / Confirmation items / Breaking Changes
- **Checklist:**
  - [ ] Lint/tests pass
  - [ ] Complies with acceptance criteria
  - [ ] Complies with security design (CSP/CORS/log masking)
  - [ ] Documentation updates (README/design documents)

---

## 8. Release Process

1. Update `CHANGELOG.md` (Keep a Changelog)
2. Update version (`package.json` / `pyproject.toml` / `compose.yaml` labels)
3. Tag: `git tag vX.Y.Z && git push --tags`
4. Create GitHub Release:
   - Changes, known issues, upgrade procedures
   - Attachments: SBOM (optional), compose.yaml, .env.example
5. Publish container (optional): `ghcr.io/codelibs/assera-api:sha` / `assera-ui:sha`

### 8.1 Versioning

- **SemVer** compliant: MAJOR.MINOR.PATCH
- Increment MAJOR for breaking changes and document migration procedures

---

## 9. Definition of Done

- Meets acceptance criteria
- 80% unit/integration test coverage
- p95 latency measurement (local) reporting
- Security/linter no warnings
- Documentation (README/design documents) updated

---

## 10. Issue Operations

- **Label examples:** `type/bug`, `type/feature`, `area/ui`, `area/api`, `good first issue`, `help wanted`
- **Templates:** `.github/ISSUE_TEMPLATE/bug_report.md`, `feature_request.md`
- **Priority:** Document with MoSCoW (Must/Should/Could/Won't)

---

## 11. Security Policy (SECURITY.md)

- Vulnerability reporting contact (email/GitHub Security Advisories)
- Adjust based on 90-day public disclosure rule
- Template vulnerability reproduction steps, impact scope, workarounds

---

## 12. Code of Conduct (CODE_OF_CONDUCT.md)

- Adopt Contributor Covenant v2.1
- State maintainer team contact

---

## 13. Artifacts/Deliverables

- `compose.yaml`, `compose.dev.yaml`, `.env.example`
- `Dockerfile` (api/ui)
- Design documents (under docs/)
- SBOM (optional)

---

## 14. Migration Policy

- Data persistence only in Fess/OpenSearch area (Assera is stateless)
- Document procedures in `MIGRATIONS.md` for breaking changes

---

**End of Document**
