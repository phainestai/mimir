# Activity: Create Welcome Page & Verify

**Activity ID**: TBD
**Order**: 7
**Phase**: Verify
**Dependencies**: Predecessor: BSP-06 (Create Makefile)

## Description

Create Welcome Page & Verify

## Guidance

# Create Welcome Page & Verify

## Objective

Create a basic health-check welcome page that displays application health status, verify `make provision` works end-to-end, and confirm F5 (debug launch) shows the welcome page in the browser.

---

## Process

### 1. Create Health Check View

Create a simple view that shows system health:

```python
# {app}/views/health.py
import sys
import django
import platform
from datetime import datetime
from django.http import JsonResponse
from django.shortcuts import render

def health_json(request):
    """JSON health endpoint for monitoring."""
    return JsonResponse({
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "python_version": sys.version,
        "django_version": django.__version__,
        "platform": platform.platform(),
    })

def welcome(request):
    """Welcome page showing app health dashboard."""
    context = {
        "status": "healthy",
        "timestamp": datetime.now(),
        "python_version": sys.version.split()[0],
        "django_version": django.__version__,
        "platform": platform.platform(),
        "checks": _run_health_checks(),
    }
    return render(request, "welcome.html", context)

def _run_health_checks():
    """Run basic health checks and return results."""
    checks = []

    # Database check
    try:
        from django.db import connection
        connection.ensure_connection()
        checks.append({"name": "Database", "status": "✅", "detail": "Connected"})
    except Exception as e:
        checks.append({"name": "Database", "status": "❌", "detail": str(e)})

    # Static files check
    import os
    static_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static")
    if os.path.isdir(static_dir):
        checks.append({"name": "Static Files", "status": "✅", "detail": "Directory exists"})
    else:
        checks.append({"name": "Static Files", "status": "⚠️", "detail": "Directory missing"})

    # Logging check
    log_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "logs")
    if os.path.isdir(log_dir):
        checks.append({"name": "Logging", "status": "✅", "detail": "Log directory exists"})
    else:
        checks.append({"name": "Logging", "status": "⚠️", "detail": "Log directory missing"})

    return checks
```

### 2. Create Welcome Template

```html
<!-- templates/welcome.html -->
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ project_name }} — Welcome</title>
    <style>
        /* Minimal inline CSS — no external dependencies needed at bootstrap */
        body { font-family: -apple-system, system-ui, sans-serif; max-width: 800px; margin: 40px auto; padding: 0 20px; color: #333; }
        h1 { color: #2563eb; }
        .status { display: inline-block; padding: 4px 12px; border-radius: 12px; font-size: 14px; font-weight: 600; }
        .status.healthy { background: #dcfce7; color: #166534; }
        .checks { margin-top: 20px; }
        .check { display: flex; justify-content: space-between; padding: 8px 0; border-bottom: 1px solid #e5e7eb; }
        .meta { color: #6b7280; font-size: 14px; margin-top: 20px; }
        table { width: 100%; border-collapse: collapse; margin-top: 12px; }
        td, th { text-align: left; padding: 8px; border-bottom: 1px solid #e5e7eb; }
    </style>
</head>
<body>
    <h1>🚀 {{ project_name }}</h1>
    <p>Application is running. <span class="status healthy">{{ status }}</span></p>

    <h2>Health Checks</h2>
    <table>
        <tr><th>Component</th><th>Status</th><th>Detail</th></tr>
        {% for check in checks %}
        <tr>
            <td>{{ check.name }}</td>
            <td>{{ check.status }}</td>
            <td>{{ check.detail }}</td>
        </tr>
        {% endfor %}
    </table>

    <div class="meta">
        <p>Python {{ python_version }} · Django {{ django_version }}</p>
        <p>{{ platform }}</p>
        <p>{{ timestamp }}</p>
    </div>
</body>
</html>
```

### 3. Wire Up URLs

```python
# config/urls.py
from django.urls import path
from {app}.views.health import welcome, health_json

urlpatterns = [
    path("", welcome, name="welcome"),
    path("health/", health_json, name="health-json"),
]
```

### 4. End-to-End Verification

Run the full bootstrap sequence and verify:

```bash
# 1. Provision from scratch
make provision
# Expected: all dependencies installed, DB migrated, no errors

# 2. Run the server
make run
# Expected: Django dev server starts on http://localhost:8000

# 3. Verify welcome page
# Open http://localhost:8000 in browser
# Expected: Welcome page showing "healthy" status with all checks ✅

# 4. Verify health JSON endpoint
curl http://localhost:8000/health/
# Expected: {"status": "healthy", "python_version": "...", ...}

# 5. Verify F5 debug launch
# Press F5 in IDE → Django server starts under debugger
# Breakpoints work, can inspect variables

# 6. Run tests (should pass even if 0 tests)
make test
# Expected: no failures

# 7. Run linter
make lint
# Expected: clean or only style warnings
```

### 5. Final Commit

```bash
git add .
git commit -m "feat(bootstrap): add welcome page with health checks, wire up URLs

Bootstrap verification complete:
- make provision ✅
- make run ✅
- F5 debug launch ✅
- Welcome page at / with health dashboard
- JSON health endpoint at /health/"
```

---

## Deliverables

- ✅ **Welcome page** showing app health status at `/`
- ✅ **Health JSON endpoint** at `/health/`
- ✅ **`make provision`** completes without errors
- ✅ **`make run`** starts server, welcome page visible
- ✅ **F5 debug launch** works in IDE
- ✅ **`make test`** runs without failures
- ✅ **`make lint`** runs cleanly
- ✅ **Final commit** with verification results

## Artifacts Produced

- Health check view (`{app}/views/health.py`)
- Welcome template (`templates/welcome.html`)
- URL configuration update (`config/urls.py`)

## Artifacts Consumed

- All previous BSP artifacts (Makefile, project structure, dependencies, tooling)
- `docs/architecture/SAO.md` — for project name and stack details

## Notes

This is the final BSP activity. After verification passes, the project is bootstrapped and ready for Elaboration phase — pick the first feature from the backlog and start building with the BPE (Build Feature) workflow.
