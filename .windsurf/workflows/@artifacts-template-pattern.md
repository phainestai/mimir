## Artifacts Template Pattern for Workflows/Activities

Since we now have the Artifact model with `template_file` support, here's how to enhance Workflows and Activities with template-style artifacts:

### Enhanced Activity Pattern with Template Artifacts

```markdown
# Activity: Create React Component

**Activity ID**: TBD
**Order**: 3
**Phase**: Implementation
**Dependencies**: Predecessor: Design Component API

## Description
Create a reusable React component following established patterns.

## Template Artifacts

### Outputs (Produced by this Activity):
- **React Component** (Code, Required) 
  - Template: `component_template.tsx` 📁
  - Location: `src/components/{ComponentName}/`
  - Includes: TypeScript interface, props validation, tests
  
- **Storybook Story** (Document, Optional)
  - Template: `story_template.stories.tsx` 📁  
  - Location: `src/components/{ComponentName}/{ComponentName}.stories.tsx`
  - Includes: Default args, variants, documentation
  
- **Unit Tests** (Code, Required)
  - Template: `component_test_template.test.tsx` 📁
  - Location: `src/components/{ComponentName}/__tests__/`
  - Includes: Render tests, interaction tests, accessibility tests

### Inputs (Consumed by this Activity):
- **Component API Specification** (from: Design Component API)
- **Design System Tokens** (from: Setup Design System)  
- **Code Style Guide** (from: Define Development Standards)

## Guidance
Follow the template artifacts above. The component template includes:
- Proper TypeScript interfaces
- Accessibility attributes
- Error boundary patterns
- Performance optimization hooks

Replace `{ComponentName}` with your actual component name in PascalCase.
```

### Template File Examples

**component_template.tsx**:
```typescript
import React, { memo } from 'react';
import { cn } from '@/lib/utils';

interface {ComponentName}Props {
  children: React.ReactNode;
  className?: string;
  variant?: 'default' | 'secondary' | 'destructive';
  size?: 'sm' | 'md' | 'lg';
}

export const {ComponentName} = memo<{ComponentName}Props>(({ 
  children, 
  className, 
  variant = 'default',
  size = 'md',
  ...props 
}) => {
  return (
    <div
      className={cn(
        'component-base-styles',
        variants[variant],
        sizes[size],
        className
      )}
      {...props}
    >
      {children}
    </div>
  );
});

{ComponentName}.displayName = '{ComponentName}';

const variants = {
  default: 'bg-primary text-primary-foreground',
  secondary: 'bg-secondary text-secondary-foreground', 
  destructive: 'bg-destructive text-destructive-foreground',
};

const sizes = {
  sm: 'h-8 px-2 text-sm',
  md: 'h-10 px-4',
  lg: 'h-12 px-6 text-lg',
};
```

### Enhanced Workflow Pattern

```markdown
# Workflow: React Component Development

**Workflow ID**: TBD
**Description**: Standard process for creating reusable React components
**Artifact Flow**: Design → Implement → Test → Document → Review

## Standard Artifact Templates

This workflow consistently produces these artifact types across all activities:

### 🎨 **Design Phase Artifacts**
- **Component Specification** (Template: `spec_template.md`)
- **Figma Design** (Template: `figma_component_template.fig`)  
- **Accessibility Checklist** (Template: `a11y_checklist.md`)

### 💻 **Implementation Phase Artifacts**  
- **React Component** (Template: `component_template.tsx`)
- **TypeScript Types** (Template: `types_template.ts`)
- **CSS Modules** (Template: `styles_template.module.css`)

### 🧪 **Testing Phase Artifacts**
- **Unit Tests** (Template: `component_test_template.test.tsx`)
- **Visual Regression Tests** (Template: `visual_test_template.spec.ts`)
- **Integration Tests** (Template: `integration_test_template.spec.ts`)

### 📚 **Documentation Phase Artifacts**
- **Storybook Story** (Template: `story_template.stories.tsx`)
- **API Documentation** (Template: `api_docs_template.md`)
- **Usage Examples** (Template: `examples_template.md`)

## Activities
1. **Design Component API** → Produces: Component Specification, Figma Design
2. **Implement Component** → Produces: React Component, TypeScript Types  
3. **Write Tests** → Produces: Unit Tests, Visual Tests
4. **Create Documentation** → Produces: Storybook Story, API Docs
5. **Review & Publish** → Produces: Published Component, Usage Examples
```

### Implementation in Models

The existing Artifact model already supports this with:
- **template_file**: FileField for storing template files
- **produced_by**: Links to the Activity that creates artifact
- **type**: "Template", "Code", "Document", etc.
- **is_required**: Boolean flag for Must vs Optional artifacts

### Benefits of Template Artifacts

1. **Consistency**: All React components follow same structure
2. **Speed**: Developers start with working templates, not blank files  
3. **Quality**: Templates embed best practices, accessibility, testing
4. **Onboarding**: New team members see expected patterns immediately
5. **Evolution**: Update templates to improve all future components