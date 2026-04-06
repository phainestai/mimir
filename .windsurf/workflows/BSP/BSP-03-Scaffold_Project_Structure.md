# Activity: Scaffold Project Structure

**Activity ID**: TBD
**Order**: 3
**Phase**: Initialize
**Dependencies**: Predecessor: BSP-02 (Initialize Repository)

## Description

Scaffold Project Structure

## Guidance

# Scaffold Project Structure

## Objective

Create the directory tree as defined in DTA-04 (Code Organization). This includes all top-level directories, app directories, placeholder files, and `__init__.py` files where needed.

---

## Process

### 1. Read DTA-04 Decisions

From SAO.md § Code Organization, extract:
- Repository strategy (monorepo/polyrepo)
- Directory structure with layer separation
- App/module names from DTA-02 (Application Blocks)

### 2. Create Directory Tree

Example for a Django project:

```bash
mkdir -p {app_name}/{models,services,views,templates/{app_name}}
mkdir -p tests/{unit,integration,e2e}
mkdir -p docs/{architecture,process,features,ux,runbooks}
mkdir -p logs
mkdir -p static/{css,js,img}
mkdir -p scripts
```

### 3. Create Placeholder Files

For each directory, create the minimum files needed so the structure is functional:

```bash
# Python packages need __init__.py
touch {app_name}/__init__.py
touch {app_name}/models/__init__.py
touch {app_name}/services/__init__.py
touch {app_name}/views/__init__.py
touch tests/__init__.py
touch tests/unit/__init__.py
touch tests/integration/__init__.py
touch tests/e2e/__init__.py

# Keep empty directories in Git
touch logs/.gitkeep
touch static/css/.gitkeep
touch static/js/.gitkeep
touch static/img/.gitkeep
touch docs/runbooks/.gitkeep
```

### 4. Create docs/ Placeholder Structure

```bash
# Architecture docs (from DTA)
touch docs/architecture/.gitkeep
# Process docs (from DSP)
touch docs/process/.gitkeep
# Feature files (from ESM)
touch docs/features/.gitkeep
# UX artifacts (from ESM)
touch docs/ux/.gitkeep
```

### 5. Commit Scaffold

```bash
git add .
git commit -m "chore(scaffold): create project directory structure per DTA-04"
```

---

## Deliverables

- ✅ **Directory tree** created per DTA-04 decisions
- ✅ **App packages** initialized with `__init__.py`
- ✅ **Test directory** structure created (unit/integration/e2e)
- ✅ **Docs directory** structure created
- ✅ **Static assets** directories created
- ✅ **Scaffold committed**

## Artifacts Produced

- Complete directory tree with placeholder files

## Artifacts Consumed

- `docs/architecture/SAO.md` — § Code Organization (DTA-04)
- `docs/architecture/SAO.md` — § Application Blocks (DTA-02)

## Notes

The exact directory names and structure depend on DTA-02 and DTA-04 decisions. The example above assumes Django — adjust for the actual framework chosen.
