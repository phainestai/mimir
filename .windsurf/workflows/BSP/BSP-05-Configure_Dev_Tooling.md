# Activity: Configure Dev Tooling

**Activity ID**: TBD
**Order**: 5
**Phase**: Configure
**Dependencies**: Predecessor: BSP-04 (Initialize Runtimes & Dependencies)

## Description

Configure Dev Tooling

## Guidance

# Configure Dev Tooling

## Objective

Set up linters, formatters, pre-commit hooks, IDE settings, and debug configurations as defined in DTA-16 (Developer Experience).

---

## Process

### 1. Pre-commit Hooks

```bash
# Install pre-commit
pip install pre-commit

# Create .pre-commit-config.yaml
cat > .pre-commit-config.yaml << 'EOF'
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.6.0
    hooks:
      - id: ruff
        args: [--fix]
      - id: ruff-format
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.6.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-added-large-files
      - id: check-merge-conflict
EOF

# Install hooks
pre-commit install
```

### 2. IDE Settings (VS Code / Windsurf / Cursor)

```bash
mkdir -p .vscode

# Settings
cat > .vscode/settings.json << 'EOF'
{
    "python.defaultInterpreterPath": ".venv/bin/python",
    "python.analysis.typeCheckingMode": "basic",
    "[python]": {
        "editor.defaultFormatter": "charliermarsh.ruff",
        "editor.formatOnSave": true,
        "editor.codeActionsOnSave": {
            "source.fixAll": "explicit",
            "source.organizeImports": "explicit"
        }
    },
    "files.exclude": {
        "**/__pycache__": true,
        "**/*.pyc": true,
        ".venv": true,
        "node_modules": true
    },
    "editor.rulers": [120]
}
EOF

# Extensions recommendations
cat > .vscode/extensions.json << 'EOF'
{
    "recommendations": [
        "charliermarsh.ruff",
        "ms-python.python",
        "ms-python.debugpy",
        "batisteo.vscode-django",
        "firefox-devtools.vscode-firefox-debug"
    ]
}
EOF
```

### 3. Debug Configurations

```bash
cat > .vscode/launch.json << 'EOF'
{
    "version": "0.2.0",
    "configurations": [
        {
            "name": "Django: Run Server",
            "type": "debugpy",
            "request": "launch",
            "program": "${workspaceFolder}/manage.py",
            "args": ["runserver", "0.0.0.0:8000"],
            "django": true,
            "justMyCode": false
        },
        {
            "name": "Pytest: Current File",
            "type": "debugpy",
            "request": "launch",
            "module": "pytest",
            "args": ["${file}", "-v", "--tb=short"],
            "justMyCode": false
        },
        {
            "name": "Pytest: All Tests",
            "type": "debugpy",
            "request": "launch",
            "module": "pytest",
            "args": ["tests/", "-v", "--tb=short"],
            "justMyCode": false
        }
    ]
}
EOF
```

### 4. EditorConfig

```bash
cat > .editorconfig << 'EOF'
root = true

[*]
indent_style = space
indent_size = 4
end_of_line = lf
charset = utf-8
trim_trailing_whitespace = true
insert_final_newline = true

[*.{js,jsx,ts,tsx,json,yml,yaml,html,css}]
indent_size = 2

[Makefile]
indent_style = tab
EOF
```

### 5. Commit Tooling Config

```bash
git add .
git commit -m "chore(tooling): configure linter, formatter, pre-commit, IDE settings, debug configs"
```

---

## Deliverables

- ✅ **Pre-commit hooks** installed and configured
- ✅ **VS Code settings** configured (formatter, linter, interpreter)
- ✅ **Debug configurations** created (Django server, pytest)
- ✅ **EditorConfig** created for consistent formatting
- ✅ **IDE extension recommendations** added
- ✅ **Tooling committed**

## Artifacts Produced

- `.pre-commit-config.yaml`
- `.vscode/settings.json`
- `.vscode/extensions.json`
- `.vscode/launch.json`
- `.editorconfig`

## Artifacts Consumed

- `docs/architecture/SAO.md` — § Developer Experience (DTA-16)
- `docs/architecture/SAO.md` — § Code Organization (DTA-04) for line length, style conventions

## Notes

Debug configurations assume Django. Adjust the `launch.json` if a different framework was chosen in DTA-02.
