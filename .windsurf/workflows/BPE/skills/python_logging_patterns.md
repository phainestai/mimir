# Skill: Python Logging Patterns

**Capability Domain**: LOGGING_PATTERN
**Technology Stack**: Python

## Overview

Comprehensive logging patterns for Python applications with emphasis on informative, structured logging at appropriate levels. Enables effective troubleshooting by logging who, what, why, where, and when for every significant operation.

## Reference Implementation

### Pattern 1: Application Logger Setup

```python
# mimir/logging_config.py
import logging
import logging.handlers
from pathlib import Path

def setup_logging():
    """Configure application logging with file rotation."""
    # Create logs directory
    log_dir = Path('logs')
    log_dir.mkdir(exist_ok=True)
    
    # Configure root logger
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    
    # File handler with rotation
    file_handler = logging.handlers.RotatingFileHandler(
        'logs/app.log',
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5
    )
    file_handler.setLevel(logging.INFO)
    
    # Detailed format for file logs
    file_formatter = logging.Formatter(
        '[%(asctime)s] [%(levelname)s] [%(name)s:%(funcName)s:%(lineno)d] '
        '[PID:%(process)d:TID:%(thread)d] %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    file_handler.setFormatter(file_formatter)
    
    # Console handler (simpler format)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.WARNING)
    console_formatter = logging.Formatter(
        '[%(levelname)s] %(name)s: %(message)s'
    )
    console_handler.setFormatter(console_formatter)
    
    # Add handlers
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger
```

### Pattern 2: Service Method Logging

```python
# methodology/services/playbook_service.py
import logging
from django.core.exceptions import ValidationError

logger = logging.getLogger(__name__)

class PlaybookService:
    """Business logic for playbook management."""
    
    @staticmethod
    def create_playbook(name: str, description: str, category: str, author):
        """
        Create a new playbook.
        
        :param name: Playbook name as str. Example: "React Development"
        :param description: Description as str. Example: "Modern React patterns"
        :param category: Category as str. Example: "development"
        :param author: User instance. Example: User(id=1, username="maria")
        :return: Created Playbook instance
        :raises ValidationError: If validation fails
        """
        # Entry logging with context
        logger.info(
            f"Creating playbook: name={name!r}, category={category!r}, "
            f"author={author.username} (id={author.id})"
        )
        
        # Validation with logging
        if not name or not name.strip():
            logger.warning(
                f"Playbook creation failed: empty name provided by user {author.username}"
            )
            raise ValidationError("Playbook name cannot be empty")
        
        # Check for duplicates
        if Playbook.objects.filter(name=name, author=author).exists():
            logger.warning(
                f"Playbook creation failed: duplicate name {name!r} "
                f"for user {author.username}"
            )
            raise ValidationError(f"Playbook '{name}' already exists")
        
        # Create playbook
        try:
            playbook = Playbook.objects.create(
                name=name,
                description=description,
                category=category,
                author=author,
                version=Decimal('0.1'),
                status='draft'
            )
            
            # Success logging with result
            logger.info(
                f"Playbook created successfully: id={playbook.id}, "
                f"name={playbook.name!r}, version={playbook.version}, "
                f"author={author.username}"
            )
            
            return playbook
            
        except Exception as e:
            # Error logging with full context
            logger.error(
                f"Playbook creation failed with exception: {type(e).__name__}: {e}. "
                f"Context: name={name!r}, category={category!r}, "
                f"author={author.username} (id={author.id})",
                exc_info=True
            )
            raise
```

### Pattern 3: View Logging

```python
# methodology/views.py
import logging
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages

logger = logging.getLogger(__name__)

@login_required
def playbook_create(request):
    """Create new playbook."""
    logger.info(
        f"Playbook create view accessed by user {request.user.username} "
        f"(id={request.user.id}), method={request.method}"
    )
    
    if request.method == 'POST':
        # Log form submission
        logger.info(
            f"Playbook create form submitted by {request.user.username}. "
            f"Data: name={request.POST.get('name')!r}, "
            f"category={request.POST.get('category')!r}"
        )
        
        service = PlaybookService()
        try:
            playbook = service.create_playbook(
                name=request.POST['name'],
                description=request.POST.get('description', ''),
                category=request.POST['category'],
                author=request.user
            )
            
            logger.info(
                f"Playbook created via web UI: id={playbook.id}, "
                f"redirecting to detail page"
            )
            messages.success(request, f'Playbook "{playbook.name}" created')
            return redirect('playbook_detail', playbook_id=playbook.id)
            
        except ValidationError as e:
            logger.warning(
                f"Playbook creation validation error for user {request.user.username}: {e}"
            )
            messages.error(request, str(e))
    
    return render(request, 'playbooks/create.html')
```

### Pattern 4: Conditional Logic Logging

```python
def process_workflow(workflow_id: int, user):
    """Process workflow with detailed decision logging."""
    logger.info(
        f"Processing workflow: id={workflow_id}, user={user.username}"
    )
    
    workflow = Workflow.objects.get(id=workflow_id)
    
    # Log decision points
    if workflow.status == 'draft':
        logger.info(
            f"Workflow {workflow_id} is in draft status, "
            f"allowing modifications"
        )
        can_modify = True
    elif workflow.status == 'released':
        logger.info(
            f"Workflow {workflow_id} is released, "
            f"modifications require PIP"
        )
        can_modify = False
    else:
        logger.warning(
            f"Workflow {workflow_id} has unexpected status: {workflow.status}"
        )
        can_modify = False
    
    # Log data transformations
    activities = workflow.activities.all()
    logger.debug(
        f"Loaded {activities.count()} activities for workflow {workflow_id}"
    )
    
    # Log results
    logger.info(
        f"Workflow processing complete: id={workflow_id}, "
        f"can_modify={can_modify}, activity_count={activities.count()}"
    )
    
    return can_modify, activities
```

### Pattern 5: Error Context Logging

```python
def import_workflow_data(file_path: str, user):
    """Import workflow with comprehensive error logging."""
    logger.info(
        f"Starting workflow import: file={file_path}, user={user.username}"
    )
    
    try:
        # Validate file exists
        if not Path(file_path).exists():
            logger.error(
                f"Workflow import failed: file not found. "
                f"Path: {file_path}, user: {user.username}"
            )
            raise FileNotFoundError(f"File not found: {file_path}")
        
        # Parse file
        logger.debug(f"Parsing workflow file: {file_path}")
        with open(file_path, 'r') as f:
            data = json.load(f)
        
        logger.info(
            f"Workflow file parsed successfully: "
            f"{len(data.get('activities', []))} activities found"
        )
        
        # Import activities
        for idx, activity_data in enumerate(data.get('activities', [])):
            logger.debug(
                f"Importing activity {idx+1}: name={activity_data.get('name')!r}"
            )
            # ... import logic ...
        
        logger.info(
            f"Workflow import completed successfully: "
            f"file={file_path}, activities_imported={len(data.get('activities', []))}"
        )
        
    except json.JSONDecodeError as e:
        logger.error(
            f"Workflow import failed: invalid JSON. "
            f"File: {file_path}, error: {e}, line: {e.lineno}, col: {e.colno}",
            exc_info=True
        )
        raise
    except Exception as e:
        logger.error(
            f"Workflow import failed with unexpected error: {type(e).__name__}: {e}. "
            f"File: {file_path}, user: {user.username}",
            exc_info=True
        )
        raise
```

## Common Pitfalls

### ❌ Don't: Log without context
```python
logger.info("Creating playbook")
logger.error("Failed")
```

### ✅ Do: Log with full context
```python
logger.info(
    f"Creating playbook: name={name!r}, category={category!r}, "
    f"author={author.username} (id={author.id})"
)
logger.error(
    f"Playbook creation failed: {e}. Context: name={name!r}, "
    f"author={author.username}",
    exc_info=True
)
```

### ❌ Don't: Use print statements
```python
print(f"User {user.username} logged in")
```

### ✅ Do: Use logger
```python
logger.info(f"User {user.username} (id={user.id}) logged in successfully")
```

### ❌ Don't: Log sensitive data
```python
logger.info(f"User login: password={password}")  # NEVER!
```

### ✅ Do: Mask sensitive data
```python
logger.info(f"User login attempt: username={username}, password=***")
```

## Quality Gates

Before declaring logging complete:

- [ ] All service methods log entry with parameters
- [ ] All service methods log exit with results
- [ ] All errors logged with full context and exc_info=True
- [ ] All decision points logged (if/else branches)
- [ ] All data transformations logged
- [ ] No sensitive data (passwords, tokens) in logs
- [ ] User context included (username, user_id)
- [ ] Operation context included (what, why, when)
- [ ] Log levels appropriate (DEBUG/INFO/WARNING/ERROR)
- [ ] File handler configured with rotation

## Log Level Guidelines

### DEBUG
- Detailed flow control
- Type checking
- Internal state
- Loop iterations
- Data structure contents

### INFO
- Method entry/exit
- Configuration loaded
- Major processing steps
- Results and outcomes
- User actions

### WARNING
- Concerning but recoverable conditions
- Substitutions and fallbacks
- Fallback usage
- Data quality issues
- Deprecated feature usage

### ERROR
- Failures requiring attention
- Unrecoverable conditions
- Exceptions
- Data corruption
- External service failures

## Informative Logging Checklist

Every log message should answer:

- **Who**: Which user/agent triggered the action?
- **What**: What operation was performed?
- **Why**: Why did it happen (intent, rule, logic)?
- **Where**: Which class/method/line?
- **When**: Timestamp (automatic)
- **How**: With what parameters/data?
- **Result**: What was the outcome?

## Example: Complete Logging Pattern

```python
import logging

logger = logging.getLogger(__name__)

class WorkflowService:
    @staticmethod
    def update_workflow(workflow_id: int, updates: dict, user):
        """
        Update workflow with comprehensive logging.
        
        :param workflow_id: Workflow ID. Example: 42
        :param updates: Field updates. Example: {"name": "New Name"}
        :param user: User making changes. Example: User(id=1)
        :return: Updated workflow
        """
        # Entry logging
        logger.info(
            f"Updating workflow: id={workflow_id}, "
            f"fields={list(updates.keys())}, "
            f"user={user.username} (id={user.id})"
        )
        
        try:
            # Fetch workflow
            workflow = Workflow.objects.get(id=workflow_id)
            logger.debug(
                f"Workflow loaded: id={workflow_id}, "
                f"current_name={workflow.name!r}, "
                f"status={workflow.status}"
            )
            
            # Validate permissions
            if workflow.playbook.author != user:
                logger.warning(
                    f"Workflow update denied: user {user.username} "
                    f"not authorized for workflow {workflow_id}"
                )
                raise PermissionError("Not authorized")
            
            # Apply updates
            for field, value in updates.items():
                old_value = getattr(workflow, field)
                setattr(workflow, field, value)
                logger.info(
                    f"Workflow {workflow_id} field updated: "
                    f"{field}: {old_value!r} -> {value!r}"
                )
            
            workflow.save()
            
            # Success logging
            logger.info(
                f"Workflow updated successfully: id={workflow_id}, "
                f"updated_fields={list(updates.keys())}, "
                f"user={user.username}"
            )
            
            return workflow
            
        except Workflow.DoesNotExist:
            logger.error(
                f"Workflow update failed: workflow not found. "
                f"id={workflow_id}, user={user.username}"
            )
            raise
        except Exception as e:
            logger.error(
                f"Workflow update failed: {type(e).__name__}: {e}. "
                f"Context: id={workflow_id}, updates={updates}, "
                f"user={user.username}",
                exc_info=True
            )
            raise
```
