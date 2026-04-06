# Skill: Playwright Semantic Naming for UI Testing

**Capability Domain**: UI_TESTING
**Technology Stack**: Playwright+HTML

## Overview

Comprehensive rules for naming HTML and UI components to ensure reliable Playwright E2E testing. Emphasizes `data-testid` attributes, accessibility, and semantic naming patterns.

## Reference Implementation

### Pattern 1: Playwright Selector Hierarchy (MANDATORY ORDER)

Always use selectors in this exact priority order:

1. **`get_by_test_id(...)`** - Primary choice for all components
2. **`get_by_role(name=...)`** - Secondary for semantic elements with aria-labels
3. **`get_by_label(...)`** - For form inputs with labels
4. **`get_by_text(...)`** - Only for static, stable content
5. **NEVER** use CSS selectors, XPath, or `locator()` with CSS

### Pattern 2: Hierarchical data-testid Naming

```html
<!-- Page-Level Containers -->
<div data-testid="playbooks-page">
<div data-testid="playbook-form-dialog">
<div data-testid="playbook-details-modal">

<!-- Feature Components -->
<div data-testid="playbook-card">
<div data-testid="playbook-list">
<div data-testid="playbook-filters">

<!-- Action Elements -->
<button data-testid="create-playbook-button">
<button data-testid="save-playbook-button">
<button data-testid="edit-playbook-button">
<button data-testid="delete-playbook-button">

<!-- Form Elements -->
<input data-testid="playbook-name-input">
<textarea data-testid="playbook-description-input">
<select data-testid="playbook-category-select">

<!-- Status/Feedback -->
<div data-testid="success-message">
<div data-testid="error-message">
<div data-testid="loading-spinner">
```

### Pattern 3: Mandatory Accessibility Attributes

Every interactive element MUST have proper accessibility:

```html
<!-- Buttons - MUST have aria-label or descriptive text -->
<button aria-label="Create new playbook" data-testid="create-playbook-button">
  <i class="fa-solid fa-plus"></i>
</button>

<!-- Form inputs - MUST have associated labels -->
<label for="playbook-name">Playbook Name *</label>
<input 
  id="playbook-name" 
  data-testid="playbook-name-input"
  aria-describedby="name-error"
  required 
/>
<div id="name-error" data-testid="playbook-name-error" role="alert">
  {nameError}
</div>

<!-- Dialogs - MUST have unique accessible names -->
<dialog aria-label="Create Playbook Dialog" data-testid="playbook-form-dialog">
  <h2>Create New Playbook</h2>
</dialog>
```

### Pattern 4: Component State Visibility

Make component states testable via data attributes:

```html
<!-- Loading states -->
<div 
  data-testid="playbook-list" 
  data-state="loading"
  data-count="0">
</div>

<!-- Form validation states -->
<input 
  data-testid="playbook-name-input"
  data-valid="false"
  aria-invalid="true"
/>

<!-- Button states -->
<button 
  data-testid="save-playbook-button"
  data-state="submitting"
  disabled>
  Saving...
</button>
```

### Pattern 5: List and Card Components

Ensure predictable structure for list items:

```html
<!-- List container -->
<div data-testid="playbook-list" role="list">
  <div 
    data-testid="playbook-card"
    data-playbook-id="1"
    data-playbook-status="draft"
    role="article"
    aria-label="Playbook: React Development">
    
    <h3 data-testid="playbook-card-title">React Development</h3>
    <p data-testid="playbook-card-status">Draft</p>
    
    <div data-testid="playbook-card-actions">
      <button 
        data-testid="edit-playbook-button"
        aria-label="Edit React Development">
        Edit
      </button>
    </div>
  </div>
</div>
```

### Pattern 6: Form Components

Structure forms for reliable testing:

```html
<form 
  role="form" 
  aria-label="Playbook creation form"
  data-testid="playbook-form">
  
  <fieldset data-testid="playbook-basic-fields">
    <legend>Basic Information</legend>
    
    <div data-testid="playbook-name-field">
      <label for="playbook-name">Name *</label>
      <input 
        id="playbook-name"
        data-testid="playbook-name-input"
        required
        aria-describedby="name-error"
      />
      <div id="name-error" data-testid="playbook-name-error" role="alert">
        {nameError}
      </div>
    </div>
  </fieldset>
  
  <div data-testid="playbook-form-actions">
    <button 
      type="button"
      data-testid="cancel-playbook-button">
      Cancel
    </button>
    <button 
      type="submit"
      data-testid="save-playbook-button">
      Save
    </button>
  </div>
</form>
```

## Common Pitfalls

### ❌ Don't: Generic names
```html
<div id="main" class="container">
<button class="btn btn-primary">
```

### ✅ Do: Semantic, descriptive names
```html
<main data-testid="playbooks-page" role="main">
<button data-testid="create-playbook-button" aria-label="Create new playbook">
```

### ❌ Don't: Use CSS selectors in tests
```python
page.locator('.btn-primary').click()
page.locator('div:nth-child(2)').click()
```

### ✅ Do: Use data-testid selectors
```python
page.get_by_test_id("create-playbook-button").click()
page.get_by_test_id("playbook-card").filter(has_text="React").click()
```

### ❌ Don't: Missing accessibility
```html
<button><i class="fa-plus"></i></button>  <!-- No aria-label -->
<input />  <!-- No label -->
```

### ✅ Do: Proper accessibility
```html
<button aria-label="Create new playbook">
  <i class="fa-plus"></i>
</button>
<label for="name">Name</label>
<input id="name" />
```

## Quality Gates

Before committing any component, verify:

- [ ] All interactive elements have `aria-label` or descriptive text
- [ ] All form inputs have associated `<label>` elements
- [ ] All dialogs have unique accessible names
- [ ] All components have appropriate `data-testid` attributes
- [ ] Component states are visible via data attributes
- [ ] List items have predictable structure and identifiers
- [ ] Form validation errors are accessible and testable
- [ ] No CSS animations interfere with testing
- [ ] Naming follows hierarchical pattern (domain-component-element-type)

## Naming Convention

Format: `{domain}-{component}-{element}-{type}`

Examples:
- `playbook-list` (component)
- `playbook-card-title` (element in component)
- `create-playbook-button` (action)
- `playbook-name-input` (form field)
- `playbook-form-dialog` (modal)

## Testing Validation Checklist

- [ ] All buttons have icons and tooltips
- [ ] All forms have proper labels
- [ ] All errors have role="alert"
- [ ] All modals have aria-label
- [ ] All lists have role="list"
- [ ] All cards have role="article"
- [ ] All interactive elements are keyboard accessible
- [ ] All state changes are visible via data attributes
