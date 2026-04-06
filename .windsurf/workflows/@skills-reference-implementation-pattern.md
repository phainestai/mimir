## Enhanced DTA Activity Pattern with Skills Integration

Here's how to enhance DTA activities to link reference implementations via Skills:

### Example Enhancement for DTA-03 (Integration & API Design)

```markdown
### 5. Scan Skills & Reference Implementations

Query Playbook Skills where `capability_domain` in:
- `API_REST`
- `API_GRAPHQL` 
- `API_MCP`
- `INTEGRATION_EXTERNAL`

Report coverage:
```
Skill Coverage for Integration & API Design:
  API_REST         | [Django REST Framework Skill] ✅
                   | Reference: /skills/api-rest-django/examples/
                   | Includes: CRUD endpoints, serializers, pagination
  
  API_MCP          | [FastMCP Integration Skill] ✅  
                   | Reference: /skills/api-mcp-fastmcp/examples/
                   | Includes: Tool decorators, stdio handling, error patterns
  
  API_GRAPHQL      | ❌ No Skill - will need custom implementation
                   | Estimated impact: +2 iterations for research/prototyping
```

If reference implementations exist: "Following Django REST patterns from [Django REST Framework Skill](#skill-123), estimate 3 days for implementation."

If gaps exist: "No Skill for GraphQL — will need to research/prototype. Estimated impact: +2 iterations."
```

### Skills Content Structure for Reference Implementations

```markdown
# Skill: Django REST Framework API Implementation

## Overview
**Capability Domain**: API_REST
**Technology Stack**: Django+DRF+PostgreSQL

## Reference Implementation

### 1. Basic CRUD Endpoints
```python
# views.py - Reference implementation
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

class PlaybookViewSet(viewsets.ModelViewSet):
    queryset = Playbook.objects.filter(status='released')
    serializer_class = PlaybookSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        # Filter by user ownership
        return super().get_queryset().filter(author=self.request.user)
```

### 2. Pagination & Filtering
```python
# settings.py - Standard pagination
REST_FRAMEWORK = {
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
    'DEFAULT_FILTER_BACKENDS': ['django_filters.rest_framework.DjangoFilterBackend']
}
```

### 3. Error Handling Pattern
```python
# exceptions.py - Standard error responses
from rest_framework.views import exception_handler

def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)
    if response is not None:
        response.data = {
            'error': True,
            'message': str(exc),
            'code': response.status_code
        }
    return response
```

### 4. Repository Links
- **Example Project**: https://github.com/example/django-rest-patterns
- **Production Usage**: Mimir HOMEBASE API implementation
- **Documentation**: https://www.django-rest-framework.org/

## Common Pitfalls
- Don't expose internal model structure in serializers
- Always implement proper permission checks
- Use throttling for public endpoints

## Quality Gates
- [ ] All endpoints have tests with >90% coverage
- [ ] API documentation generated automatically
- [ ] Authentication/authorization implemented
- [ ] Error responses follow consistent format
```