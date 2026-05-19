"""
Django management command to create demo FDD-like playbook.

Creates a Feature-Driven Development inspired playbook with:
- 2 workflows: "Design Features" and "Implement Features"
- 10 activities total with rich Markdown guidance
- Mermaid diagrams, code examples, and structured guidance
"""

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from methodology.models import Playbook, Workflow
from methodology.services.activity_service import ActivityService

User = get_user_model()


class Command(BaseCommand):
    help = 'Create demo FDD-like playbook with 10 activities in 2 workflows'

    def handle(self, *args, **options):
        self.stdout.write('Creating demo FDD playbook...')
        
        # Get or create admin user
        admin_user = User.objects.filter(username='admin').first()
        if not admin_user:
            admin_user = User.objects.create_superuser(
                username='admin',
                email='admin@example.com',
                password='admin123'
            )
            self.stdout.write(self.style.SUCCESS(f'Created admin user'))
        
        # Create playbook
        playbook = Playbook.objects.create(
            name='Feature-Driven Development (FDD)',
            description='A lightweight iterative software development process focused on building features',
            category='development',
            tags=['agile', 'fdd', 'iterative', 'feature-driven'],
            status='active',
            source='owned',
            visibility='private',
            author=admin_user
        )
        self.stdout.write(self.style.SUCCESS(f'Created playbook: {playbook.name}'))
        
        # Workflow 1: Design Features
        workflow_design = Workflow.objects.create(
            name='Design Features',
            description='Design phase for feature development - from model to detailed design',
            playbook=playbook,
            order=1
        )
        self.stdout.write(self.style.SUCCESS(f'Created workflow: {workflow_design.name}'))
        
        # Design Activities (5 activities)
        design_activities = [
            {
                'name': 'Build Domain Model',
                'guidance': '''## Overview

Build an overall domain model that provides a framework for adding detail on a feature-by-feature basis.

## Steps

1. **Identify Major Domain Objects**
   - Review requirements and existing documentation
   - List key business entities
   - Define relationships between entities

2. **Create Class Diagram**
   - Use UML notation
   - Include key attributes and methods
   - Show associations and multiplicities

## Example

```mermaid
classDiagram
    class User {
        +String username
        +String email
        +login()
        +logout()
    }
    class Order {
        +Date orderDate
        +Decimal total
        +submit()
        +cancel()
    }
    User "1" --> "*" Order : places
```

## Deliverables

- Domain model diagram
- Class definitions document
- Entity relationship documentation
''',
                'phase': 'Modeling',
                'order': 1,
                'has_dependencies': False
            },
            {
                'name': 'Develop Feature List',
                'guidance': '''## Overview

Identify and document all features that need to be designed and built. Features are small, client-valued functions expressed in the form: `<action> <result> <object>`.

## Steps

1. **Decompose Requirements**
   - Break down high-level requirements
   - Identify discrete features
   - Use client-friendly language

2. **Categorize Features**
   - Group by business area
   - Assign to major feature sets
   - Prioritize by business value

3. **Feature Naming Convention**
   ```
   <action> <result> <by/for/of/to> <object>
   
   Examples:
   - Calculate total of Sale
   - Display properties of Product
   - Validate completeness of Order
   ```

## Template

| Feature ID | Feature Name | Description | Priority |
|------------|--------------|-------------|----------|
| FT-001 | Calculate order total | Compute sum of line items plus tax | High |
| FT-002 | Validate payment info | Check credit card details | High |
| FT-003 | Send order confirmation | Email receipt to customer | Medium |

## Deliverables

- Feature list document
- Feature categorization
- Priority matrix
''',
                'phase': 'Planning',
                'order': 2,
                'has_dependencies': True
            },
            {
                'name': 'Plan by Feature',
                'guidance': '''## Overview

Plan the development sequence and assign features to programmers. Group features into work packages based on complexity and dependencies.

## Steps

1. **Sequence Features**
   - Order by dependencies
   - Consider technical risk
   - Balance team workload

2. **Estimate Effort**
   - Use story points or days
   - Factor in complexity
   - Account for unknowns

3. **Create Work Packages**
   ```markdown
   ### Work Package: User Authentication
   
   **Features:**
   - Login user
   - Logout user  
   - Reset password
   
   **Dependencies:** User model, Database setup
   **Estimated Effort:** 5 days
   **Assigned To:** Developer A
   ```

## Deliverables

- Development plan
- Feature assignments
- Timeline estimates
''',
                'phase': 'Planning',
                'order': 3,
                'has_dependencies': True
            },
            {
                'name': 'Design by Feature',
                'guidance': '''## Overview

For each feature, produce detailed design documentation including sequence diagrams, refinements to the object model, and method signatures.

## Steps

1. **Refine Domain Model**
   - Add feature-specific classes
   - Define attributes and methods
   - Document relationships

2. **Create Sequence Diagrams**
   ```mermaid
   sequenceDiagram
       participant User
       participant Controller
       participant Service
       participant Database
       
       User->>Controller: submitOrder()
       Controller->>Service: validateOrder()
       Service->>Database: checkInventory()
       Database-->>Service: inventory status
       Service-->>Controller: validation result
       Controller-->>User: confirmation
   ```

3. **Define Method Signatures**
   ```python
   class OrderService:
       def validate_order(self, order_id: int) -> bool:
           """
           Validate order completeness and inventory
           
           Args:
               order_id: Order identifier
               
           Returns:
               True if order is valid, False otherwise
           """
           pass
   ```

## Deliverables

- Feature design document
- Sequence diagrams
- Updated class model
- Method signatures
''',
                'phase': 'Design',
                'order': 4,
                'has_dependencies': True
            },
            {
                'name': 'Design Inspection',
                'guidance': '''## Overview

Review and validate designs for completeness, correctness, and consistency before implementation begins.

## Steps

1. **Prepare for Inspection**
   - Distribute design documents
   - Schedule review session
   - Identify reviewers

2. **Conduct Design Review**
   - Walk through sequence diagrams
   - Verify method signatures
   - Check error handling
   - Validate assumptions

3. **Review Checklist**
   - [ ] All feature requirements covered
   - [ ] Sequence diagrams complete
   - [ ] Method signatures defined
   - [ ] Error cases handled
   - [ ] Dependencies identified
   - [ ] Performance considerations noted
   - [ ] Security implications reviewed

4. **Document Findings**
   | Issue ID | Severity | Description | Resolution |
   |----------|----------|-------------|------------|
   | INS-001 | High | Missing error handling | Add try-catch |
   | INS-002 | Medium | Unclear method name | Rename to clarify |

## Deliverables

- Inspection report
- Issue log
- Approved design (or rework list)
''',
                'phase': 'Review',
                'order': 5,
                'has_dependencies': True
            }
        ]
        
        for activity_data in design_activities:
            activity = ActivityService.create_activity(
                workflow=workflow_design,
                **activity_data
            )
            self.stdout.write(f'  ✓ Created activity: {activity.name}')
        
        # Workflow 2: Implement Features
        workflow_implement = Workflow.objects.create(
            name='Implement Features',
            description='Implementation phase - code, test, and integrate features',
            playbook=playbook,
            order=2
        )
        self.stdout.write(self.style.SUCCESS(f'Created workflow: {workflow_implement.name}'))
        
        # Implementation Activities (5 activities)
        implement_activities = [
            {
                'name': 'Build by Feature',
                'guidance': '''## Overview

Implement the feature according to the approved design. This includes coding, unit testing, and code review.

## Steps

1. **Implement Classes**
   ```python
   class OrderValidator:
       """Validates order completeness and business rules."""
       
       def __init__(self, inventory_service: InventoryService):
           self.inventory = inventory_service
           
       def validate(self, order: Order) -> ValidationResult:
           """
           Validate order against business rules.
           
           Returns ValidationResult with success/failure and messages.
           """
           if not order.items:
               return ValidationResult(False, "Order has no items")
               
           if not self._check_inventory(order):
               return ValidationResult(False, "Insufficient inventory")
               
           return ValidationResult(True, "Order valid")
   ```

2. **Write Unit Tests**
   ```python
   def test_validate_empty_order():
       validator = OrderValidator(mock_inventory)
       result = validator.validate(Order())
       assert not result.success
       assert "no items" in result.message
   ```

3. **Run Tests**
   - Execute unit tests
   - Verify 100% pass rate
   - Check code coverage

## Quality Gates

- [ ] All methods implemented
- [ ] Unit tests written
- [ ] Tests passing
- [ ] Code follows style guide
- [ ] No static analysis warnings

## Deliverables

- Working code
- Unit tests
- Test results
''',
                'phase': 'Implementation',
                'order': 1,
                'has_dependencies': False
            },
            {
                'name': 'Code Inspection',
                'guidance': '''## Overview

Peer review of implemented code to ensure quality, maintainability, and adherence to standards.

## Steps

1. **Pre-Inspection**
   - Create pull request/merge request
   - Run automated checks (linting, tests)
   - Prepare code walkthrough

2. **Code Review Checklist**
   - [ ] Code matches design
   - [ ] Naming conventions followed
   - [ ] Error handling present
   - [ ] No code duplication
   - [ ] Comments where needed
   - [ ] Tests comprehensive
   - [ ] No security vulnerabilities
   - [ ] Performance acceptable

3. **Review Process**
   ```markdown
   **Reviewer:** Jane Doe
   **Date:** 2025-01-15
   **Feature:** Calculate Order Total
   
   **Findings:**
   - ✓ Logic correct
   - ⚠️ Missing null check on line 47
   - ⚠️ Method too complex - consider refactoring
   - ✓ Tests cover happy path
   - ⚠️ Need edge case tests
   
   **Decision:** Rework required
   ```

## Deliverables

- Code review report
- Approved code (or rework items)
''',
                'phase': 'Review',
                'order': 2,
                'has_dependencies': True
            },
            {
                'name': 'Integration Testing',
                'guidance': '''## Overview

Test the feature in context with other features and system components to ensure proper integration.

## Steps

1. **Create Integration Tests**
   ```python
   @pytest.mark.integration
   def test_order_processing_flow():
       # Setup
       user = create_test_user()
       product = create_test_product()
       
       # Execute full flow
       order = create_order(user, [product])
       payment = process_payment(order)
       confirmation = send_confirmation(order, payment)
       
       # Verify
       assert order.status == 'COMPLETED'
       assert payment.status == 'SUCCESS'
       assert confirmation.sent == True
   ```

2. **Test Scenarios**
   - Happy path (all success)
   - Error conditions
   - Edge cases
   - Boundary conditions

3. **Integration Test Matrix**
   | Test ID | Scenario | Components | Status |
   |---------|----------|------------|--------|
   | INT-001 | Complete order flow | Order, Payment, Email | Pass |
   | INT-002 | Payment failure | Order, Payment | Pass |
   | INT-003 | Inventory insufficient | Order, Inventory | Pass |

## Deliverables

- Integration test suite
- Test results report
- Defect log (if any)
''',
                'phase': 'Testing',
                'order': 3,
                'has_dependencies': True
            },
            {
                'name': 'Feature Integration',
                'guidance': '''## Overview

Integrate the completed feature into the main codebase, ensuring it works harmoniously with existing features.

## Steps

1. **Pre-Integration Checklist**
   - [ ] All tests passing
   - [ ] Code reviewed and approved
   - [ ] Documentation updated
   - [ ] Database migrations ready
   - [ ] Configuration reviewed

2. **Merge Strategy**
   ```bash
   # Fetch latest main
   git fetch origin main
   git checkout main
   git pull
   
   # Merge feature branch
   git merge --no-ff feature/calculate-order-total
   
   # Run full test suite
   pytest tests/
   
   # Push if all tests pass
   git push origin main
   ```

3. **Post-Integration Verification**
   - Run full regression test suite
   - Verify build pipeline success
   - Check deployment readiness

4. **Integration Flow**
   ```mermaid
   graph LR
       A[Feature Branch] --> B[Code Review]
       B --> C[Merge to Main]
       C --> D[CI/CD Pipeline]
       D --> E[Staging Deploy]
       E --> F[Smoke Tests]
       F --> G[Production Ready]
   ```

## Deliverables

- Merged code in main branch
- Integration test results
- Build pipeline success confirmation
''',
                'phase': 'Integration',
                'order': 4,
                'has_dependencies': True
            },
            {
                'name': 'Release Feature',
                'guidance': '''## Overview

Deploy the feature to production and verify it works correctly in the live environment.

## Steps

1. **Pre-Release Checklist**
   - [ ] Feature toggle configured
   - [ ] Rollback plan documented
   - [ ] Monitoring alerts set up
   - [ ] Stakeholders notified
   - [ ] Documentation published

2. **Deployment Process**
   ```yaml
   # deployment.yml
   feature:
     name: calculate-order-total
     version: 1.0.0
     toggle: FEATURE_ORDER_TOTAL_V2
     rollout: 
       - environment: staging
         percentage: 100
       - environment: production
         percentage: 10  # Canary
   ```

3. **Post-Release Verification**
   - Monitor error rates
   - Check performance metrics
   - Verify user analytics
   - Gather feedback

4. **Rollout Strategy**
   ```mermaid
   graph TD
       A[Deploy to Staging] --> B[Smoke Tests]
       B --> C{Tests Pass?}
       C -->|Yes| D[10% Production]
       C -->|No| E[Rollback]
       D --> F[Monitor 24h]
       F --> G{Stable?}
       G -->|Yes| H[50% Production]
       G -->|No| E
       H --> I[Monitor 24h]
       I --> J{Stable?}
       J -->|Yes| K[100% Production]
       J -->|No| E
   ```

## Deliverables

- Production deployment
- Release notes
- Monitoring dashboard
- Feature metrics report
''',
                'phase': 'Deployment',
                'order': 5,
                'has_dependencies': True
            }
        ]
        
        for activity_data in implement_activities:
            activity = ActivityService.create_activity(
                workflow=workflow_implement,
                **activity_data
            )
            self.stdout.write(f'  ✓ Created activity: {activity.name}')
        
        self.stdout.write(self.style.SUCCESS('\n' + '='*60))
        self.stdout.write(self.style.SUCCESS(f'✓ Demo FDD Playbook Created Successfully!'))
        self.stdout.write(self.style.SUCCESS('='*60))
        self.stdout.write(f'\nPlaybook: {playbook.name}')
        self.stdout.write(f'Workflows: 2')
        self.stdout.write(f'Activities: 10 (5 in Design, 5 in Implement)')
        self.stdout.write(f'\nView at: /playbooks/{playbook.pk}/')
