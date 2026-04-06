# Activity: Initialize Runtimes & Dependencies

**Activity ID**: TBD
**Order**: 4
**Phase**: Initialize
**Dependencies**: Predecessor: BSP-03 (Scaffold Project Structure)

## Description

Initialize Runtimes & Dependencies

## Guidance

# Initialize Runtimes & Dependencies

## Objective

Set up language runtimes (Python venv, Node.js) and install project dependencies via their respective package managers. Create dependency manifest files (`requirements.txt`, `package.json`) with pinned versions from the SAO.md Technology Stack Table.

---

## Process

### 1. Python Runtime

```bash
# Create virtual environment
python3 -m venv .venv

# Activate (for current session)
source .venv/bin/activate

# Upgrade pip
pip install --upgrade pip

# Create requirements.txt from SAO.md Technology Stack Table
cat > requirements.txt << 'EOF'
# Core framework
django>=5.1,<6.0

# Testing
pytest>=8.0
pytest-django>=4.8

# Code quality
ruff>=0.6

# Logging
# (add based on DTA-12 Observability decisions)

# Add all Python dependencies from SAO.md stack table here
EOF

# Install
pip install -r requirements.txt
```

### 2. Django Project Initialization (if Django is chosen)

```bash
# Create Django project (only if manage.py doesn't exist)
django-admin startproject config .

# This creates:
#   config/
#   ├── __init__.py
#   ├── settings.py
#   ├── urls.py
#   ├── asgi.py
#   └── wsgi.py
#   manage.py
```

Adjust `config/settings.py`:
- Set `ALLOWED_HOSTS`
- Configure `DATABASES` per DTA-05 decisions
- Configure `STATIC_URL`, `STATICFILES_DIRS`
- Configure logging per DTA-12 decisions
- Set `SECRET_KEY` handling per DTA-13 decisions

### 3. Node.js Runtime (if applicable)

```bash
# Initialize package.json
npm init -y

# Install frontend dependencies from SAO.md
npm install --save-dev \
    playwright \
    # Add based on stack decisions

# Create .nvmrc for Node version pinning
echo "20" > .nvmrc
```

### 4. Pytest Configuration

Create `pytest.ini` or add to `pyproject.toml`:

```ini
[tool.pytest.ini_options]
DJANGO_SETTINGS_MODULE = "config.settings"
python_files = ["tests.py", "test_*.py", "*_tests.py"]
python_paths = ["."]
addopts = "-v --tb=short"
log_cli = true
log_file = "tests.log"
log_file_level = "INFO"
```

### 5. Create pyproject.toml (if not exists)

Consolidate Python tool configuration:

```toml
[project]
name = "{project-name}"
version = "0.1.0"
requires-python = ">=3.12"

[tool.ruff]
line-length = 120
target-version = "py312"

[tool.ruff.lint]
select = ["E", "F", "I", "N", "W"]

[tool.pytest.ini_options]
DJANGO_SETTINGS_MODULE = "config.settings"
addopts = "-v --tb=short"
log_file = "tests.log"
```

### 6. Commit Dependencies

```bash
git add .
git commit -m "chore(deps): initialize Python venv, requirements.txt, Django project, pytest config"
```

---

## Deliverables

- ✅ **Python venv** created at `.venv/`
- ✅ **requirements.txt** created with pinned versions from SAO.md
- ✅ **Django project** initialized (if applicable)
- ✅ **package.json** created (if Node.js in stack)
- ✅ **pyproject.toml** created with tool configuration
- ✅ **All dependencies** installed and verified
- ✅ **Dependencies committed**

## Artifacts Produced

- `.venv/` (gitignored)
- `requirements.txt`
- `manage.py` (if Django)
- `config/` settings directory (if Django)
- `package.json` (if Node.js)
- `.nvmrc` (if Node.js)
- `pyproject.toml`

## Artifacts Consumed

- `docs/architecture/SAO.md` — Technology Stack Table
- `docs/architecture/SAO.md` — § Data Architecture (DTA-05) for DB config
- `docs/architecture/SAO.md` — § Observability (DTA-12) for logging config
- `docs/architecture/SAO.md` — § Config & Secrets (DTA-13) for SECRET_KEY handling

## Notes

The virtual environment `.venv/` is gitignored. Developers recreate it via `make provision` which runs `pip install -r requirements.txt`.
