# Activity: Configure Observability & Logging

**Activity ID**: 95
**Order**: 8
**Phase**: Elaboration
**Dependencies**: None

## Description

Configure Observability & Logging

## Guidance

# Configure Observability & Logging

## Objective

Set up three-tier logging infrastructure for backend operations (`logs/app.log`), frontend interactions (`logs/gui.log`), and AI token consumption (`logs/consumption.log`). This provides observability from day one and enables EST workflow token tracking for estimate calibration.

---

## Prerequisites

- BSP-07 complete (welcome page verified)
- Project structure exists
- Django settings configured
- Static files directory exists

---

## Goals

### Goal 1: Backend Operation Logging

**What**: All backend operations log to `logs/app.log` with informative context

**Why**: Enable troubleshooting without reproduction by logging who, what, where, when, and why for every significant operation

**Success Criteria**:
- [ ] Django LOGGING configuration added to settings
- [ ] RotatingFileHandler configured (10MB, 5 backups)
- [ ] Log format includes module, function, line number, and context
- [ ] All service methods log entry, exit, and errors
- [ ] Log messages follow informative logging pattern (who, what, where, when, why)

**Implementation**: See Skill **Django Logging Setup**

---

### Goal 2: Frontend Interaction Logging

**What**: All HTMX interactions and user actions log to `logs/gui.log`

**Why**: Track user behavior, debug frontend issues, and understand interaction patterns

**Success Criteria**:
- [ ] JavaScript Logger class created in `static/js/logger.js`
- [ ] HTMX event listeners configured (beforeRequest, afterRequest, responseError)
- [ ] Django backend endpoint created (`/api/log/gui/`)
- [ ] Frontend logs sent to backend for persistence
- [ ] Console integration for development debugging

**Implementation**: See Skill **HTMX Frontend Logging**

---

### Goal 3: Token Consumption Tracking

**What**: AI token usage logged to `logs/consumption.log` in JSON format

**Why**: Enable EST workflow sprint-by-sprint calibration via velocity factor calculation and K-token baseline updates

**Success Criteria**:
- [ ] TokenTracker utility class created
- [ ] Scenario-level token tracking implemented
- [ ] JSON log format compatible with EST-08 Sprint Close & Rebaseline
- [ ] Consumption logger configured with JSON formatter
- [ ] Sprint report generation utility available

**Implementation**: See Skill **Claude Token Tracking**

---

## Implementation Steps

### Step 1: Create Logs Directory Structure

```bash
mkdir -p logs
touch logs/.gitkeep

# Add logs to .gitignore (keep structure, ignore content)
cat >> .gitignore << 'EOF'

# Logs
logs/*.log
!logs/.gitkeep
EOF
```

**Deliverable**: `logs/` directory with `.gitkeep`, `.gitignore` updated

---

### Step 2: Configure Backend Logging

**Objective**: Add Django LOGGING configuration for three log files

**Tasks**:
1. Add LOGGING dictionary to `{project_name}/settings.py`
2. Configure formatters (verbose, simple, json)
3. Configure handlers (app_file, gui_file, consumption_file, console)
4. Configure loggers (django, {project_name}, gui, consumption)
5. Add informative logging to service methods

**Reference**: See Skill **Django Logging Setup** for:
- Complete LOGGING configuration
- RotatingFileHandler setup
- Logger usage patterns in services, views, models
- Informative logging message format
- Testing logging configuration

**Deliverable**: Django LOGGING configured, backend operations logging to `app.log`

---

### Step 3: Configure Frontend Logging

**Objective**: Create JavaScript logger and backend endpoint for GUI events

**Tasks**:
1. Create `static/js/logger.js` with Logger class
2. Add HTMX event listeners (beforeRequest, afterRequest, responseError, etc.)
3. Create Django view `{app_name}/views/logging_views.py::log_gui_event`
4. Add URL route `/api/log/gui/`
5. Include logger in `templates/base.html`
6. Test frontend logging in browser console

**Reference**: See Skill **HTMX Frontend Logging** for:
- JavaScript Logger class implementation
- HTMX event logging patterns
- Django backend endpoint
- User action logging
- JavaScript error catching
- Performance considerations (throttling, batching)

**Deliverable**: Frontend interactions logging to `gui.log`

---

### Step 4: Configure Token Consumption Tracking

**Objective**: Create TokenTracker utility for EST workflow integration

**Tasks**:
1. Create `{app_name}/utils/token_tracker.py` with TokenTracker class
2. Add consumption logger to Django settings (JSON formatter)
3. Create utility functions for parsing consumption.log
4. Create Django management command for sprint reports
5. Document integration with BPE workflow

**Reference**: See Skill **Claude Token Tracking** for:
- TokenTracker class implementation
- JSON log format for EST-08
- Parsing and aggregation utilities
- Sprint report generation
- Integration with Claude API
- Velocity factor calculation

**Deliverable**: Token consumption logging to `consumption.log` in EST-compatible format

---

### Step 5: Verify All Logs Are Working

**Verification Checklist**:

1. **Backend Logging**:
   ```bash
   # Start Django server
   python manage.py runserver
   
   # Trigger some operations (create, read, update)
   # Check logs/app.log for entries
   tail -f logs/app.log
   ```

2. **Frontend Logging**:
   ```bash
   # Open browser to http://localhost:8000
   # Open browser console (F12)
   # Click buttons, submit forms
   # Verify console shows log messages
   # Check logs/gui.log for persisted entries
   tail -f logs/gui.log
   ```

3. **Token Consumption**:
   ```python
   # In Django shell
   from {app_name}.utils.token_tracker import log_token_consumption
   
   log_token_consumption(
       scenario_id="TEST-01",
       user_id=1,
       tokens_used=1000,
       model="claude-3-5-sonnet-20241022",
       sprint=1
   )
   ```
   ```bash
   # Check logs/consumption.log
   cat logs/consumption.log
   # Should show JSON entry
   ```

4. **Log Rotation**:
   ```bash
   # Verify file size limits
   ls -lh logs/
   # Should show maxBytes=10MB configured
   ```

**Deliverable**: All three logs verified and working

---

### Step 6: Commit Logging Infrastructure

```bash
git add logs/.gitkeep .gitignore
git add {project_name}/settings.py
git add static/js/logger.js
git add {app_name}/views/logging_views.py
git add {app_name}/utils/token_tracker.py
git add {app_name}/urls.py
git add templates/base.html

git commit -m "feat(observability): configure three-tier logging infrastructure

Add comprehensive logging for backend operations, frontend interactions,
and AI token consumption:

Backend (logs/app.log):
- Django LOGGING configuration with RotatingFileHandler
- Informative logging pattern (module:function:line + context)
- Logs for services, views, models, and signals

Frontend (logs/gui.log):
- JavaScript Logger class with console and backend integration
- HTMX event listeners for all interactions
- Django endpoint for GUI log collection
- User action and error logging

Token Consumption (logs/consumption.log):
- TokenTracker utility for scenario-level tracking
- JSON format compatible with EST-08 Sprint Close workflow
- Parsing and aggregation utilities
- Sprint report generation command

Enables:
- Troubleshooting without reproduction
- User behavior analysis
- EST workflow token calibration

Refs: Activity EST-08 (Sprint Close and Rebaseline)"
```

**Deliverable**: Logging infrastructure committed to repository

---

## Success Criteria

- [x] **Logs directory** created with `.gitkeep`
- [x] **`.gitignore`** updated to exclude `logs/*.log`
- [x] **Backend logging** configured in Django settings
- [x] **app.log** receiving backend operation logs
- [x] **gui.log** receiving frontend interaction logs
- [x] **consumption.log** receiving token consumption in JSON format
- [x] **Log rotation** configured (10MB, 5 backups)
- [x] **Informative logging** pattern followed (module:function:line + context)
- [x] **JavaScript Logger** created and included in base template
- [x] **HTMX events** automatically logged
- [x] **TokenTracker** utility created
- [x] **All logs verified** and working
- [x] **Infrastructure committed** to repository

---

## Inputs

Read these before starting this activity. They are produced earlier in the playbook and are authoritative — raise a drift event instead of deviating.

- **System Architecture Overview Template** (Template, Required) — produced by Write SAO.md (#59).
- **Makefile Template** (Code, Required) — produced by Create Makefile (#93).

## Agent

None

## Skill

**Title**: Django Logging Setup
**Capability Domain**: BACKEND_LOGGING
**Technology Stack**: Django+Python

## Rules

- **Informative Logging** (`do-informative-logging`)

## Artifacts Produced

None

## Artifacts Consumed

- **System Architecture Overview Template** (Template) - Required
- **Makefile Template** (Code) - Required

## Notes

No additional notes.
