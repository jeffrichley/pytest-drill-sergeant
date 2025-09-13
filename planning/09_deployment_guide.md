# Deployment Guide

## Overview

This guide covers the deployment and distribution of pytest-drill-sergeant, including package publishing, CI/CD integration, and community distribution.

## Package Distribution

### PyPI Publishing

#### Package Structure
```
pytest-drill-sergeant/
├── pyproject.toml          # Package configuration
├── README.md               # Project documentation
├── LICENSE                 # License file
├── CHANGELOG.md            # Version history
├── src/
│   └── pytest_drill_sergeant/
│       ├── __init__.py
│       ├── core/
│       ├── plugin/
│       └── cli/
├── tests/                  # Test suite
├── docs/                   # Documentation
└── examples/               # Example projects
```

#### pyproject.toml Configuration
```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "pytest-drill-sergeant"
version = "1.0.0"
description = "A pytest plugin that acts as a drill sergeant for AI-written tests"
readme = "README.md"
license = {file = "LICENSE"}
authors = [
    {name = "Your Name", email = "your.email@example.com"},
]
maintainers = [
    {name = "Your Name", email = "your.email@example.com"},
]
keywords = ["pytest", "testing", "quality", "ai", "linting"]
classifiers = [
    "Development Status :: 4 - Beta",
    "Intended Audience :: Developers",
    "License :: OSI Approved :: MIT License",
    "Operating System :: OS Independent",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.10",
    "Programming Language :: Python :: 3.11",
    "Programming Language :: Python :: 3.12",
    "Framework :: Pytest",
    "Topic :: Software Development :: Testing",
    "Topic :: Software Development :: Quality Assurance",
]
requires-python = ">=3.10"
dependencies = [
    "pytest>=8.0.0",
    "coverage>=7.0.0",
    "click>=8.0.0",
    "pydantic>=2.0.0",
    "rich>=13.0.0",
    "datasketch>=1.6.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0.0",
    "pytest-cov>=4.0.0",
    "black>=23.0.0",
    "ruff>=0.1.0",
    "mypy>=1.0.0",
    "pre-commit>=3.0.0",
]
ci = [
    "github-actions-toolkit>=0.1.0",
    "sarif-tools>=0.1.0",
]

[project.urls]
Homepage = "https://github.com/your-org/pytest-drill-sergeant"
Documentation = "https://pytest-drill-sergeant.readthedocs.io"
Repository = "https://github.com/your-org/pytest-drill-sergeant"
Issues = "https://github.com/your-org/pytest-drill-sergeant/issues"
Changelog = "https://github.com/your-org/pytest-drill-sergeant/blob/main/CHANGELOG.md"

[project.scripts]
drill-sergeant = "pytest_drill_sergeant.cli.main:cli"

[project.entry-points.pytest11]
drill_sergeant = "pytest_drill_sergeant.plugin.hooks"

[tool.hatch.build.targets.wheel]
packages = ["src/pytest_drill_sergeant"]

[tool.hatch.build.targets.sdist]
include = [
    "/src",
    "/tests",
    "/docs",
    "/examples",
    "/README.md",
    "/LICENSE",
    "/CHANGELOG.md",
]
```

#### Publishing Process
```bash
# 1. Install build tools (using uv for speed)
uv add --dev build twine

# 2. Build package
uv run python -m build

# 3. Check package
uv run twine check dist/*

# 4. Upload to PyPI
uv run twine upload dist/*

# 5. Verify installation
uv add pytest-drill-sergeant
```

### GitHub Releases

#### Release Automation
```yaml
# .github/workflows/release.yml
name: Release

on:
  push:
    tags:
      - 'v*'

jobs:
  release:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          pip install uv
          uv add --dev build twine

      - name: Build package
        run: uv run python -m build

      - name: Check package
        run: uv run twine check dist/*

      - name: Publish to PyPI
        env:
          TWINE_USERNAME: __token__
          TWINE_PASSWORD: ${{ secrets.PYPI_API_TOKEN }}
        run: uv run twine upload dist/*

      - name: Create GitHub Release
        uses: actions/create-release@v1
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        with:
          tag_name: ${{ github.ref }}
          release_name: Release ${{ github.ref }}
          draft: false
          prerelease: false
```

## CI/CD Integration

### GitHub Actions

#### Basic Workflow
```yaml
# .github/workflows/ci.yml
name: CI

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: [3.10, 3.11, 3.12]
        pytest-version: [8.0, 8.1, 8.2]

    steps:
      - uses: actions/checkout@v4

      - name: Set up Python ${{ matrix.python-version }}
        uses: actions/setup-python@v4
        with:
          python-version: ${{ matrix.python-version }}

      - name: Cache pip dependencies
        uses: actions/cache@v3
        with:
          path: ~/.cache/pip
          key: ${{ runner.os }}-pip-${{ hashFiles('**/pyproject.toml') }}
          restore-keys: |
            ${{ runner.os }}-pip-

      - name: Install dependencies
        run: |
          pip install uv
          uv add pytest==${{ matrix.pytest-version }}
          uv add --dev -e .[dev]

      - name: Run tests
        run: uv run pytest tests/ -v --cov=pytest_drill_sergeant --cov-report=xml

      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          file: ./coverage.xml
          flags: unittests
          name: codecov-umbrella
```

#### Quality Gate Workflow
```yaml
# .github/workflows/quality-gate.yml
name: Quality Gate

on:
  pull_request:
    branches: [main]

jobs:
  quality-gate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          pip install -e .[dev]

      - name: Run quality checks
        run: |
          pytest tests/ --ds-mode=quality-gate --ds-sarif-report=quality-report.sarif

      - name: Upload SARIF
        uses: github/codeql-action/upload-sarif@v3
        with:
          sarif_file: quality-report.sarif

      - name: Comment on PR
        uses: actions/github-script@v6
        with:
          script: |
            const fs = require('fs');
            const report = JSON.parse(fs.readFileSync('quality-report.sarif', 'utf8'));

            const findings = report.runs[0].results.length;
            const message = `## Quality Gate Results\n\nFound ${findings} quality issues.`;

            github.rest.issues.createComment({
              issue_number: context.issue.number,
              owner: context.repo.owner,
              repo: context.repo.repo,
              body: message
            });
```

### GitLab CI

#### .gitlab-ci.yml
```yaml
stages:
  - test
  - quality
  - deploy

variables:
  PIP_CACHE_DIR: "$CI_PROJECT_DIR/.cache/pip"

cache:
  paths:
    - .cache/pip
    - venv/

test:
  stage: test
  image: python:3.11
  before_script:
    - python -m venv venv
    - source venv/bin/activate
    - pip install --upgrade pip
    - pip install -e .[dev]
  script:
    - pytest tests/ -v --cov=pytest_drill_sergeant --cov-report=xml
  artifacts:
    reports:
      coverage_report:
        coverage_format: cobertura
        path: coverage.xml
  coverage: '/TOTAL.*\s+(\d+%)$/'

quality:
  stage: quality
  image: python:3.11
  before_script:
    - python -m venv venv
    - source venv/bin/activate
    - pip install --upgrade pip
    - pip install -e .[dev]
  script:
    - pytest tests/ --ds-mode=quality-gate --ds-sarif-report=quality-report.sarif
  artifacts:
    reports:
      sast: quality-report.sarif

deploy:
  stage: deploy
  image: python:3.11
  script:
    - pip install build twine
    - python -m build
    - twine upload dist/*
  only:
    - tags
```

### Jenkins

#### Jenkinsfile
```groovy
pipeline {
    agent any

    environment {
        PYTHON_VERSION = '3.11'
        PYTEST_VERSION = '8.1'
    }

    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        stage('Setup') {
            steps {
                sh '''
                    python -m venv venv
                    source venv/bin/activate
                    pip install --upgrade pip
                    pip install pytest==${PYTEST_VERSION}
                    pip install -e .[dev]
                '''
            }
        }

        stage('Test') {
            steps {
                sh '''
                    source venv/bin/activate
                    pytest tests/ -v --cov=pytest_drill_sergeant --cov-report=xml
                '''
            }
            post {
                always {
                    publishCoverage adapters: [
                        coberturaAdapter('coverage.xml')
                    ], sourceFileResolver: sourceFiles('STORE_LAST_BUILD')
                }
            }
        }

        stage('Quality Gate') {
            steps {
                sh '''
                    source venv/bin/activate
                    pytest tests/ --ds-mode=quality-gate --ds-sarif-report=quality-report.sarif
                '''
            }
            post {
                always {
                    publishHTML([
                        allowMissing: false,
                        alwaysLinkToLastBuild: true,
                        keepAll: true,
                        reportDir: 'quality-report',
                        reportFiles: 'index.html',
                        reportName: 'Quality Report'
                    ])
                }
            }
        }

        stage('Deploy') {
            when {
                tag pattern: "v\\d+\\.\\d+\\.\\d+", comparator: "REGEXP"
            }
            steps {
                sh '''
                    source venv/bin/activate
                    pip install build twine
                    python -m build
                    twine upload dist/*
                '''
            }
        }
    }
}
```

## Documentation Deployment

### Read the Docs

#### Configuration
```yaml
# .readthedocs.yml
version: 2

build:
  os: ubuntu-22.04
  tools:
    python: "3.11"

sphinx:
  configuration: docs/conf.py

formats:
  - htmlzip
  - epub

python:
  install:
    - method: pip
      path: .
      extra_requirements:
        - docs
```

#### Documentation Structure
```
docs/
├── conf.py
├── index.rst
├── installation.rst
├── configuration.rst
├── usage.rst
├── api.rst
├── examples.rst
├── contributing.rst
└── _static/
```

### GitHub Pages

#### Documentation Workflow
```yaml
# .github/workflows/docs.yml
name: Deploy Documentation

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  docs:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          pip install -e .[docs]

      - name: Build documentation
        run: |
          cd docs
          make html

      - name: Deploy to GitHub Pages
        uses: peaceiris/actions-gh-pages@v3
        if: github.ref == 'refs/heads/main'
        with:
          github_token: ${{ secrets.GITHUB_TOKEN }}
          publish_dir: ./docs/_build/html
```

## Community Distribution

### Pre-commit Hooks

#### Configuration
```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/your-org/pytest-drill-sergeant
    rev: v1.0.0
    hooks:
      - id: drill-sergeant
        name: pytest-drill-sergeant
        entry: drill-sergeant
        language: system
        types: [python]
        args: [--mode=advisory]
```

### VS Code Extension

#### Package.json
```json
{
  "name": "pytest-drill-sergeant",
  "displayName": "pytest-drill-sergeant",
  "description": "AI test quality enforcement for pytest",
  "version": "1.0.0",
  "engines": {
    "vscode": "^1.74.0"
  },
  "categories": ["Testing", "Linters"],
  "activationEvents": [
    "onLanguage:python"
  ],
  "main": "./out/extension.js",
  "contributes": {
    "commands": [
      {
        "command": "drill-sergeant.analyze",
        "title": "Analyze Test Quality"
      }
    ],
    "configuration": {
      "title": "pytest-drill-sergeant",
      "properties": {
        "drill-sergeant.mode": {
          "type": "string",
          "default": "advisory",
          "enum": ["advisory", "quality-gate", "strict"],
          "description": "Analysis mode"
        },
        "drill-sergeant.persona": {
          "type": "string",
          "default": "drill_sergeant",
          "description": "Persona for feedback"
        }
      }
    }
  }
}
```

### Docker Distribution

#### Dockerfile
```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY pyproject.toml .
COPY src/ src/

RUN pip install -e .

ENTRYPOINT ["drill-sergeant"]
```

#### Docker Compose
```yaml
version: '3.8'

services:
  drill-sergeant:
    build: .
    volumes:
      - .:/workspace
    working_dir: /workspace
    command: lint /workspace
```

## Monitoring and Analytics

### Usage Tracking

#### Anonymous Usage Metrics
```python
# Optional usage tracking
import uuid
import json
import requests
from pathlib import Path

class UsageTracker:
    def __init__(self):
        self.anonymous_id = self._get_or_create_id()

    def _get_or_create_id(self):
        config_dir = Path.home() / ".config" / "pytest-drill-sergeant"
        config_dir.mkdir(parents=True, exist_ok=True)

        id_file = config_dir / "anonymous_id"
        if id_file.exists():
            return id_file.read_text().strip()
        else:
            anonymous_id = str(uuid.uuid4())
            id_file.write_text(anonymous_id)
            return anonymous_id

    def track_usage(self, event_type: str, metadata: dict):
        if not self._is_opted_in():
            return

        data = {
            "anonymous_id": self.anonymous_id,
            "event_type": event_type,
            "timestamp": time.time(),
            "metadata": metadata
        }

        try:
            requests.post("https://analytics.example.com/track", json=data, timeout=5)
        except:
            pass  # Fail silently

    def _is_opted_in(self):
        config_file = Path.home() / ".config" / "pytest-drill-sergeant" / "config.json"
        if config_file.exists():
            config = json.loads(config_file.read_text())
            return config.get("analytics_opt_in", False)
        return False
```

### Error Reporting

#### Sentry Integration
```python
import sentry_sdk
from sentry_sdk.integrations.pytest import PytestIntegration

def setup_error_reporting():
    sentry_sdk.init(
        dsn="https://your-sentry-dsn@sentry.io/project-id",
        integrations=[PytestIntegration()],
        traces_sample_rate=0.1,
        environment="production"
    )
```

## Security Considerations

### Package Security

#### Code Signing
```bash
# Sign package with GPG
gpg --detach-sign --armor dist/pytest_drill_sergeant-1.0.0-py3-none-any.whl

# Verify signature
gpg --verify pytest_drill_sergeant-1.0.0-py3-none-any.whl.asc
```

#### Dependency Scanning
```yaml
# .github/workflows/security.yml
name: Security

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  security:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Run Trivy vulnerability scanner
        uses: aquasecurity/trivy-action@master
        with:
          scan-type: 'fs'
          scan-ref: '.'
          format: 'sarif'
          output: 'trivy-results.sarif'

      - name: Upload Trivy scan results
        uses: github/codeql-action/upload-sarif@v3
        with:
          sarif_file: 'trivy-results.sarif'
```

### Access Control

#### PyPI API Tokens
- Use API tokens instead of passwords
- Rotate tokens regularly
- Use scoped tokens for specific projects
- Monitor token usage

#### GitHub Secrets
- Use least-privilege access
- Rotate secrets regularly
- Monitor secret usage
- Use environment-specific secrets

## Rollback Procedures

### Package Rollback
```bash
# 1. Identify problematic version
pip index versions pytest-drill-sergeant

# 2. Downgrade to previous version
pip install pytest-drill-sergeant==0.9.0

# 3. Verify functionality
pytest --ds-mode=advisory

# 4. Communicate to users
# Update documentation and issue announcements
```

### CI/CD Rollback
```bash
# 1. Revert to previous workflow
git revert <commit-hash>

# 2. Push changes
git push origin main

# 3. Monitor deployment
# Check CI/CD pipeline status

# 4. Verify functionality
# Run tests and quality checks
```

## Maintenance

### Regular Tasks
- Update dependencies monthly
- Review security advisories weekly
- Monitor package download statistics
- Respond to issues and PRs promptly
- Update documentation as needed

### Version Management
- Follow semantic versioning
- Maintain changelog
- Tag releases properly
- Communicate breaking changes
- Provide migration guides

### Community Management
- Respond to issues within 48 hours
- Review PRs within 1 week
- Maintain code of conduct
- Encourage contributions
- Recognize contributors
