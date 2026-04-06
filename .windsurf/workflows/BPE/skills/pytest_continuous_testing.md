# Skill: pytest Continuous Testing

**Capability Domain**: TEST_FRAMEWORK
**Technology Stack**: pytest+Python

## Overview

Patterns for continuous testing with pytest, including automated test running, log monitoring, error detection, and automatic fixing. Ensures tests run continuously during development with real-time feedback.

## Reference Implementation

### Pattern 1: pytest Configuration

```ini
# pytest.ini
[pytest]
DJANGO_SETTINGS_MODULE = mimir.settings
python_files = test_*.py
python_classes = Test*
python_functions = test_*
testpaths = tests
addopts = 
    -v
    --strict-markers
    --tb=short
    --disable-warnings
    -p no:warnings
    --log-cli-level=INFO
    --log-file=tests.log
    --log-file-level=INFO
    --log-file-format=%(asctime)s [%(levelname)s] %(message)s
    --log-file-date-format=%Y-%m-%d %H:%M:%S

markers =
    unit: Unit tests
    integration: Integration tests
    e2e: End-to-end tests
    slow: Slow running tests
```

### Pattern 2: Continuous Test Runner Script

```python
# continuous_test_runner.py
import time
import subprocess
import sys
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

class TestRunner(FileSystemEventHandler):
    """Watch for file changes and run affected tests."""
    
    def __init__(self):
        self.last_run = 0
        self.debounce_seconds = 2
    
    def on_modified(self, event):
        """Run tests when Python files change."""
        if event.is_directory:
            return
        
        if not event.src_path.endswith('.py'):
            return
        
        # Debounce rapid changes
        current_time = time.time()
        if current_time - self.last_run < self.debounce_seconds:
            return
        
        self.last_run = current_time
        
        # Determine which tests to run
        file_path = Path(event.src_path)
        
        if 'tests/' in str(file_path):
            # Test file changed - run that test
            test_file = file_path
        else:
            # Source file changed - run related tests
            test_file = self.find_related_test(file_path)
        
        if test_file and test_file.exists():
            self.run_tests(test_file)
        else:
            # Run all tests if can't determine specific test
            self.run_tests()
    
    def find_related_test(self, source_file: Path) -> Path:
        """Find test file for source file."""
        # Example: methodology/services/playbook_service.py
        # -> tests/unit/test_playbook_service.py
        
        parts = source_file.parts
        if 'services' in parts:
            test_name = f"test_{source_file.stem}.py"
            return Path('tests/unit') / test_name
        elif 'views' in parts:
            test_name = f"test_{source_file.stem}.py"
            return Path('tests/integration') / test_name
        
        return None
    
    def run_tests(self, test_file: Path = None):
        """Run pytest with specified test file."""
        cmd = ['pytest']
        
        if test_file:
            cmd.append(str(test_file))
            print(f"\n{'='*60}")
            print(f"Running tests: {test_file}")
            print('='*60)
        else:
            cmd.append('tests/')
            print(f"\n{'='*60}")
            print("Running all tests")
            print('='*60)
        
        cmd.extend(['-v', '--tb=short'])
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        # Print output
        print(result.stdout)
        if result.stderr:
            print(result.stderr)
        
        # Parse for errors
        if result.returncode != 0:
            print(f"\n❌ Tests FAILED")
            self.analyze_failures(result.stdout)
        else:
            print(f"\n✅ All tests PASSED")
    
    def analyze_failures(self, output: str):
        """Analyze test failures and suggest fixes."""
        if 'FAILED' in output:
            print("\nFailed tests detected. Check tests.log for details.")
        
        if 'ImportError' in output:
            print("⚠️  Import errors detected - check dependencies")
        
        if 'AssertionError' in output:
            print("⚠️  Assertion failures - check test expectations")

def main():
    """Start continuous test runner."""
    print("Starting continuous test runner...")
    print("Watching for changes in Python files...")
    print("Press Ctrl+C to stop\n")
    
    # Initial test run
    runner = TestRunner()
    runner.run_tests()
    
    # Watch for changes
    observer = Observer()
    observer.schedule(runner, path='.', recursive=True)
    observer.start()
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
        print("\nStopping continuous test runner...")
    
    observer.join()

if __name__ == '__main__':
    main()
```

### Pattern 3: Running Tests

```bash
# Run all tests
pytest tests/

# Run specific test file
pytest tests/unit/test_playbook_service.py

# Run specific test class
pytest tests/unit/test_playbook_service.py::TestPlaybookService

# Run specific test method
pytest tests/unit/test_playbook_service.py::TestPlaybookService::test_create_playbook

# Run with coverage
pytest tests/ --cov=methodology --cov-report=html

# Run only unit tests
pytest tests/unit/ -v

# Run only integration tests
pytest tests/integration/ -v

# Run with markers
pytest -m unit
pytest -m "not slow"
```

### Pattern 4: Test Log Monitoring

```python
# monitor_tests.py
import time
from pathlib import Path

def monitor_test_log():
    """Monitor tests.log for errors and auto-fix."""
    log_file = Path('tests.log')
    
    if not log_file.exists():
        print("tests.log not found. Run tests first.")
        return
    
    print("Monitoring tests.log for errors...")
    
    with open(log_file, 'r') as f:
        # Read existing content
        f.seek(0, 2)  # Go to end
        
        while True:
            line = f.readline()
            if not line:
                time.sleep(0.1)
                continue
            
            # Parse for errors
            if 'FAILED' in line:
                print(f"❌ Test failure: {line.strip()}")
            elif 'ERROR' in line:
                print(f"⚠️  Error: {line.strip()}")
            elif 'PASSED' in line:
                print(f"✅ Test passed: {line.strip()}")

if __name__ == '__main__':
    monitor_test_log()
```

## Common Pitfalls

### ❌ Don't: Run tests manually every time
```bash
# Wrong - manual testing
pytest tests/
# ... make changes ...
pytest tests/
# ... make changes ...
pytest tests/
```

### ✅ Do: Use continuous test runner
```bash
# Correct - automated testing
python continuous_test_runner.py
# Tests run automatically on file changes
```

### ❌ Don't: Ignore failing tests
```bash
# Wrong - continuing with failures
pytest tests/  # 23/25 passed
# Continue development anyway
```

### ✅ Do: Fix tests immediately
```bash
# Correct - fix before continuing
pytest tests/  # 23/25 passed
# Fix the 2 failing tests
pytest tests/  # 25/25 passed ✅
# Now continue development
```

### ❌ Don't: Skip test logs
```bash
# Wrong - no logging
pytest tests/
```

### ✅ Do: Always log test output
```bash
# Correct - with logging
pytest tests/ --log-file=tests.log --log-file-level=INFO
```

## Quality Gates

Before declaring testing setup complete:

- [ ] pytest.ini configured with proper settings
- [ ] tests.log configured and rotating
- [ ] Continuous test runner script created
- [ ] File watcher monitoring source and test files
- [ ] Tests run automatically on file changes
- [ ] Test failures immediately visible
- [ ] Log monitoring active
- [ ] Coverage reporting configured
- [ ] Test markers defined (unit, integration, e2e)
- [ ] All tests passing (100% pass rate)

## Requirements

```txt
# requirements.txt (testing dependencies)
pytest>=8.0.0
pytest-django>=4.5.0
pytest-cov>=4.1.0
pytest-asyncio>=0.21.0
watchdog>=3.0.0  # For file watching
```

## Continuous Testing Workflow

1. **Start continuous runner**: `python continuous_test_runner.py`
2. **Make code changes**: Edit source files
3. **Tests run automatically**: Related tests execute
4. **Check output**: Green (pass) or red (fail)
5. **Fix failures immediately**: Don't continue with failing tests
6. **Monitor tests.log**: Check for patterns and issues
7. **Commit when green**: Only commit when all tests pass

## Test Organization

```
tests/
├── unit/                    # Fast, isolated tests
│   ├── test_playbook_service.py
│   ├── test_workflow_service.py
│   └── test_activity_service.py
├── integration/             # Real dependencies, no mocking
│   ├── test_playbook_views.py
│   ├── test_workflow_crud.py
│   └── test_activity_dependencies.py
├── e2e/                     # Full user journeys
│   ├── test_playbook_creation_journey.py
│   └── test_workflow_execution_journey.py
├── conftest.py              # Shared fixtures
└── __init__.py
```

## Key Principles

1. **Fast**: Unit tests run in <1s, integration in <5s
2. **Comprehensive**: Cover all scenarios from feature files
3. **No Mocking**: Integration tests use real dependencies
4. **Clear**: One test per scenario, clear docstrings
5. **Reliable**: No flaky tests, deterministic results
6. **Continuous**: Tests run automatically on changes
7. **Immediate Fixes**: Failing tests fixed before continuing
