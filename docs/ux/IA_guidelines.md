# Mimir Information Architecture Guidelines

## Document Overview

This document defines the Information Architecture, Design System, and UI patterns for the Mimir application. We rely heavily on **Bootstrap 5.3+** as our foundational framework, extending it with custom tokens and components where needed.

**Philosophy**: Leverage Bootstrap's conventions, utilities, and component patterns as the first choice. Customize only when necessary for brand identity or specific user experience requirements.

---

## Table of Contents

1. [Design System Foundation](#design-system-foundation)
2. [Skeleton & Layout](#skeleton--layout)
3. [Visual Design](#visual-design)
4. [Component Kit (Atomic Design)](#component-kit-atomic-design)
5. [Behavior & Interactions](#behavior--interactions)
6. [Flow & User Experience](#flow--user-experience)
7. [Data & State Patterns](#data--state-patterns)

---

## Design System Foundation

### 1. Design Tokens

We extend Bootstrap's native CSS variables with Mimir-specific tokens. All tokens follow Bootstrap's naming convention for consistency.

#### Color Tokens

**Base Bootstrap Colors** (use as-is):
```css
/* Primary palette - Bootstrap defaults */
--bs-primary: #0d6efd;
--bs-secondary: #6c757d;
--bs-success: #198754;
--bs-info: #0dcaf0;
--bs-warning: #ffc107;
--bs-danger: #dc3545;
--bs-light: #f8f9fa;
--bs-dark: #212529;

/* Grayscale */
--bs-gray-100: #f8f9fa;
--bs-gray-200: #e9ecef;
--bs-gray-300: #dee2e6;
--bs-gray-400: #ced4da;
--bs-gray-500: #adb5bd;
--bs-gray-600: #6c757d;
--bs-gray-700: #495057;
--bs-gray-800: #343a40;
--bs-gray-900: #212529;
```

**Mimir Custom Colors** (stat cards from dashboard):
```css
/* Dashboard stat card colors */
--mimir-purple: #5856d6;       /* Members online - purple card */
--mimir-blue: #38a9f0;         /* Members online - blue card */
--mimir-orange: #ffa726;       /* Members online - orange card */
--mimir-red: #ef5350;          /* Members online - red card */

/* Chart colors */
--mimir-chart-primary: #38a9f0;
--mimir-chart-secondary: #4caf50;
--mimir-chart-accent: #ffa726;

/* Background colors */
--mimir-bg-body: #f5f5f5;
--mimir-bg-surface: #ffffff;
--mimir-bg-elevated: #ffffff;
```

#### Spacing Tokens

**Use Bootstrap's spacing scale** (0.25rem increments):
```css
/* Bootstrap spacing multiplier: 1 = 0.25rem = 4px */
--bs-spacer: 1rem; /* 16px base */

/* Usage via utility classes */
.m-0  /* margin: 0 */
.m-1  /* margin: 0.25rem (4px) */
.m-2  /* margin: 0.5rem (8px) */
.m-3  /* margin: 1rem (16px) */
.m-4  /* margin: 1.5rem (24px) */
.m-5  /* margin: 3rem (48px) */

/* Same pattern for padding (p-*), gaps (gap-*), etc. */
```

**Mimir Custom Spacing**:
```css
/* Card spacing */
--mimir-card-padding: 1.25rem;        /* 20px */
--mimir-card-gap: 1.5rem;             /* 24px between cards */

/* Section spacing */
--mimir-section-gap: 2rem;            /* 32px between major sections */
--mimir-content-max-width: 1200px;    /* Max width for main content */
```

#### Typography Tokens

**Bootstrap Font Stack** (use as-is):
```css
--bs-font-sans-serif: system-ui, -apple-system, "Segoe UI", Roboto, "Helvetica Neue", "Noto Sans", "Liberation Sans", Arial, sans-serif;
--bs-font-monospace: SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace;

/* Font sizes - Bootstrap scale */
--bs-body-font-size: 1rem;        /* 16px */
--bs-body-font-weight: 400;
--bs-body-line-height: 1.5;

/* Heading scale */
--bs-h1-font-size: 2.5rem;        /* 40px */
--bs-h2-font-size: 2rem;          /* 32px */
--bs-h3-font-size: 1.75rem;       /* 28px */
--bs-h4-font-size: 1.5rem;        /* 24px */
--bs-h5-font-size: 1.25rem;       /* 20px */
--bs-h6-font-size: 1rem;          /* 16px */
```

**Mimir Typography Extensions**:
```css
/* Stat card numbers */
--mimir-stat-number: 2.5rem;      /* Large numbers like "9,823" */
--mimir-stat-label: 0.875rem;     /* Labels like "Members online" */

/* Small text */
--mimir-text-small: 0.875rem;     /* 14px */
--mimir-text-xs: 0.75rem;         /* 12px */
```

#### Shadow Tokens

**Bootstrap Shadows** (use as-is):
```css
--bs-box-shadow: 0 0.5rem 1rem rgba(0, 0, 0, 0.15);
--bs-box-shadow-sm: 0 0.125rem 0.25rem rgba(0, 0, 0, 0.075);
--bs-box-shadow-lg: 0 1rem 3rem rgba(0, 0, 0, 0.175);
--bs-box-shadow-inset: inset 0 1px 2px rgba(0, 0, 0, 0.075);
```

**Mimir Custom Shadows**:
```css
/* Card elevation */
--mimir-card-shadow: 0 2px 4px rgba(0, 0, 0, 0.08);
--mimir-card-shadow-hover: 0 4px 12px rgba(0, 0, 0, 0.15);

/* Modal/dropdown elevation */
--mimir-elevated-shadow: 0 8px 24px rgba(0, 0, 0, 0.12);
```

#### Border Tokens

**Bootstrap Borders** (use as-is):
```css
--bs-border-width: 1px;
--bs-border-style: solid;
--bs-border-color: #dee2e6;
--bs-border-radius: 0.375rem;       /* 6px */
--bs-border-radius-sm: 0.25rem;     /* 4px */
--bs-border-radius-lg: 0.5rem;      /* 8px */
--bs-border-radius-xl: 1rem;        /* 16px */
--bs-border-radius-2xl: 2rem;       /* 32px */
--bs-border-radius-pill: 50rem;     /* Fully rounded */
```

**Mimir Border Extensions**:
```css
/* Card borders */
--mimir-card-border-width: 0;       /* Cards use shadow instead of border */
--mimir-card-border-radius: 0.5rem; /* 8px rounded corners */

/* Input borders */
--mimir-input-border-color: var(--bs-gray-300);
--mimir-input-focus-border-color: var(--bs-primary);
```

---

### 2. Token Naming Conventions

**Follow Bootstrap's BEM-inspired naming**:

```
--{namespace}-{element}-{property}-{modifier}
```

**Examples**:
- `--bs-primary` (Bootstrap namespace, color name)
- `--bs-btn-padding-x` (Bootstrap namespace, button element, padding horizontal)
- `--mimir-card-shadow` (Mimir namespace, card element, shadow property)
- `--mimir-stat-number` (Mimir namespace, stat element, number variant)

**Naming Rules**:
1. Use `--bs-*` for Bootstrap overrides
2. Use `--mimir-*` for custom tokens
3. Use semantic names (`--mimir-bg-surface`) over literal (`--mimir-white`)
4. Use kebab-case for all token names
5. Group related tokens with common prefix

---

### 3. Theming Strategy

#### Light Mode (Default)

Based on the dashboard screenshot, light mode uses:

```css
[data-bs-theme="light"] {
  /* Background hierarchy */
  --mimir-bg-body: #f5f5f5;           /* Page background (light gray) */
  --mimir-bg-surface: #ffffff;        /* Card/panel background */
  --mimir-bg-elevated: #ffffff;       /* Modal/dropdown background */
  
  /* Text colors */
  --mimir-text-primary: #212529;      /* Primary text */
  --mimir-text-secondary: #6c757d;    /* Secondary/muted text */
  --mimir-text-disabled: #adb5bd;     /* Disabled text */
  
  /* Border colors */
  --mimir-border-color: #dee2e6;      /* Default borders */
  --mimir-divider-color: #e9ecef;     /* Dividers/separators */
}
```

#### Dark Mode

Toggle via icon in top navigation. Uses Bootstrap's dark mode with Mimir adjustments:

```css
[data-bs-theme="dark"] {
  /* Background hierarchy */
  --mimir-bg-body: #1a1a1a;
  --mimir-bg-surface: #2d2d2d;
  --mimir-bg-elevated: #3a3a3a;
  
  /* Text colors */
  --mimir-text-primary: #f8f9fa;
  --mimir-text-secondary: #adb5bd;
  --mimir-text-disabled: #6c757d;
  
  /* Border colors */
  --mimir-border-color: #495057;
  --mimir-divider-color: #343a40;
  
  /* Adjust stat card backgrounds for dark mode */
  --mimir-purple: #7c7aec;
  --mimir-blue: #64c3ff;
  --mimir-orange: #ffb74d;
  --mimir-red: #f77673;
}
```

#### Theme Switching

- Toggle button in top-right navigation (moon/sun icon)
- Preference saved to `localStorage`
- Smooth transition: `transition: background-color 0.2s ease, color 0.2s ease;`
- Use Bootstrap's `[data-bs-theme]` attribute on `<html>` or `<body>`

#### Brand Variations

Not currently implemented. Future consideration for:
- Whitelabel deployments
- Family-specific branding
- Custom color schemes per user preference

---

### 4. Icon System

**Font Awesome Pro** is the primary icon library.

#### Icon Guidelines

**Usage**:
```html
<!-- Solid icons for primary actions -->
<i class="fa-solid fa-save"></i>

<!-- Regular icons for secondary actions -->
<i class="fa-regular fa-heart"></i>

<!-- Light icons for subtle UI elements -->
<i class="fa-light fa-gear"></i>
```

**Icon Sizes**:
```css
/* Bootstrap icon sizing utilities */
.icon-xs { font-size: 0.75rem; }   /* 12px */
.icon-sm { font-size: 1rem; }      /* 16px - default */
.icon-md { font-size: 1.5rem; }    /* 24px */
.icon-lg { font-size: 2rem; }      /* 32px */
.icon-xl { font-size: 3rem; }      /* 48px */
```

**Icon Colors**:
- Use Bootstrap color utilities: `.text-primary`, `.text-danger`, etc.
- Inherit text color by default
- Use semantic colors for status: success (green), warning (orange), danger (red)

**Icon + Text Pattern**:
```html
<!-- Icon before text (most common) -->
<button class="btn btn-primary">
  <i class="fa-solid fa-save me-2"></i>
  Save Changes
</button>

<!-- Icon after text (dropdowns, external links) -->
<a href="#" class="btn btn-link">
  View Details
  <i class="fa-solid fa-arrow-right ms-2"></i>
</a>

<!-- Icon only (with tooltip) -->
<button class="btn btn-icon" data-bs-toggle="tooltip" title="Settings">
  <i class="fa-solid fa-gear"></i>
</button>
```

**Navigation Icons** (from dashboard):
- Settings: `fa-gear`
- Notifications: `fa-bell` (with badge count)
- Messages: `fa-envelope` (with badge count)
- User menu: `fa-user-circle` or avatar image
- Dark mode toggle: `fa-moon` / `fa-sun`
- Dashboard: `fa-chart-line`
- Hamburger menu: `fa-bars`

**Action Icons**:
- Edit: `fa-pen-to-square`
- Delete: `fa-trash-can`
- Add: `fa-plus`
- Close: `fa-xmark`
- Search: `fa-magnifying-glass`
- Filter: `fa-filter`
- Download: `fa-download`
- Upload: `fa-upload`

**Status Icons**:
- Success: `fa-circle-check`
- Error: `fa-circle-exclamation`
- Warning: `fa-triangle-exclamation`
- Info: `fa-circle-info`

---

### 5. Grid System and Spacing Units

**Use Bootstrap 5 Grid System**:

```html
<div class="container">           <!-- Fixed-width container -->
<div class="container-fluid">     <!-- Full-width container -->
<div class="container-lg">        <!-- Responsive container -->
```

**Grid Breakpoints** (Bootstrap defaults):
```css
/* Breakpoints */
xs: 0px        (default, mobile-first)
sm: 576px      (small devices)
md: 768px      (tablets)
lg: 992px      (desktops)
xl: 1200px     (large desktops)
xxl: 1400px    (extra large)

/* Usage */
<div class="col-12 col-md-6 col-lg-4">  /* Responsive columns */
```

**Dashboard Layout** (from screenshot):
```html
<!-- Stat cards: 4 columns on desktop -->
<div class="row g-3">
  <div class="col-12 col-sm-6 col-lg-3">
    <!-- Stat card -->
  </div>
  <!-- Repeat 4 times -->
</div>

<!-- Main content: Full width -->
<div class="row mt-4">
  <div class="col-12">
    <!-- Chart card -->
  </div>
</div>
```

**Spacing Scale**:

Use Bootstrap utilities exclusively:
- Margin: `m-{size}`, `mt-{size}`, `me-{size}`, `mb-{size}`, `ms-{size}`, `mx-{size}`, `my-{size}`
- Padding: `p-{size}`, `pt-{size}`, `pe-{size}`, `pb-{size}`, `ps-{size}`, `px-{size}`, `py-{size}`
- Gap: `gap-{size}`, `row-gap-{size}`, `column-gap-{size}`

Sizes: `0, 1, 2, 3, 4, 5` (where 3 = 1rem = 16px)

**Common Spacing Patterns**:
```html
<!-- Card padding -->
<div class="card">
  <div class="card-body p-3">  <!-- 16px padding -->

<!-- Section gaps -->
<section class="mb-4">         <!-- 24px bottom margin -->

<!-- Inline spacing -->
<button class="btn btn-primary me-2">  <!-- 8px right margin -->
```

---

## Skeleton & Layout

### 1. Information Design

**Information Hierarchy Principles**:

1. **Visual hierarchy**: Use size, weight, color to guide attention
2. **Progressive disclosure**: Show essential info first, details on demand
3. **Grouping**: Related items visually clustered
4. **Scannable layouts**: F-pattern reading, clear headings

**Dashboard Information Architecture** (from screenshot):

```
Page Structure:
├── Top Navigation (persistent)
│   ├── Left: Hamburger menu + nav links (Dashboard, Users, Settings)
│   └── Right: Dark mode toggle + notification badges + user avatar
├── Breadcrumbs (Home / Admin / Dashboard)
├── Page Actions (right-aligned: Dashboard, Settings buttons)
├── Stat Cards (4-column grid, primary metrics)
├── Chart Section (full-width, detailed analytics)
└── Chart Legend (metrics breakdown below chart)
```

**Content Prioritization**:
- **Primary**: Key metrics (stat cards), main content (chart)
- **Secondary**: Navigation, breadcrumbs, filters
- **Tertiary**: Settings, help, user profile

---

### 2. Base Layouts

#### 2-Column Layout (Content + Metadata Sidebar)

**Use Case**: Detail pages with contextual information (NOT for navigation)

**Note**: All navigation happens via top navbar. Sidebars are ONLY for metadata, filters, or related content.

```html
<div class="container-fluid">
  <div class="row">
    <!-- Main content: Primary area -->
    <main class="col-lg-9 col-xl-10">
      <!-- Page content -->
    </main>
    
    <!-- Metadata sidebar: 3 columns on large screens -->
    <aside class="col-lg-3 col-xl-2">
      <!-- Filters, metadata, related info -->
      <!-- NO navigation links -->
    </aside>
  </div>
</div>
```

**Sidebar Behavior**:
- Desktop (lg+): Fixed width sidebar, always visible
- Tablet (md): Collapsible sidebar, toggle button
- Mobile (sm): Stack below content or collapsible panel

#### 3-Column Layout (Filters + Content + Metadata)

**Use Case**: Content with contextual information on both sides (playbook editor with filters and metadata)

**Note**: All navigation still happens via top navbar. Both sidebars are for content organization only.

```html
<div class="container-fluid">
  <div class="row">
    <!-- Left sidebar: Filters, Quick actions (2-3 columns) -->
    <aside class="col-lg-2">
      <!-- Filters, tags, quick actions -->
      <!-- NO navigation links -->
    </aside>
    
    <!-- Main content: Primary area (6-8 columns) -->
    <main class="col-lg-8">
      <!-- Content -->
    </main>
    
    <!-- Right sidebar: Metadata (2-3 columns) -->
    <aside class="col-lg-2">
      <!-- Related info, version history, metadata -->
    </aside>
  </div>
</div>
```

**Responsive Behavior**:
- Desktop: All 3 columns visible
- Tablet: Left sidebar collapses, 2-column layout
- Mobile: Stack vertically, hide sidebars in collapsible panels

#### Grid Layout (Dashboard Cards)

**Use Case**: Dashboards, card galleries, product listings

```html
<div class="container-fluid">
  <!-- Stat cards -->
  <div class="row g-3 mb-4">
    <div class="col-12 col-sm-6 col-lg-3">
      <div class="card stat-card"><!-- Card --></div>
    </div>
    <!-- Repeat 4 times -->
  </div>
  
  <!-- Full-width chart -->
  <div class="row">
    <div class="col-12">
      <div class="card chart-card"><!-- Chart --></div>
    </div>
  </div>
</div>
```

**Grid Variations**:
- 4-column: `col-lg-3` (dashboards, small cards)
- 3-column: `col-lg-4` (product cards, medium content)
- 2-column: `col-lg-6` (large cards, detailed content)
- Masonry: Use Bootstrap utilities + custom CSS for uneven heights

#### Form Layouts

**Use Case**: Data entry, settings, user input

**Note**: Mimir does NOT use Django Forms. We build custom views and templates with manual validation.

```html
<!-- Vertical form (default) -->
<form>
  <div class="mb-3">
    <label for="email" class="form-label">Email address</label>
    <input type="email" class="form-control" id="email">
  </div>
  <div class="mb-3">
    <label for="password" class="form-label">Password</label>
    <input type="password" class="form-control" id="password">
  </div>
  <button type="submit" class="btn btn-primary">Submit</button>
</form>

<!-- Horizontal form (labels beside inputs) -->
<form>
  <div class="row mb-3">
    <label for="email" class="col-sm-3 col-form-label">Email</label>
    <div class="col-sm-9">
      <input type="email" class="form-control" id="email">
    </div>
  </div>
</form>

<!-- Inline form (compact, single line) -->
<form class="row g-3">
  <div class="col-auto">
    <input type="text" class="form-control" placeholder="Search...">
  </div>
  <div class="col-auto">
    <button type="submit" class="btn btn-primary">Search</button>
  </div>
</form>
```

#### Form Validation and Error Handling

**Validation Strategy**: Server-side validation in Django views with Bootstrap styling.

**Field-Level Validation Errors**:

Show validation errors **underneath the invalid field** in red with icon.

```html
<!-- Invalid field with error message -->
<div class="mb-3">
  <label for="email" class="form-label">Email address</label>
  <input type="email" 
         class="form-control is-invalid" 
         id="email" 
         value="invalidemail">
  <div class="invalid-feedback">
    <i class="fa-solid fa-circle-exclamation me-1"></i>
    This field is required.
  </div>
</div>

<!-- Multiple validation errors -->
<div class="mb-3">
  <label for="password" class="form-label">Password</label>
  <input type="password" 
         class="form-control is-invalid" 
         id="password">
  <div class="invalid-feedback">
    <i class="fa-solid fa-circle-exclamation me-1"></i>
    Password must be at least 8 characters long.
  </div>
</div>

<!-- Valid field (optional success state) -->
<div class="mb-3">
  <label for="username" class="form-label">Username</label>
  <input type="text" 
         class="form-control is-valid" 
         id="username" 
         value="maria">
  <div class="valid-feedback">
    <i class="fa-solid fa-circle-check me-1"></i>
    Username is available.
  </div>
</div>
```

**Common Validation Messages**:
- Required fields: `"This field is required."`
- Invalid email: `"Please enter a valid email address."`
- Password strength: `"Password must be at least 8 characters long."`
- Unique constraint: `"This username is already taken."`
- Number range: `"Value must be between 1 and 100."`
- Date validation: `"Please enter a valid date."`

**Form-Level Validation Errors**:

For errors that don't belong to specific fields (e.g., "Invalid credentials"):

```html
<!-- Error alert at top of form -->
<div class="alert alert-danger alert-dismissible fade show" role="alert">
  <i class="fa-solid fa-triangle-exclamation me-2"></i>
  <strong>Authentication failed:</strong> Invalid email or password.
  <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
</div>
```

---

### 3. Liquid vs Fixed Layouts, Breakpoints

**Layout Strategy**: Liquid (fluid) layouts using Bootstrap's responsive containers

**Container Types**:
```css
.container          /* Fixed-width, centered, responsive breakpoints */
.container-fluid    /* Full-width, 100% at all breakpoints */
.container-{breakpoint}  /* Fluid until breakpoint, then fixed */
```

**Mimir Default**: Use `.container-fluid` for admin/dashboard interfaces (maximize screen real estate)

**Breakpoints** (Bootstrap standard):
```css
/* No fixed breakpoints for Mimir - fully responsive */
xs: 0px      → Mobile portrait
sm: 576px    → Mobile landscape
md: 768px    → Tablet
lg: 992px    → Desktop
xl: 1200px   → Large desktop
xxl: 1400px  → Extra large desktop
```

**Content Max-Width**:
```css
/* For readability, constrain text-heavy content */
.content-readable {
  max-width: 65ch; /* ~65 characters per line */
}

.content-max {
  max-width: 1200px; /* Maximum content width */
  margin: 0 auto;
}
```

---

### 4. Navigation Design

#### Top Navigation (Primary)

From dashboard screenshot:

```html
<nav class="navbar navbar-expand-lg navbar-light bg-white shadow-sm">
  <div class="container-fluid">
    <!-- Hamburger menu (mobile) -->
    <button class="navbar-toggler">
      <i class="fa-solid fa-bars"></i>
    </button>
    
    <!-- Brand/Logo -->
    <a class="navbar-brand" href="/">Mimir</a>
    
    <!-- Main navigation links (left) -->
    <div class="collapse navbar-collapse">
      <ul class="navbar-nav me-auto">
        <li class="nav-item">
          <a class="nav-link active" href="/dashboard">Dashboard</a>
        </li>
        <li class="nav-item">
          <a class="nav-link" href="/users">Users</a>
        </li>
        <li class="nav-item">
          <a class="nav-link" href="/settings">Settings</a>
        </li>
      </ul>
      
      <!-- Utility items (right) -->
      <ul class="navbar-nav ms-auto">
        <!-- Dark mode toggle -->
        <li class="nav-item">
          <button class="btn btn-link nav-link" id="darkModeToggle">
            <i class="fa-solid fa-moon"></i>
          </button>
        </li>
        
        <!-- Notifications (with badge) -->
        <li class="nav-item">
          <a class="nav-link position-relative" href="/notifications">
            <i class="fa-solid fa-bell"></i>
            <span class="badge bg-danger rounded-pill position-absolute">3</span>
          </a>
        </li>
        
        <!-- Messages (with badge) -->
        <li class="nav-item">
          <a class="nav-link position-relative" href="/messages">
            <i class="fa-solid fa-envelope"></i>
            <span class="badge bg-warning rounded-pill position-absolute">113</span>
          </a>
        </li>
        
        <!-- Activity/Tasks (with badge) -->
        <li class="nav-item">
          <a class="nav-link position-relative" href="/activity">
            <i class="fa-solid fa-list-check"></i>
            <span class="badge bg-info rounded-pill position-absolute">7</span>
          </a>
        </li>
        
        <!-- User menu -->
        <li class="nav-item dropdown">
          <a class="nav-link dropdown-toggle" href="#" data-bs-toggle="dropdown">
            <img src="/avatar.jpg" class="rounded-circle" width="32" height="32">
          </a>
          <ul class="dropdown-menu dropdown-menu-end">
            <li><a class="dropdown-item" href="/profile">My Profile</a></li>
            <li><a class="dropdown-item" href="/settings">Settings</a></li>
            <li><hr class="dropdown-divider"></li>
            <li><a class="dropdown-item" href="/logout">Log Out</a></li>
          </ul>
        </li>
      </ul>
    </div>
  </div>
</nav>
```

**Navigation States**:
- **Active**: `.nav-link.active` (bold, primary color, lighter background)
  - Applied dynamically based on current `request.path`
  - Single page sections: Use exact path match (e.g., `request.path == '/dashboard/'`)
  - Multi-page sections: Use path contains check (e.g., `'/playbooks/' in request.path`)
  - Must include `aria-current="page"` attribute for accessibility
- **Hover**: Background tint (Bootstrap default)
- **Focus**: Visible outline for accessibility (Bootstrap default)
- **Disabled**: `.nav-link.disabled` (grayed out, no hover effect, `href="#"`)

#### Breadcrumbs (Secondary)

```html
<nav aria-label="breadcrumb">
  <ol class="breadcrumb">
    <li class="breadcrumb-item"><a href="/">Home</a></li>
    <li class="breadcrumb-item"><a href="/admin">Admin</a></li>
    <li class="breadcrumb-item active" aria-current="page">Dashboard</li>
  </ol>
</nav>
```

#### Dropdown Menus (For Grouped Navigation)

**For apps with deep hierarchies, use navbar dropdowns instead of sidebars**:

```html
<!-- In top navbar -->
<li class="nav-item dropdown">
  <a class="nav-link dropdown-toggle" href="#" data-bs-toggle="dropdown">
    <i class="fa-solid fa-sync me-2"></i>
    Sync
  </a>
  <ul class="dropdown-menu">
    <li><a class="dropdown-item" href="/sync/status">
      <i class="fa-solid fa-circle-check me-2"></i>
      Status
    </a></li>
    <li><a class="dropdown-item" href="/sync/history">
      <i class="fa-solid fa-clock-rotate-left me-2"></i>
      History
    </a></li>
    <li><hr class="dropdown-divider"></li>
    <li><a class="dropdown-item" href="/sync/settings">
      <i class="fa-solid fa-gear me-2"></i>
      Settings
    </a></li>
  </ul>
</li>
```

#### Tabs (Content Navigation)

```html
<ul class="nav nav-tabs" role="tablist">
  <li class="nav-item" role="presentation">
    <button class="nav-link active" data-bs-toggle="tab" data-bs-target="#overview">
      Overview
    </button>
  </li>
  <li class="nav-item" role="presentation">
    <button class="nav-link" data-bs-toggle="tab" data-bs-target="#activities">
      Activities
    </button>
  </li>
  <li class="nav-item" role="presentation">
    <button class="nav-link" data-bs-toggle="tab" data-bs-target="#settings">
      Settings
    </button>
  </li>
</ul>

<div class="tab-content">
  <div class="tab-pane fade show active" id="overview"><!-- Content --></div>
  <div class="tab-pane fade" id="activities"><!-- Content --></div>
  <div class="tab-pane fade" id="settings"><!-- Content --></div>
</div>
```

#### Navbar Entity Links & Feature Wiring

**Current Navbar Structure** (`templates/base.html`):

**Active Links:**
- **Mimir** (brand/home) - `/` - ✅ Implemented
- **Dashboard** - `/dashboard/` - Icon: `fa-gauge` - ✅ Implemented
- **Playbooks** - `/playbooks/` - Icon: `fa-book-sparkles` - ✅ Implemented
- **User Menu** - Login/Logout - ✅ Implemented

**Placeholder Links (Disabled - Coming Soon):**
- **Workflows** - Icon: `fa-arrow-progress` - Tooltip: "Coming soon: View workflows across playbooks"
- **Phases** - Icon: `fa-bars-progress` - Tooltip: "Coming soon: Manage workflow phases"
- **Activities** - Icon: `fa-list-check` - Tooltip: "Coming soon: Browse all activities"
- **Artifacts** - Icon: `fa-gift` - Tooltip: "Coming soon: Manage artifacts and deliverables"
- **Roles** - Icon: `fa-brain` - Tooltip: "Coming soon: Define and assign roles"
- **Skills** - Icon: `fa-hand-holding-magic` - Tooltip: "Coming soon: Browse skill guides"
- **PIPs** - Icon: `fa-lightbulb` - Tooltip: "Coming soon: Global PIPs list (currently accessed via Playbook tabs)"

**Feature Wiring Pattern:**

When a feature block is complete, add navbar scenarios to its `.feature` file:

```gherkin
# ============================================================
# NAVBAR INTEGRATION - Wire when [Feature] block is complete
# ============================================================

Scenario: [FEATURE]-NAVBAR-01 [Feature] link appears in main navigation
  Given the [Feature] feature is fully implemented
  And Maria is authenticated in FOB
  When she views any page in FOB
  Then she sees "[Feature]" link in the main navbar
  And the link has icon "[fa-icon-name]"
  And the link has tooltip "[Helpful tooltip text]"
  
Scenario: [FEATURE]-NAVBAR-02 Navigate to [Feature] from any page
  Given Maria is authenticated in FOB
  And she is on any page in FOB
  When she clicks "[Feature]" in the main navbar
  Then she is redirected to FOB-[FEATURE]-[PAGE]-1
  And the [Feature] nav link is highlighted as active
```

**Activating Placeholder Links (4 steps):**

1. Remove `disabled` class from `<a>` tag
2. Change `href="#"` to actual route (e.g., `href="/workflows/"`)
3. Update tooltip from "Coming soon: ..." to active description
4. Ensure NAVBAR scenarios pass in integration tests

**Navbar Link Requirements:**
- ✅ Font Awesome Pro icon (semantically appropriate)
- ✅ Bootstrap tooltip explaining action/status
- ✅ `data-testid="nav-[feature]"` attribute
- ✅ Active state highlighting when on feature pages

**Active State Implementation:**

```django
{# Single-page section (exact match) #}
<a class="nav-link {% if request.path == '/dashboard/' %}active{% endif %}" 
   href="/dashboard/"
   {% if request.path == '/dashboard/' %}aria-current="page"{% endif %}>
    <i class="fas fa-gauge"></i> Dashboard
</a>

{# Multi-page section (contains check) #}
<a class="nav-link {% if '/playbooks/' in request.path %}active{% endif %}" 
   href="/playbooks/"
   {% if '/playbooks/' in request.path %}aria-current="page"{% endif %}>
    <i class="fas fa-book-sparkles"></i> Playbooks
</a>
```

**Icon Selection:**
- Dashboard: `fa-gauge` (metrics/overview)
- Playbooks: `fa-book-sparkles` (curated collections)
- Workflows: `fa-arrow-progress` (progression through steps)
- Phases: `fa-bars-progress` (sequential progress through stages)
- Activities: `fa-list-check` (task checklists)
- Artifacts: `fa-gift` (deliverables/outputs)
- Roles: `fa-brain` (knowledge/thinking/expertise)
- Skills: `fa-hand-holding-magic` (guidance/teaching)
- PIPs: `fa-lightbulb` (ideas/improvements)

**Icon Rationale:**
- **Workflows** (`fa-arrow-progress`): Represents forward movement through a process
- **Phases** (`fa-bars-progress`): Shows multiple bars for distinct sequential stages
- **Artifacts** (`fa-gift`): Deliverables are "gifts" produced by the process
- **Roles** (`fa-brain`): Emphasizes expertise and cognitive work
- **Skills** (`fa-hand-holding-magic`): Conveys assistance and enabling knowledge transfer

---

### 5. Interface Design

#### Dashboard Interface Pattern

From screenshot analysis:

**Structure**:
1. **Top bar**: Navigation + utilities (fixed/sticky)
2. **Breadcrumbs**: Context navigation (below top bar)
3. **Page header**: Title + actions (right-aligned buttons)
4. **Stat cards**: KPI grid (4 columns)
5. **Main content**: Charts, tables, content areas
6. **Footer**: Optional, minimal

**Code Pattern**:
```html
<!-- Top navigation (sticky) -->
<nav class="navbar sticky-top">...</nav>

<!-- Page container -->
<div class="container-fluid p-4">
  <!-- Breadcrumbs -->
  <nav aria-label="breadcrumb" class="mb-3">...</nav>
  
  <!-- Page header -->
  <div class="d-flex justify-content-between align-items-center mb-4">
    <h1 class="h3 mb-0">Dashboard</h1>
    <div class="btn-group">
      <button class="btn btn-outline-secondary">
        <i class="fa-solid fa-chart-line me-2"></i>
        Dashboard
      </button>
      <button class="btn btn-outline-secondary">
        <i class="fa-solid fa-gear me-2"></i>
        Settings
      </button>
    </div>
  </div>
  
  <!-- Stat cards -->
  <div class="row g-3 mb-4">
    <!-- 4 stat cards -->
  </div>
  
  <!-- Main content -->
  <div class="row">
    <div class="col-12">
      <div class="card">
        <!-- Chart content -->
      </div>
    </div>
  </div>
</div>
```

#### Page Action Patterns

**Right-aligned actions** (from screenshot):
```html
<div class="d-flex justify-content-between align-items-center">
  <h1>Page Title</h1>
  <div>
    <button class="btn btn-outline-primary me-2">
      <i class="fa-solid fa-download me-2"></i>
      Export
    </button>
    <button class="btn btn-primary">
      <i class="fa-solid fa-plus me-2"></i>
      Create New
    </button>
  </div>
</div>
```

**Filter patterns**:
```html
<!-- Filter row above content -->
<div class="d-flex gap-2 mb-3">
  <button class="btn btn-outline-secondary active">Day</button>
  <button class="btn btn-outline-secondary">Month</button>
  <button class="btn btn-outline-secondary">Year</button>
  <button class="btn btn-primary ms-auto">
    <i class="fa-solid fa-filter"></i>
  </button>
</div>
```

---

### 6. Semantic Markup

**Always use semantic HTML5 elements**:

```html
<!-- Page structure -->
<header>      <!-- Top navigation, page header -->
<nav>         <!-- Navigation menus, breadcrumbs -->
<main>        <!-- Primary page content -->
<article>     <!-- Independent content (blog post, playbook) -->
<section>     <!-- Thematic grouping of content -->
<aside>       <!-- Contextual content, metadata (NOT navigation) -->
<footer>      <!-- Page footer, copyright -->

<!-- Content structure -->
<h1> to <h6>  <!-- Headings (maintain hierarchy) -->
<p>           <!-- Paragraphs -->
<ul>, <ol>, <li>  <!-- Lists -->
<dl>, <dt>, <dd>  <!-- Definition lists -->
<table>       <!-- Tabular data only -->
<form>        <!-- User input -->
<button>      <!-- Interactive buttons (not <a> styled as button) -->
<a>           <!-- Navigation links (not buttons styled as links) -->
```

**Accessibility Requirements**:
- `role` attributes for ARIA landmarks
- `aria-label` for context
- `alt` text for images
- Keyboard navigation support
- Focus indicators
- Screen reader friendly

---

### 7. Layout Skeletons and Wireframes

#### Dashboard Skeleton (from screenshot)

```
┌─────────────────────────────────────────────────────────────┐
│ [☰] Logo    Dashboard  Users  Settings    [🌙][🔔3][✉️113][👤]│ Top Nav
├─────────────────────────────────────────────────────────────┤
│ Home / Admin / Dashboard          [📊 Dashboard][⚙️Settings]│ Breadcrumb + Actions
├─────────────────────────────────────────────────────────────┤
│ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐           │
│ │ 9,823   │ │ 9,823   │ │ 9,823   │ │ 9,823   │           │ Stat Cards
│ │Members  │ │Members  │ │Members  │ │Members  │           │
│ │online   │ │online   │ │online   │ │online   │           │
│ │ [chart] │ │ [chart] │ │ [chart] │ │ [chart] │           │
│ └─────────┘ └─────────┘ └─────────┘ └─────────┘           │
├─────────────────────────────────────────────────────────────┤
│ Traffic                          [Day][Month][Year][Filter] │
│ September 2019                                              │
│ ┌───────────────────────────────────────────────────────┐  │
│ │                                                        │  │
│ │                  [Line Chart]                         │  │ Main Chart
│ │                                                        │  │
│ │                                                        │  │
│ └───────────────────────────────────────────────────────┘  │
│ 29.703 Users (40%) | 24.093 Users (20%) | 78.706 Views...  │ Legend
└─────────────────────────────────────────────────────────────┘
```

#### Detail Page Skeleton

```
┌─────────────────────────────────────────────┐
│ Top Navigation                              │
├────────┬────────────────────────────────────┤
│ Side   │ Breadcrumbs                        │
│ bar    ├────────────────────────────────────┤
│        │ Page Title          [Actions]      │
│ Nav    ├────────────────────────────────────┤
│ Menu   │                                    │
│        │ Main Content Area                  │
│        │                                    │
│        │                                    │
└────────┴────────────────────────────────────┘
```

---

### 8. Responsive Behavior at Each Breakpoint

#### Extra Small (xs: 0-575px) - Mobile

- Stack all columns vertically
- Hide sidebars (off-canvas)
- Hamburger menu for navigation
- Full-width cards
- Simplified tables (card view)
- Touch-friendly targets (min 44x44px)

```html
<!-- Stat cards: Stack on mobile -->
<div class="col-12 col-sm-6 col-lg-3">
  <div class="card">...</div>
</div>
```

#### Small (sm: 576-767px) - Mobile Landscape

- 2-column stat cards
- Collapsible sections
- Condensed navigation
- Medium-sized touch targets

```html
<!-- 2 columns on small devices -->
<div class="col-12 col-sm-6 col-lg-3">
```

#### Medium (md: 768-991px) - Tablet

- 2-3 column layouts
- Sidebar becomes collapsible
- Full navigation visible
- Hover states enabled

```html
<!-- 3 columns on tablets -->
<div class="col-12 col-sm-6 col-md-4 col-lg-3">
```

#### Large (lg: 992-1199px) - Desktop

- 3-4 column layouts
- Fixed sidebar
- Full feature set
- Hover, tooltips enabled
- Keyboard shortcuts

```html
<!-- 4 columns on desktop -->
<div class="col-lg-3">
```

#### Extra Large (xl: 1200+px) - Large Desktop

- Maximum 4-5 columns
- Optimal spacing
- All features visible
- No truncation needed

**Responsive Utilities**:
```html
<!-- Show/hide at breakpoints -->
<div class="d-none d-lg-block">Desktop only</div>
<div class="d-lg-none">Mobile/Tablet only</div>

<!-- Responsive text alignment -->
<div class="text-center text-lg-start">
```

---

## Visual Design

### 1. Colors

#### Color Palette

**Primary Colors** (Bootstrap semantic):
- **Primary**: `#0d6efd` - Links, primary actions, focus states
- **Success**: `#198754` - Confirmations, positive states
- **Danger**: `#dc3545` - Errors, destructive actions, alerts
- **Warning**: `#ffc107` - Warnings, caution states
- **Info**: `#0dcaf0` - Informational messages, tooltips

**Dashboard Stat Card Colors** (from screenshot):
- **Purple**: `#5856d6` - Category indicator
- **Blue**: `#38a9f0` - Category indicator
- **Orange**: `#ffa726` - Category indicator  
- **Red**: `#ef5350` - Category indicator

**Neutral Colors**:
- **Gray-100 to Gray-900**: Background layers, borders, text
- **White**: `#ffffff` - Cards, modals, elevated surfaces
- **Black**: `#000000` - Used sparingly for text

#### Usage Guidelines

**Backgrounds**:
```css
/* Page background */
body { background-color: var(--bs-gray-100); /* #f8f9fa */ }

/* Card/surface */
.card { background-color: var(--bs-white); }

/* Content sidebars (metadata, filters - NOT navigation) */
.content-sidebar { background-color: var(--bs-light); /* #f8f9fa */ }

/* Stat cards - colored backgrounds */
.stat-card-purple { background: linear-gradient(135deg, #5856d6 0%, #7c7aec 100%); }
.stat-card-blue { background: linear-gradient(135deg, #38a9f0 0%, #64c3ff 100%); }
.stat-card-orange { background: linear-gradient(135deg, #ffa726 0%, #ffb74d 100%); }
.stat-card-red { background: linear-gradient(135deg, #ef5350 0%, #f77673 100%); }
```

**Text Colors**:
```css
/* Primary text */
.text-body { color: var(--bs-body-color); /* #212529 */ }

/* Secondary/muted text */
.text-muted { color: var(--bs-secondary-color); /* #6c757d */ }

/* On colored backgrounds - white text */
.stat-card { color: #ffffff; }
```

**Interactive Elements**:
- **Links**: Primary blue (#0d6efd)
- **Hover**: Darken 10%
- **Active**: Darken 15%
- **Disabled**: Gray-400 (#ced4da)

#### Contrast Ratios (WCAG AA Compliance)

**Minimum Requirements**:
- Normal text: 4.5:1
- Large text (18px+): 3:1
- UI components: 3:1

**Verified Combinations**:
- White text on primary blue: ✓ 4.6:1
- Gray-900 on white: ✓ 15.3:1
- Gray-600 on white: ✓ 4.5:1
- White on stat card colors: ✓ 4.5:1+

---

### 2. Typography

#### Type Scale

**Bootstrap Default Scale** (modular scale ~1.25):
```css
h1, .h1 { font-size: 2.5rem; font-weight: 500; }   /* 40px */
h2, .h2 { font-size: 2rem; font-weight: 500; }     /* 32px */
h3, .h3 { font-size: 1.75rem; font-weight: 500; }  /* 28px */
h4, .h4 { font-size: 1.5rem; font-weight: 500; }   /* 24px */
h5, .h5 { font-size: 1.25rem; font-weight: 500; }  /* 20px */
h6, .h6 { font-size: 1rem; font-weight: 500; }     /* 16px */

body { font-size: 1rem; font-weight: 400; }         /* 16px */
small, .small { font-size: 0.875rem; }              /* 14px */
```

**Custom Sizes**:
```css
.text-xs { font-size: 0.75rem; }    /* 12px - badges, labels */
.text-sm { font-size: 0.875rem; }   /* 14px - secondary text */
.text-lg { font-size: 1.125rem; }   /* 18px - emphasis */
.text-xl { font-size: 1.25rem; }    /* 20px - sub-headings */
  
/* Stat card large numbers */
.stat-number { 
  font-size: 2.5rem;     /* 40px */
  font-weight: 600;
  line-height: 1.2;
}
```

#### Typography Hierarchy

**Page Title**: h1 or .h3 (dashboard uses .h3)
```html
<h1 class="h3 mb-4">Dashboard</h1>
```

**Section Headings**: h2 or .h5
```html
<h2 class="h5 mb-3">Traffic</h2>
```

**Card Titles**: h3 or .h6
```html
<h3 class="h6 mb-2">Members online</h3>
```

**Body Text**: Default 1rem (16px)
```html
<p>Regular paragraph text</p>
```

**Small Text**: .small or .text-muted
```html
<small class="text-muted">September 2019</small>
```

#### Line Heights

```css
/* Headings - tighter leading */
h1, h2, h3, h4, h5, h6 {
  line-height: 1.2;
}

/* Body text - comfortable reading */
body, p {
  line-height: 1.5;  /* 24px at 16px font size */
}

/* Dense UI elements */
.btn, .badge, .alert {
  line-height: 1.5;
}
```

#### Font Weights

**Bootstrap Utilities**:
```css
.fw-light { font-weight: 300; }      /* Light text, rarely used */
.fw-normal { font-weight: 400; }     /* Body text, default */
.fw-medium { font-weight: 500; }     /* Headings, semi-bold */
.fw-semibold { font-weight: 600; }   /* Emphasized headings */
.fw-bold { font-weight: 700; }       /* Strong emphasis */
```

**Usage**:
- Body text: 400 (normal)
- Headings: 500 (medium) or 600 (semibold)
- Stat numbers: 600 (semibold)
- Buttons: 500 (medium)
- Strong emphasis: 700 (bold)

---

### 3. Controls

#### Buttons

**Primary Actions**:
```html
<button class="btn btn-primary">
  <i class="fa-solid fa-save me-2"></i>
  Save Changes
</button>
```

**Secondary Actions**:
```html
<button class="btn btn-outline-secondary">
  <i class="fa-solid fa-filter me-2"></i>
  Filter
</button>
```

**Danger Actions**:
```html
<button class="btn btn-danger">
  <i class="fa-solid fa-trash me-2"></i>
  Delete
</button>
```

**Button Sizes**:
```html
<button class="btn btn-primary btn-sm">Small</button>
<button class="btn btn-primary">Default</button>
<button class="btn btn-primary btn-lg">Large</button>
```

**Button Groups** (from dashboard):
```html
<div class="btn-group">
  <button class="btn btn-outline-secondary active">Day</button>
  <button class="btn btn-outline-secondary">Month</button>
  <button class="btn btn-outline-secondary">Year</button>
</div>
```

#### Inputs

**Text Input**:
```html
<div class="mb-3">
  <label for="username" class="form-label">Username</label>
  <input type="text" class="form-control" id="username" 
         placeholder="Enter username">
</div>
```

**Input with Icon**:
```html
<div class="input-group">
  <span class="input-group-text">
    <i class="fa-solid fa-magnifying-glass"></i>
  </span>
  <input type="text" class="form-control" placeholder="Search...">
</div>
```

**Select**:
```html
<select class="form-select">
  <option selected>Choose...</option>
  <option value="1">Option 1</option>
  <option value="2">Option 2</option>
</select>
```

#### Toggles

**Checkbox**:
```html
<div class="form-check">
  <input class="form-check-input" type="checkbox" id="remember">
  <label class="form-check-label" for="remember">
    Remember me
  </label>
</div>
```

**Switch**:
```html
<div class="form-check form-switch">
  <input class="form-check-input" type="checkbox" id="darkMode">
  <label class="form-check-label" for="darkMode">
    Dark Mode
  </label>
</div>
```

**Radio Buttons**:
```html
<div class="form-check">
  <input class="form-check-input" type="radio" name="visibility" id="public">
  <label class="form-check-label" for="public">
    Public
  </label>
</div>
```

---

### 4. Semantics: States

#### Active vs Inactive

**Navigation**:
```css
.nav-link { color: var(--bs-gray-600); }
.nav-link.active { 
  color: var(--bs-primary); 
  font-weight: 600; 
}
```

**Buttons**:
```css
.btn-outline-secondary { background: transparent; }
.btn-outline-secondary.active { 
  background: var(--bs-secondary); 
  color: white; 
}
```

**Tabs**:
```css
.nav-tabs .nav-link { border-bottom: 2px solid transparent; }
.nav-tabs .nav-link.active { 
  border-bottom-color: var(--bs-primary); 
  color: var(--bs-primary);
}
```

#### Disabled State

**Buttons**:
```css
.btn:disabled {
  opacity: 0.65;
  cursor: not-allowed;
  pointer-events: none;
}
```

```html
<button class="btn btn-primary" disabled 
        data-bs-toggle="tooltip" 
        title="Fill in required fields to enable">
  <i class="fa-solid fa-save me-2"></i>
  Save
</button>
```

**Inputs**:
```css
.form-control:disabled {
  background-color: var(--bs-gray-200);
  opacity: 1;
  cursor: not-allowed;
}
```

**Links**:
```css
.nav-link.disabled {
  color: var(--bs-gray-400);
  pointer-events: none;
  cursor: default;
}
```

#### Focus State

**Accessibility Requirement**: All interactive elements must have visible focus indicators

```css
/* Bootstrap default focus */
.form-control:focus {
  border-color: var(--bs-primary);
  box-shadow: 0 0 0 0.25rem rgba(13, 110, 253, 0.25);
}

.btn:focus {
  box-shadow: 0 0 0 0.25rem rgba(13, 110, 253, 0.5);
}

/* Custom focus for cards */
.card:focus-within {
  outline: 2px solid var(--bs-primary);
  outline-offset: 2px;
}
```

#### Hover State

**Buttons**:
```css
.btn-primary:hover {
  background-color: darken(var(--bs-primary), 10%);
  border-color: darken(var(--bs-primary), 10%);
}
```

**Cards**:
```css
.card:hover {
  box-shadow: var(--mimir-card-shadow-hover);
  transform: translateY(-2px);
  transition: all 0.2s ease;
}
```

**Links**:
```css
.nav-link:hover {
  color: var(--bs-primary);
  background-color: var(--bs-gray-100);
}
```

---

### 5. Styling for Skeleton Elements

#### Cards

**Stat Card** (from dashboard):
```css
.stat-card {
  background: linear-gradient(135deg, var(--card-color-start), var(--card-color-end));
  color: white;
  border: none;
  border-radius: 0.5rem;
  padding: 1.5rem;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  position: relative;
  overflow: hidden;
}

.stat-card-number {
  font-size: 2.5rem;
  font-weight: 600;
  line-height: 1.2;
  margin-bottom: 0.5rem;
}

.stat-card-label {
  font-size: 0.875rem;
  opacity: 0.9;
  text-transform: capitalize;
}

.stat-card-icon {
  position: absolute;
  top: 1rem;
  right: 1rem;
  opacity: 0.3;
}

.stat-card-chart {
  margin-top: 1rem;
  height: 60px;
}
```

**Standard Card**:
```css
.card {
  background: white;
  border: none;
  border-radius: 0.5rem;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.08);
}

.card-header {
  background: transparent;
  border-bottom: 1px solid var(--bs-gray-200);
  padding: 1rem 1.25rem;
}

.card-body {
  padding: 1.25rem;
}
```

#### Navigation Bar

```css
.navbar {
  background: white;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  padding: 0.75rem 1rem;
}

.navbar-brand {
  font-size: 1.25rem;
  font-weight: 600;
}

.nav-link {
  color: var(--bs-gray-700);
  padding: 0.5rem 1rem;
  transition: all 0.2s ease;
}

.nav-link:hover {
  color: var(--bs-primary);
  background: var(--bs-gray-100);
  border-radius: 0.375rem;
}

.nav-link.active {
  color: var(--bs-primary);
  font-weight: 600;
}
```

#### Badges (Notification Count)

```css
.badge {
  font-size: 0.75rem;
  font-weight: 600;
  padding: 0.25em 0.5em;
  border-radius: 50rem;
}

/* Positioned badge on nav icons */
.nav-item .badge {
  position: absolute;
  top: 0;
  right: 0;
  transform: translate(25%, -25%);
  min-width: 1.25rem;
  height: 1.25rem;
  display: flex;
  align-items: center;
  justify-content: center;
}
```

#### Charts

```css
.chart-container {
  position: relative;
  height: 400px;
  padding: 1.5rem;
}

.chart-title {
  font-size: 1.25rem;
  font-weight: 600;
  margin-bottom: 0.5rem;
}

.chart-subtitle {
  font-size: 0.875rem;
  color: var(--bs-gray-600);
  margin-bottom: 1.5rem;
}

.chart-legend {
  display: flex;
  flex-wrap: wrap;
  gap: 1.5rem;
  padding: 1rem;
  border-top: 1px solid var(--bs-gray-200);
  margin-top: 1rem;
}

.chart-legend-item {
  display: flex;
  flex-direction: column;
  align-items: center;
}

.chart-legend-value {
  font-size: 1.125rem;
  font-weight: 600;
  color: var(--bs-gray-900);
}

.chart-legend-label {
  font-size: 0.875rem;
  color: var(--bs-gray-600);
}
```

---

### 6. Elevation and Depth

**Shadow Layers** (increasing elevation):

```css
/* Level 0: Flat, no shadow */
.elevation-0 { box-shadow: none; }

/* Level 1: Subtle lift (cards) */
.elevation-1 { box-shadow: 0 2px 4px rgba(0, 0, 0, 0.08); }

/* Level 2: Moderate lift (hover cards) */
.elevation-2 { box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15); }

/* Level 3: High lift (modals, dropdowns) */
.elevation-3 { box-shadow: 0 8px 24px rgba(0, 0, 0, 0.12); }

/* Level 4: Floating (tooltips, popovers) */
.elevation-4 { box-shadow: 0 12px 32px rgba(0, 0, 0, 0.18); }
```

**Usage**:
- Cards: elevation-1
- Hover cards: elevation-2
- Dropdowns: elevation-3
- Modals: elevation-3
- Tooltips: elevation-4
- Navigation bar: elevation-1 (subtle)

**Z-Index Layers**:
```css
/* Define clear z-index scale */
--z-base: 1;
--z-dropdown: 1000;
--z-sticky: 1020;
--z-fixed: 1030;
--z-modal-backdrop: 1040;
--z-modal: 1050;
--z-popover: 1060;
--z-tooltip: 1070;
```

---

### 7. Border Radius and Shape Language

**Border Radius Scale**:

```css
/* Bootstrap defaults */
--bs-border-radius-sm: 0.25rem;    /* 4px - small elements */
--bs-border-radius: 0.375rem;      /* 6px - default */
--bs-border-radius-lg: 0.5rem;     /* 8px - cards, large elements */
--bs-border-radius-xl: 1rem;       /* 16px - modals */
--bs-border-radius-pill: 50rem;    /* Fully rounded - badges, pills */
```

**Mimir Usage**:
- **Buttons**: 0.375rem (default)
- **Cards**: 0.5rem (lg)
- **Inputs**: 0.375rem (default)
- **Badges**: 50rem (pill)
- **Modals**: 0.5rem (lg)
- **Stat cards**: 0.5rem (lg)

**Consistency Rule**: Use `.rounded`, `.rounded-lg`, etc. utility classes instead of custom values

```html
<div class="card rounded-lg">...</div>
<span class="badge rounded-pill">3</span>
<button class="btn rounded">Click me</button>
```

---

# Mimir IA Guidelines - Part 2 (Continuation)

## Component Kit (Atomic Design)

### 1. Atoms (Basic Elements)

Atoms are the foundational building blocks - the smallest functional units.

#### Button Atom
```html
<button class="btn btn-primary" 
        data-bs-toggle="tooltip" 
        title="Save changes to the methodology">
  <i class="fa-solid fa-save me-2"></i>
  Save
</button>
```

**Variants**:
- `.btn-primary` - Primary action
- `.btn-secondary` - Secondary action
- `.btn-outline-primary` - Outlined primary
- `.btn-link` - Link style
- `.btn-sm`, `.btn-lg` - Size variants

**Placement (page actions)** — primary is always the **rightmost** control in the row; secondary actions sit **to its left** (LTR). Use `d-flex justify-content-end gap-2` (optionally `flex-wrap`) so groups align to the corner.

| Context | Corner | Order (left → right) |
|---------|--------|----------------------|
| **List pages** | Top-right of the page header (or filter toolbar row) | Secondary … Primary |
| **Create / edit forms** | Bottom-right of the form | e.g. Cancel → Save draft → Submit |
| **Read-only detail / view** | Top-right of the page header (same idea as list) | Secondary … Primary |

**Owned resource detail (e.g. playbook):** Put **Delete** (or equivalent destructive control) **leftmost** in the header button cluster so it is never mistaken for the primary action; keep **Back** **rightmost** when shown. Primary CTAs (e.g. Submit PIP on a released playbook) stay **rightmost before Back**.

```html
<!-- List or view header -->
<div class="d-flex justify-content-end gap-2 flex-wrap">
  <button type="button" class="btn btn-outline-secondary">Secondary</button>
  <a class="btn btn-primary" href="#">Primary</a>
</div>

<!-- Form footer -->
<div class="d-flex justify-content-end gap-2 flex-wrap mt-4">
  <a href="#" class="btn btn-outline-secondary">Cancel</a>
  <button type="submit" class="btn btn-outline-primary">Save draft</button>
  <button type="submit" class="btn btn-primary">Submit</button>
</div>
```

Modal footers follow the same rule: dismiss / cancel left, confirming primary action right.

**Dev-only mockups:** Static PIP wireframes under `/mockups/…` follow these placement rules for consistency with production templates. Those routes are registered only when `ENABLE_UI_MOCKUPS` is true (`mimir.settings.dev`); test and production settings leave it disabled so `/mockups/` returns 404.

#### Input Atom
```html
<input type="text" 
       class="form-control" 
       id="username"
       placeholder="Enter username"
       aria-label="Username">
```

#### Icon Atom
```html
<i class="fa-solid fa-user"></i>
<i class="fa-regular fa-heart"></i>
<i class="fa-light fa-gear"></i>
```

#### Label Atom
```html
<label for="email" class="form-label">Email address</label>
<label class="form-label required">
  Password
  <span class="text-danger">*</span>
</label>
```

#### Badge Atom
```html
<span class="badge bg-primary">New</span>
<span class="badge bg-danger rounded-pill">3</span>
<span class="badge bg-warning text-dark">Pending</span>
```

---

### 2. Molecules (Simple Combinations)

Molecules combine atoms into simple functional groups.

#### SearchBar Molecule
```html
<div class="search-bar">
  <div class="input-group">
    <span class="input-group-text">
      <i class="fa-solid fa-magnifying-glass"></i>
    </span>
    <input type="text" class="form-control" placeholder="Search playbooks...">
    <button class="btn btn-primary">Search</button>
  </div>
</div>
```

#### FormField Molecule
```html
<div class="form-field mb-3">
  <label for="playbookName" class="form-label">
    Playbook Name
    <span class="text-danger">*</span>
  </label>
  <input type="text" 
         class="form-control" 
         id="playbookName"
         required>
  <div class="form-text">Choose a descriptive name</div>
  <div class="invalid-feedback">Please provide a playbook name</div>
</div>
```

#### Card Molecule
```html
<div class="card">
  <div class="card-body">
    <h5 class="card-title">Card Title</h5>
    <p class="card-text">Card content goes here.</p>
  </div>
</div>
```

#### NotificationBadge Molecule
```html
<a href="/notifications" class="nav-link position-relative">
  <i class="fa-solid fa-bell"></i>
  <span class="badge bg-danger rounded-pill position-absolute top-0 start-100 translate-middle">
    3
  </span>
</a>
```

#### ButtonGroup Molecule
```html
<div class="btn-group" role="group">
  <button class="btn btn-outline-secondary active">Day</button>
  <button class="btn btn-outline-secondary">Month</button>
  <button class="btn btn-outline-secondary">Year</button>
</div>
```

---

### 3. Organisms (Complex Components)

Organisms are relatively complex UI components composed of molecules and atoms.

#### Header Organism
```html
<header class="navbar navbar-expand-lg navbar-light bg-white shadow-sm sticky-top">
  <div class="container-fluid">
    <!-- Left section -->
    <button class="navbar-toggler me-2">
      <i class="fa-solid fa-bars"></i>
    </button>
    <a class="navbar-brand" href="/">Mimir</a>
    
    <!-- Center navigation -->
    <div class="collapse navbar-collapse">
      <ul class="navbar-nav me-auto">
        <li class="nav-item">
          <a class="nav-link active" href="/dashboard">Dashboard</a>
        </li>
        <li class="nav-item">
          <a class="nav-link" href="/playbooks">Playbooks</a>
        </li>
        <li class="nav-item">
          <a class="nav-link" href="/families">Families</a>
        </li>
      </ul>
      
      <!-- Right utilities -->
      <ul class="navbar-nav ms-auto">
        <li class="nav-item">
          <button class="btn btn-link nav-link" id="darkModeToggle">
            <i class="fa-solid fa-moon"></i>
          </button>
        </li>
        <li class="nav-item">
          <a class="nav-link position-relative" href="/notifications">
            <i class="fa-solid fa-bell"></i>
            <span class="badge bg-danger rounded-pill position-absolute">3</span>
          </a>
        </li>
        <li class="nav-item dropdown">
          <a class="nav-link dropdown-toggle" href="#" data-bs-toggle="dropdown">
            <img src="/avatar.jpg" class="rounded-circle" width="32" height="32">
          </a>
          <ul class="dropdown-menu dropdown-menu-end">
            <li><a class="dropdown-item" href="/profile">My Profile</a></li>
            <li><a class="dropdown-item" href="/settings">Settings</a></li>
            <li><hr class="dropdown-divider"></li>
            <li><a class="dropdown-item" href="/logout">Log Out</a></li>
          </ul>
        </li>
      </ul>
    </div>
  </div>
</header>
```

#### StatCard Organism (Dashboard)
```html
<div class="card stat-card stat-card-blue">
  <div class="card-body">
    <!-- Settings icon (top right) -->
    <button class="btn btn-link text-white position-absolute top-0 end-0 m-2">
      <i class="fa-solid fa-gear"></i>
    </button>
    
    <!-- Number -->
    <div class="stat-card-number">9,823</div>
    
    <!-- Label -->
    <div class="stat-card-label">Members online</div>
    
    <!-- Mini chart -->
    <div class="stat-card-chart">
      <canvas id="chart1"></canvas>
    </div>
  </div>
</div>
```

#### DataTable Organism
```html
<div class="table-responsive">
  <table class="table table-hover">
    <thead>
      <tr>
        <th>
          <input class="form-check-input" type="checkbox" id="selectAll">
        </th>
        <th>Name</th>
        <th>Family</th>
        <th>Status</th>
        <th>Last Updated</th>
        <th class="text-end">Actions</th>
      </tr>
    </thead>
    <tbody>
      <tr>
        <td>
          <input class="form-check-input" type="checkbox">
        </td>
        <td>React Frontend Development</td>
        <td><span class="badge bg-info">Usability</span></td>
        <td><span class="badge bg-success">Active</span></td>
        <td>2 hours ago</td>
        <td class="text-end">
          <button class="btn btn-sm btn-outline-primary" 
                  data-bs-toggle="tooltip" 
                  title="Edit playbook">
            <i class="fa-solid fa-pen-to-square"></i>
          </button>
          <button class="btn btn-sm btn-outline-danger"
                  data-bs-toggle="tooltip"
                  title="Delete playbook">
            <i class="fa-solid fa-trash"></i>
          </button>
        </td>
      </tr>
      <!-- More rows -->
    </tbody>
  </table>
</div>
```

#### EditForm Organism
```html
<form class="edit-form" id="playbookForm">
  <div class="row">
    <!-- Left column -->
    <div class="col-md-8">
      <div class="mb-3">
        <label for="name" class="form-label">Playbook Name <span class="text-danger">*</span></label>
        <input type="text" class="form-control" id="name" required>
      </div>
      
      <div class="mb-3">
        <label for="description" class="form-label">Description</label>
        <textarea class="form-control" id="description" rows="3"></textarea>
      </div>
      
      <div class="mb-3">
        <label for="family" class="form-label">Family</label>
        <select class="form-select" id="family">
          <option value="">Choose family...</option>
          <option value="1">Usability</option>
          <option value="2">UX</option>
        </select>
      </div>
    </div>
    
    <!-- Right column (metadata) -->
    <div class="col-md-4">
      <div class="card">
        <div class="card-header">Settings</div>
        <div class="card-body">
          <div class="mb-3">
            <label class="form-label">Visibility</label>
            <div class="form-check">
              <input class="form-check-input" type="radio" name="visibility" id="public" checked>
              <label class="form-check-label" for="public">Public</label>
            </div>
            <div class="form-check">
              <input class="form-check-input" type="radio" name="visibility" id="private">
              <label class="form-check-label" for="private">Private</label>
            </div>
          </div>
          
          <div class="form-check form-switch">
            <input class="form-check-input" type="checkbox" id="autoApprove">
            <label class="form-check-label" for="autoApprove">Auto-approve PIPs</label>
          </div>
        </div>
      </div>
    </div>
  </div>
  
  <!-- Actions -->
  <div class="d-flex justify-content-end gap-2 mt-4">
    <button type="button" class="btn btn-outline-secondary">Cancel</button>
    <button type="button" class="btn btn-outline-primary">Save Draft</button>
    <button type="submit" class="btn btn-primary">
      <i class="fa-solid fa-save me-2"></i>
      Publish
    </button>
  </div>
</form>
```

---

### 4. Templates (Page-Level Layouts)

Templates define the overall page composition using organisms, molecules, and atoms.

#### Dashboard Template
```html
<!DOCTYPE html>
<html lang="en" data-bs-theme="light">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Dashboard - Mimir</title>
  <link rel="stylesheet" href="/css/bootstrap.min.css">
  <link rel="stylesheet" href="/css/fontawesome.min.css">
  <link rel="stylesheet" href="/css/mimir.css">
</head>
<body>
  <!-- Header Organism -->
  <header class="navbar sticky-top">...</header>
  
  <!-- Main Container -->
  <div class="container-fluid p-4">
    <!-- Breadcrumbs -->
    <nav aria-label="breadcrumb" class="mb-3">
      <ol class="breadcrumb">
        <li class="breadcrumb-item"><a href="/">Home</a></li>
        <li class="breadcrumb-item"><a href="/admin">Admin</a></li>
        <li class="breadcrumb-item active">Dashboard</li>
      </ol>
    </nav>
    
    <!-- Page Header -->
    <div class="d-flex justify-content-between align-items-center mb-4">
      <h1 class="h3 mb-0">Dashboard</h1>
      <div class="btn-group">
        <button class="btn btn-outline-secondary">
          <i class="fa-solid fa-chart-line me-2"></i>
          Dashboard
        </button>
        <button class="btn btn-outline-secondary">
          <i class="fa-solid fa-gear me-2"></i>
          Settings
        </button>
      </div>
    </div>
    
    <!-- Stat Cards Row -->
    <div class="row g-3 mb-4">
      <div class="col-12 col-sm-6 col-lg-3">
        <!-- StatCard Organism (Purple) -->
      </div>
      <div class="col-12 col-sm-6 col-lg-3">
        <!-- StatCard Organism (Blue) -->
      </div>
      <div class="col-12 col-sm-6 col-lg-3">
        <!-- StatCard Organism (Orange) -->
      </div>
      <div class="col-12 col-sm-6 col-lg-3">
        <!-- StatCard Organism (Red) -->
      </div>
    </div>
    
    <!-- Main Chart -->
    <div class="row">
      <div class="col-12">
        <div class="card">
          <div class="card-body">
            <!-- Chart organism -->
          </div>
        </div>
      </div>
    </div>
  </div>
  
  <script src="/js/bootstrap.bundle.min.js"></script>
  <script src="/js/mimir.js"></script>
</body>
</html>
```

#### Detail Page Template (with Metadata Sidebar)

**Note**: Navigation is in the top navbar. Sidebar is for metadata only.

```html
<!-- Top navbar handles all navigation -->
<header class="navbar sticky-top">...</header>

<div class="container-fluid p-4">
  <div class="row">
    <!-- Main Content -->
    <main class="col-lg-9 p-4">
      <!-- Breadcrumbs -->
      <nav aria-label="breadcrumb" class="mb-3">
        <ol class="breadcrumb">
          <li class="breadcrumb-item"><a href="/">Home</a></li>
          <li class="breadcrumb-item"><a href="/playbooks">Playbooks</a></li>
          <li class="breadcrumb-item active">React Frontend Development</li>
        </ol>
      </nav>
      
      <!-- Page Header -->
      <div class="d-flex justify-content-between align-items-center mb-4">
        <div>
          <h1 class="h3 mb-1">React Frontend Development</h1>
          <div class="text-muted">v1.0 • Updated 2 hours ago</div>
        </div>
        <div class="btn-group">
          <button class="btn btn-outline-primary" 
                  data-bs-toggle="tooltip" 
                  title="Edit this playbook">
            <i class="fa-solid fa-pen-to-square me-2"></i>
            Edit
          </button>
          <button class="btn btn-outline-secondary"
                  data-bs-toggle="tooltip"
                  title="Share with family members">
            <i class="fa-solid fa-share-nodes me-2"></i>
            Share
          </button>
        </div>
      </div>
      
      <!-- Tabs for content sections -->
      <ul class="nav nav-tabs mb-4">
        <li class="nav-item">
          <button class="nav-link active" data-bs-toggle="tab" data-bs-target="#overview">
            <i class="fa-solid fa-circle-info me-2"></i>
            Overview
          </button>
        </li>
        <li class="nav-item">
          <button class="nav-link" data-bs-toggle="tab" data-bs-target="#activities">
            <i class="fa-solid fa-list-check me-2"></i>
            Activities
          </button>
        </li>
        <li class="nav-item">
          <button class="nav-link" data-bs-toggle="tab" data-bs-target="#settings">
            <i class="fa-solid fa-gear me-2"></i>
            Settings
          </button>
        </li>
      </ul>
      
      <!-- Tab Content -->
      <div class="tab-content">
        <div class="tab-pane fade show active" id="overview">
          <!-- Content -->
        </div>
      </div>
    </main>
    
    <!-- Metadata Sidebar (NOT navigation) -->
    <aside class="col-lg-3 bg-light p-3">
      <h6 class="text-uppercase text-muted small mb-3">Details</h6>
      
      <!-- Version info -->
      <div class="mb-3">
        <div class="small text-muted">Version</div>
        <div class="fw-semibold">1.0</div>
      </div>
      
      <!-- Family -->
      <div class="mb-3">
        <div class="small text-muted">Family</div>
        <div><span class="badge bg-info">Usability</span></div>
      </div>
      
      <!-- Author -->
      <div class="mb-3">
        <div class="small text-muted">Author</div>
        <div class="d-flex align-items-center">
          <img src="/avatar.jpg" class="rounded-circle me-2" width="24" height="24">
          <span>Maria Chen</span>
        </div>
      </div>
      
      <!-- Last updated -->
      <div class="mb-3">
        <div class="small text-muted">Last Updated</div>
        <div>2 hours ago</div>
      </div>
      
      <!-- Tags -->
      <div class="mb-3">
        <div class="small text-muted">Tags</div>
        <div class="d-flex flex-wrap gap-1 mt-1">
          <span class="badge bg-secondary">React</span>
          <span class="badge bg-secondary">Frontend</span>
          <span class="badge bg-secondary">Development</span>
        </div>
      </div>
    </aside>
  </div>
</div>
```

---

### 5. Component States

Every component must define clear states with visual indicators.

#### Button States
```css
/* Default state */
.btn-primary {
  background-color: var(--bs-primary);
  border-color: var(--bs-primary);
}

/* Hover state */
.btn-primary:hover {
  background-color: darken(var(--bs-primary), 10%);
}

/* Active/Pressed state */
.btn-primary:active {
  background-color: darken(var(--bs-primary), 15%);
  transform: translateY(1px);
}

/* Focus state (accessibility) */
.btn-primary:focus {
  box-shadow: 0 0 0 0.25rem rgba(13, 110, 253, 0.5);
}

/* Disabled state */
.btn-primary:disabled {
  opacity: 0.65;
  cursor: not-allowed;
}

/* Loading state */
.btn-primary.loading {
  position: relative;
  color: transparent;
}

.btn-primary.loading::after {
  content: "";
  position: absolute;
  width: 1rem;
  height: 1rem;
  top: 50%;
  left: 50%;
  margin-left: -0.5rem;
  margin-top: -0.5rem;
  border: 2px solid white;
  border-radius: 50%;
  border-top-color: transparent;
  animation: spin 0.6s linear infinite;
}
```

#### Input States
- **Default**: Normal border, placeholder text
- **Focus**: Primary border, box-shadow
- **Valid**: Green border, checkmark icon
- **Invalid**: Red border, error icon, error message
- **Disabled**: Gray background, no interaction
- **Loading**: Spinner in input-group-text

#### Card States
- **Default**: elevation-1 shadow
- **Hover**: elevation-2 shadow, slight lift
- **Active/Selected**: Primary border, slight background tint
- **Disabled**: Reduced opacity, no hover
- **Loading**: Skeleton screen placeholders

#### Empty States
```html
<div class="empty-state text-center py-5">
  <div class="empty-state-icon mb-3">
    <i class="fa-light fa-inbox fa-4x text-muted"></i>
  </div>
  <h3 class="h5">No playbooks yet</h3>
  <p class="text-muted">Get started by creating your first playbook</p>
  <button class="btn btn-primary mt-3">
    <i class="fa-solid fa-plus me-2"></i>
    Create Playbook
  </button>
</div>
```

---

### 6. Component APIs

Each component should have a clear API (props, events, slots).

#### Example: StatCard Component API

**Props**:
```javascript
{
  number: "9,823",           // Main stat number
  label: "Members online",   // Stat label
  color: "blue",             // Color variant (purple|blue|orange|red)
  icon: "fa-gear",          // Settings icon (optional)
  chartData: [...],         // Chart data for mini chart
  trend: "+5%",             // Trend indicator (optional)
  loading: false            // Loading state
}
```

**Events**:
```javascript
{
  onSettingsClick: () => {},  // When settings icon clicked
  onClick: () => {}           // When card clicked
}
```

**Usage**:
```html
<stat-card
  number="9,823"
  label="Members online"
  color="blue"
  :chart-data="chartData"
  @settings-click="handleSettings"
/>
```

---

### 7. Component Variants and Modifiers

Use Bootstrap's variant system extended with custom modifiers.

#### Button Variants
- `.btn-primary`, `.btn-secondary`, `.btn-success`, etc.
- `.btn-outline-primary`, `.btn-outline-secondary`, etc.
- `.btn-link`

#### Size Modifiers
- `.btn-sm`, `.btn-lg`
- `.form-control-sm`, `.form-control-lg`
- `.badge-sm` (custom)

#### State Modifiers
- `.active`
- `.disabled`
- `.loading` (custom)

---

### 8. Component Documentation and Usage Examples

Each component should have:

1. **Purpose**: What problem it solves
2. **Anatomy**: Visual breakdown of parts
3. **Props/Attributes**: All configurable options
4. **States**: All possible states with examples
5. **Accessibility**: ARIA requirements, keyboard navigation
6. **Examples**: Common usage patterns
7. **Do's and Don'ts**: Best practices and anti-patterns

**Example Documentation Format**:

```markdown
## Button Component

### Purpose
Buttons trigger actions or navigate users through the application.

### Anatomy
- Icon (optional)
- Label (required)
- Badge count (optional)

### Props
| Prop | Type | Default | Description |
|------|------|---------|-------------|
| variant | string | "primary" | Button style variant |
| size | string | "md" | Button size (sm, md, lg) |
| disabled | boolean | false | Disabled state |
| loading | boolean | false | Show loading spinner |
| icon | string | null | Font Awesome icon class |

### Usage
```html
<button class="btn btn-primary">
  <i class="fa-solid fa-save me-2"></i>
  Save
</button>
```

### Do's
✓ Use primary buttons for main actions
✓ Include icons for clarity
✓ Add tooltips to icon-only buttons

### Don'ts
✗ Don't use multiple primary buttons in same context
✗ Don't use red for anything other than destructive actions
```

---

(Continue to Part 3 for remaining sections...)
# Mimir IA Guidelines - Part 3 (Final)

## Behavior & Interactions

### 1. Animation and Transition Specifications

**Timing Duration**:
```css
/* Bootstrap defaults - use these */
--bs-transition-duration: 0.15s;   /* Fast - hover states */
--bs-transition-duration-sm: 0.2s;  /* Standard - most UI */
--bs-transition-duration-md: 0.3s;  /* Moderate - modals, dropdowns */
--bs-transition-duration-lg: 0.5s;  /* Slow - page transitions */
```

**Easing Functions**:
```css
/* Bootstrap ease functions */
--bs-easing: cubic-bezier(0.4, 0, 0.2, 1);       /* Standard easing */
--bs-easing-in: cubic-bezier(0.4, 0, 1, 1);      /* Deceleration */
--bs-easing-out: cubic-bezier(0, 0, 0.2, 1);     /* Acceleration */
--bs-easing-in-out: cubic-bezier(0.4, 0, 0.2, 1); /* Smooth both ends */
```

**Transition Triggers**:
- **Hover**: Immediate (0.15s)
- **Click/Active**: Snap (0.1s)
- **Modal open/close**: 0.3s
- **Toast/Alert appear**: 0.2s slide + fade
- **Page transitions**: 0.5s fade

**Common Transitions**:
```css
/* Hover effects */
.card {
  transition: box-shadow 0.2s ease, transform 0.2s ease;
}

.card:hover {
  box-shadow: var(--mimir-card-shadow-hover);
  transform: translateY(-2px);
}

/* Fade in/out */
.fade-enter {
  opacity: 0;
}

.fade-enter-active {
  transition: opacity 0.3s ease;
}

/* Slide up */
.slide-up-enter {
  transform: translateY(20px);
  opacity: 0;
}

.slide-up-enter-active {
  transition: transform 0.3s ease, opacity 0.3s ease;
}

/* Modal backdrop */
.modal-backdrop {
  transition: opacity 0.15s linear;
}

/* Button press */
.btn:active {
  transform: scale(0.98);
  transition: transform 0.1s ease;
}
```

---

### 2. Loading States and Skeleton Screens

#### Spinner (Inline)
```html
<div class="spinner-border spinner-border-sm" role="status">
  <span class="visually-hidden">Loading...</span>
</div>
```

#### Button Loading State
```html
<button class="btn btn-primary" disabled>
  <span class="spinner-border spinner-border-sm me-2"></span>
  Saving...
</button>
```

#### Skeleton Screen (Card)
```html
<div class="card">
  <div class="card-body">
    <div class="skeleton skeleton-title mb-3"></div>
    <div class="skeleton skeleton-text mb-2"></div>
    <div class="skeleton skeleton-text mb-2"></div>
    <div class="skeleton skeleton-text w-75"></div>
  </div>
</div>

<style>
.skeleton {
  background: linear-gradient(
    90deg,
    var(--bs-gray-200) 25%,
    var(--bs-gray-100) 50%,
    var(--bs-gray-200) 75%
  );
  background-size: 200% 100%;
  animation: skeleton-loading 1.5s ease-in-out infinite;
  border-radius: 0.25rem;
}

.skeleton-title {
  height: 1.5rem;
  width: 40%;
}

.skeleton-text {
  height: 1rem;
  width: 100%;
}

@keyframes skeleton-loading {
  0% { background-position: 200% 0; }
  100% { background-position: -200% 0; }
}
</style>
```

#### Page Loading
```html
<div class="page-loader">
  <div class="spinner-border text-primary" role="status">
    <span class="visually-hidden">Loading...</span>
  </div>
  <p class="mt-3 text-muted">Loading dashboard...</p>
</div>
```

---

### 3. Micro-interactions and Feedback Patterns

#### Hover Feedback
```css
/* Nav links */
.nav-link {
  transition: all 0.2s ease;
}

.nav-link:hover {
  background-color: var(--bs-gray-100);
  border-radius: 0.375rem;
}

/* Icons */
.btn-icon:hover i {
  transform: scale(1.1);
  transition: transform 0.2s ease;
}
```

#### Click Feedback (Ripple Effect)
```html
<button class="btn btn-primary ripple-effect">
  Click Me
</button>

<script>
function createRipple(event) {
  const button = event.currentTarget;
  const ripple = document.createElement('span');
  const rect = button.getBoundingClientRect();
  
  ripple.className = 'ripple';
  ripple.style.left = `${event.clientX - rect.left}px`;
  ripple.style.top = `${event.clientY - rect.top}px`;
  
  button.appendChild(ripple);
  
  setTimeout(() => ripple.remove(), 600);
}
</script>

<style>
.ripple-effect {
  position: relative;
  overflow: hidden;
}

.ripple {
  position: absolute;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.6);
  width: 100px;
  height: 100px;
  margin-left: -50px;
  margin-top: -50px;
  animation: ripple-animation 0.6s;
  pointer-events: none;
}

@keyframes ripple-animation {
  from {
    transform: scale(0);
    opacity: 1;
  }
  to {
    transform: scale(4);
    opacity: 0;
  }
}
</style>
```

#### Success Messages, Validation Errors, and Notifications

**Mimir Messaging Strategy**: Use **Bootstrap Toasts** for success messages, validation errors, and notifications.

**Toast Container Setup**:
```html
<!-- Toast container (fixed position, top-right) -->
<div class="toast-container position-fixed top-0 end-0 p-3" style="z-index: 1090;">
  <!-- Toasts will be inserted here dynamically -->
</div>
```

**Success Toast**:
```html
<!-- Success message -->
<div class="toast align-items-center text-bg-success border-0" role="alert" aria-live="assertive" aria-atomic="true">
  <div class="d-flex">
    <div class="toast-body">
      <i class="fa-solid fa-circle-check me-2"></i>
      Playbook saved successfully!
    </div>
    <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
  </div>
</div>
```

**Error Toast**:
```html
<!-- Error notification -->
<div class="toast align-items-center text-bg-danger border-0" role="alert" aria-live="assertive" aria-atomic="true">
  <div class="d-flex">
    <div class="toast-body">
      <i class="fa-solid fa-circle-exclamation me-2"></i>
      Failed to save playbook. Please try again.
    </div>
    <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
  </div>
</div>
```

**Warning Toast**:
```html
<!-- Warning notification -->
<div class="toast align-items-center text-bg-warning border-0" role="alert" aria-live="assertive" aria-atomic="true">
  <div class="d-flex">
    <div class="toast-body">
      <i class="fa-solid fa-triangle-exclamation me-2"></i>
      Some changes may not be saved.
    </div>
    <button type="button" class="btn-close me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
  </div>
</div>
```

**Info Toast**:
```html
<!-- Info notification -->
<div class="toast align-items-center text-bg-info border-0" role="alert" aria-live="assertive" aria-atomic="true">
  <div class="d-flex">
    <div class="toast-body">
      <i class="fa-solid fa-circle-info me-2"></i>
      Sync completed with 3 new updates.
    </div>
    <button type="button" class="btn-close me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
  </div>
</div>
```

**Toast with Header**:
```html
<!-- Toast with title -->
<div class="toast" role="alert" aria-live="assertive" aria-atomic="true">
  <div class="toast-header text-bg-success">
    <i class="fa-solid fa-circle-check me-2"></i>
    <strong class="me-auto">Success</strong>
    <small>Just now</small>
    <button type="button" class="btn-close btn-close-white" data-bs-dismiss="toast" aria-label="Close"></button>
  </div>
  <div class="toast-body">
    Workflow "Build Feature" has been created successfully.
  </div>
</div>
```

**JavaScript Initialization**:
```javascript
// Initialize all toasts
document.addEventListener('DOMContentLoaded', function() {
  const toastElList = document.querySelectorAll('.toast');
  const toastList = [...toastElList].map(toastEl => new bootstrap.Toast(toastEl, {
    autohide: true,
    delay: 5000  // Auto-hide after 5 seconds
  }));
  
  // Show all toasts
  toastList.forEach(toast => toast.show());
});

// Helper function to show toast programmatically
function showToast(message, type = 'success') {
  const toastContainer = document.querySelector('.toast-container');
  
  const icons = {
    success: 'fa-circle-check',
    error: 'fa-circle-exclamation',
    warning: 'fa-triangle-exclamation',
    info: 'fa-circle-info'
  };
  
  const bgClasses = {
    success: 'text-bg-success',
    error: 'text-bg-danger',
    warning: 'text-bg-warning',
    info: 'text-bg-info'
  };
  
  const toastHTML = `
    <div class="toast align-items-center ${bgClasses[type]} border-0" role="alert">
      <div class="d-flex">
        <div class="toast-body">
          <i class="fa-solid ${icons[type]} me-2"></i>
          ${message}
        </div>
        <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
      </div>
    </div>
  `;
  
  toastContainer.insertAdjacentHTML('beforeend', toastHTML);
  const toastElement = toastContainer.lastElementChild;
  const toast = new bootstrap.Toast(toastElement, { autohide: true, delay: 5000 });
  toast.show();
  
  // Remove from DOM after hidden
  toastElement.addEventListener('hidden.bs.toast', () => toastElement.remove());
}

// Usage examples:
// showToast('Playbook saved successfully!', 'success');
// showToast('Failed to delete workflow', 'error');
// showToast('Sync is in progress', 'info');
```

**HTMX Integration**:
```html
<!-- Server returns toast HTML in response header -->
<button hx-post="/playbooks/playbook/save/123/"
        hx-target="#content"
        hx-on:htmx:after-request="if(event.detail.xhr.getResponseHeader('X-Toast')) {
          const toast = event.detail.xhr.getResponseHeader('X-Toast');
          showToast(toast, 'success');
        }">
  Save Playbook
</button>
```

**Django View Response**:
```python
# In Django view
response = HttpResponse(html_content)
response['X-Toast'] = 'Playbook saved successfully!'
response['X-Toast-Type'] = 'success'
return response
```

**Toast Positioning Options**:
```html
<!-- Top-right (default) -->
<div class="toast-container position-fixed top-0 end-0 p-3">

<!-- Top-center -->
<div class="toast-container position-fixed top-0 start-50 translate-middle-x p-3">

<!-- Bottom-right -->
<div class="toast-container position-fixed bottom-0 end-0 p-3">

<!-- Bottom-center -->
<div class="toast-container position-fixed bottom-0 start-50 translate-middle-x p-3">
```

**Best Practices**:
- ✅ Use toasts for non-blocking notifications (success, info, warnings)
- ✅ Auto-hide after 5 seconds for success/info
- ✅ Keep error toasts visible longer (10+ seconds) or require manual dismissal
- ✅ Include clear, actionable messages
- ✅ Use semantic icons (check, exclamation, info, warning)
- ✅ Stack multiple toasts vertically
- ✅ Remove from DOM after dismissal to prevent memory leaks

#### Field-Level Validation Errors

For form field validation, use inline errors **underneath the field** (not toasts):

```html
<!-- Inline error -->
<input type="email" class="form-control is-invalid" value="invalidemail">
<div class="invalid-feedback">
  <i class="fa-solid fa-circle-exclamation me-1"></i>
  Please enter a valid email address
</div>
```

---

### 4. Hover, Focus, and Active States

**Comprehensive State System**:
```css
/* Link states */
a {
  color: var(--bs-primary);
  text-decoration: none;
  transition: color 0.15s ease;
}

a:hover {
  color: darken(var(--bs-primary), 15%);
  text-decoration: underline;
}

a:focus {
  outline: 2px solid var(--bs-primary);
  outline-offset: 2px;
}

a:active {
  color: darken(var(--bs-primary), 20%);
}

/* Button states */
.btn {
  transition: all 0.15s ease;
}

.btn:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 8px rgba(0,0,0,0.15);
}

.btn:focus {
  box-shadow: 0 0 0 0.25rem rgba(13, 110, 253, 0.5);
}

.btn:active {
  transform: translateY(0);
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

/* Card states */
.card-clickable {
  cursor: pointer;
  transition: all 0.2s ease;
}

.card-clickable:hover {
  box-shadow: var(--mimir-card-shadow-hover);
  transform: translateY(-2px);
}

.card-clickable:focus-within {
  outline: 2px solid var(--bs-primary);
  outline-offset: 2px;
}
```

---

### 5. Touch and Gesture Patterns

**Touch Target Sizes**:
- Minimum: 44x44px (WCAG guideline)
- Recommended: 48x48px
- Spacing between targets: 8px minimum

```css
/* Mobile-optimized buttons */
@media (max-width: 767px) {
  .btn {
    min-height: 44px;
    padding: 0.75rem 1.5rem;
  }
  
  .nav-link {
    min-height: 44px;
    padding: 0.75rem 1rem;
  }
}
```

**Swipe Gestures** (for mobile):
- Swipe left on table row: Reveal actions
- Swipe right on modal: Dismiss
- Pull to refresh: Update content

**Long Press**:
- Hold card: Show context menu
- Hold button: Show tooltip

---

### 6. Scroll Behavior and Infinite Loading

#### Smooth Scroll
```css
html {
  scroll-behavior: smooth;
}

/* Scroll to top button */
.scroll-to-top {
  position: fixed;
  bottom: 2rem;
  right: 2rem;
  opacity: 0;
  transition: opacity 0.3s ease, transform 0.3s ease;
  z-index: var(--z-fixed);
}

.scroll-to-top.visible {
  opacity: 1;
  transform: translateY(0);
}
```

#### Infinite Scroll
```html
<div class="infinite-scroll-container">
  <!-- Content items -->
  <div class="item">...</div>
  <div class="item">...</div>
  
  <!-- Loading trigger -->
  <div class="infinite-scroll-trigger" data-loading="false">
    <div class="spinner-border"></div>
  </div>
</div>

<script>
const observer = new IntersectionObserver((entries) => {
  entries.forEach(entry => {
    if (entry.isIntersecting && !entry.target.dataset.loading) {
      loadMoreItems();
    }
  });
});

observer.observe(document.querySelector('.infinite-scroll-trigger'));
</script>
```

#### Pagination
```html
<nav aria-label="Page navigation">
  <ul class="pagination justify-content-center">
    <li class="page-item disabled">
      <a class="page-link" href="#" tabindex="-1">Previous</a>
    </li>
    <li class="page-item active"><a class="page-link" href="#">1</a></li>
    <li class="page-item"><a class="page-link" href="#">2</a></li>
    <li class="page-item"><a class="page-link" href="#">3</a></li>
    <li class="page-item">
      <a class="page-link" href="#">Next</a>
    </li>
  </ul>
</nav>
```

---

## Flow & User Experience

### 1. Interaction Design

**Click Flows**: 
- Primary action: 1 click
- Secondary action: 2 clicks maximum
- Destructive action: 2 clicks (action + confirmation)

**Form Submission Flow**:
1. User fills form
2. Click submit
3. Validate inline (immediate feedback)
4. Show loading state on button
5. Success: Toast notification + redirect
6. Error: Show error messages inline + toast

---

### 2. Displaying Progress

#### Progress Bar
```html
<div class="progress" role="progressbar">
  <div class="progress-bar" style="width: 45%">45%</div>
</div>

<!-- Striped animated -->
<div class="progress">
  <div class="progress-bar progress-bar-striped progress-bar-animated" 
       style="width: 75%"></div>
</div>
```

#### Stepper (Multi-step Form)
```html
<div class="stepper">
  <div class="step completed">
    <div class="step-icon">
      <i class="fa-solid fa-check"></i>
    </div>
    <div class="step-label">Account Info</div>
  </div>
  
  <div class="step active">
    <div class="step-icon">2</div>
    <div class="step-label">Setup FOB</div>
  </div>
  
  <div class="step">
    <div class="step-icon">3</div>
    <div class="step-label">Preferences</div>
  </div>
</div>
```

#### Upload Progress
```html
<div class="upload-progress">
  <div class="d-flex justify-content-between mb-2">
    <span>playbook-export.mpa</span>
    <span class="text-muted">45% (2.3 MB / 5.1 MB)</span>
  </div>
  <div class="progress">
    <div class="progress-bar" style="width: 45%"></div>
  </div>
</div>
```

---

### 3. Errors (Validation, System Errors, Empty States)

#### Inline Validation
```html
<!-- Valid -->
<input type="email" class="form-control is-valid" value="user@example.com">
<div class="valid-feedback">
  <i class="fa-solid fa-circle-check me-1"></i>
  Looks good!
</div>

<!-- Invalid -->
<input type="email" class="form-control is-invalid" value="invalidemail">
<div class="invalid-feedback">
  <i class="fa-solid fa-circle-exclamation me-1"></i>
  Please enter a valid email address
</div>
```

#### System Error Page
```html
<div class="error-page text-center py-5">
  <div class="error-icon mb-4">
    <i class="fa-light fa-triangle-exclamation fa-5x text-danger"></i>
  </div>
  <h1 class="display-4">500</h1>
  <h2 class="h4 mb-3">Internal Server Error</h2>
  <p class="text-muted mb-4">
    Something went wrong on our end. We've been notified and are working on it.
  </p>
  <div class="d-flex gap-2 justify-content-center">
    <button class="btn btn-primary" onclick="location.reload()">
      <i class="fa-solid fa-rotate-right me-2"></i>
      Try Again
    </button>
    <a href="/" class="btn btn-outline-secondary">
      <i class="fa-solid fa-house me-2"></i>
      Go Home
    </a>
  </div>
</div>
```

#### Toast Error
```html
<div class="toast align-items-center text-bg-danger border-0" role="alert">
  <div class="d-flex">
    <div class="toast-body">
      <i class="fa-solid fa-circle-exclamation me-2"></i>
      Failed to save playbook. Please try again.
    </div>
    <button type="button" class="btn-close btn-close-white me-2 m-auto"></button>
  </div>
</div>
```

---

### 4. Preferences and Settings

#### Settings Page Pattern

**Use tabs for settings navigation, NOT sidebar**:

```html
<div class="settings-page">
  <!-- Settings tabs -->
  <ul class="nav nav-tabs mb-4" role="tablist">
    <li class="nav-item" role="presentation">
      <button class="nav-link active" data-bs-toggle="tab" data-bs-target="#account">
        <i class="fa-solid fa-user me-2"></i>
        Account
      </button>
    </li>
    <li class="nav-item" role="presentation">
      <button class="nav-link" data-bs-toggle="tab" data-bs-target="#sync">
        <i class="fa-solid fa-sync me-2"></i>
        Sync & Connection
      </button>
    </li>
    <li class="nav-item" role="presentation">
      <button class="nav-link" data-bs-toggle="tab" data-bs-target="#notifications">
        <i class="fa-solid fa-bell me-2"></i>
        Notifications
      </button>
    </li>
    <li class="nav-item" role="presentation">
      <button class="nav-link" data-bs-toggle="tab" data-bs-target="#privacy">
        <i class="fa-solid fa-shield me-2"></i>
        Privacy
      </button>
    </li>
  </ul>
  
  <!-- Settings content -->
  <div class="tab-content">
    <div class="tab-pane fade show active" id="account">
      <div class="card">
        <div class="card-header">
          <h5 class="mb-0">Account Settings</h5>
        </div>
        <div class="card-body">
          <!-- Settings form -->
        </div>
      </div>
    </div>
    <!-- Other tabs... -->
  </div>
</div>
```

---

### 5. Onboarding and First-Use Experiences

#### Welcome Tour
```html
<div class="onboarding-tooltip" style="position: absolute; top: 100px; left: 200px;">
  <div class="card shadow-lg" style="max-width: 300px;">
    <div class="card-body">
      <div class="d-flex justify-content-between align-items-start mb-2">
        <span class="badge bg-primary">Step 1 of 4</span>
        <button class="btn-close btn-sm"></button>
      </div>
      <h6>Create Your First Playbook</h6>
      <p class="text-muted small mb-3">
        Click here to create your first playbook and start organizing your methodology.
      </p>
      <div class="d-flex justify-content-between">
        <button class="btn btn-sm btn-outline-secondary">Skip Tour</button>
        <button class="btn btn-sm btn-primary">Next</button>
      </div>
    </div>
  </div>
  <!-- Arrow pointing to element -->
  <div class="arrow"></div>
</div>
```

---

### 6. Success Confirmations and Feedback

#### Modal Confirmation
```html
<div class="modal fade" id="successModal">
  <div class="modal-dialog modal-dialog-centered">
    <div class="modal-content">
      <div class="modal-body text-center py-5">
        <div class="success-icon mb-4">
          <i class="fa-solid fa-circle-check fa-4x text-success"></i>
        </div>
        <h5 class="mb-3">Playbook Published Successfully!</h5>
        <p class="text-muted">
          Your playbook "React Frontend Development" is now available to the Usability family.
        </p>
        <button class="btn btn-primary mt-3" data-bs-dismiss="modal">
          Continue
        </button>
      </div>
    </div>
  </div>
</div>
```

---

## Data & State Patterns

### 1. Form Validation Patterns

#### Real-time Validation
```javascript
const emailInput = document.getElementById('email');

emailInput.addEventListener('blur', function() {
  const isValid = validateEmail(this.value);
  this.classList.toggle('is-valid', isValid);
  this.classList.toggle('is-invalid', !isValid);
});
```

#### On Submit Validation
```javascript
form.addEventListener('submit', function(e) {
  e.preventDefault();
  
  const isValid = validateForm(this);
  
  if (isValid) {
    submitForm(this);
  } else {
    showValidationErrors();
  }
});
```

---

### 2. Error Handling Strategies

**Error Priority**:
1. **Inline errors**: Field-level validation
2. **Toast notifications**: Action feedback
3. **Error pages**: System-level errors

**Error Message Pattern**:
```
[Icon] [What went wrong] [What to do about it]

Example: ⚠️ Failed to save playbook. Please check your connection and try again.
```

---

### 3. Data Fetching States

```javascript
const DataState = {
  IDLE: 'idle',
  LOADING: 'loading',
  SUCCESS: 'success',
  ERROR: 'error'
};

// UI templates for each state
const stateTemplates = {
  loading: '<div class="spinner-border"></div>',
  success: '<div>{{data}}</div>',
  error: '<div class="alert alert-danger">{{error}}</div>',
  empty: '<div class="empty-state">No data found</div>'
};
```

---

### 4. Empty States and Zero States

```html
<!-- Table empty state -->
<div class="empty-state text-center py-5">
  <i class="fa-light fa-inbox fa-4x text-muted mb-3"></i>
  <h5>No playbooks yet</h5>
  <p class="text-muted">
    Get started by creating your first playbook or downloading from a family.
  </p>
  <div class="mt-4">
    <button class="btn btn-primary me-2">
      <i class="fa-solid fa-plus me-2"></i>
      Create Playbook
    </button>
    <button class="btn btn-outline-secondary">
      <i class="fa-solid fa-download me-2"></i>
      Browse Families
    </button>
  </div>
</div>
```

---

### 5. Data Mutation Feedback

#### Optimistic Updates
```javascript
// Immediately update UI
updateUIOptimistically(newData);

// Send to server
api.update(newData)
  .then(() => {
    // Success toast
    showToast('Saved successfully', 'success');
  })
  .catch((error) => {
    // Revert UI
    revertUI();
    showToast('Failed to save. Please try again', 'error');
  });
```

#### Confirmation Modal
```html
<div class="modal fade" id="deleteConfirmModal">
  <div class="modal-dialog">
    <div class="modal-content">
      <div class="modal-header">
        <h5 class="modal-title">Delete Playbook?</h5>
        <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
      </div>
      <div class="modal-body">
        <p>Are you sure you want to delete <strong>"React Frontend Development"</strong>?</p>
        <div class="alert alert-warning">
          <i class="fa-solid fa-triangle-exclamation me-2"></i>
          This action cannot be undone.
        </div>
      </div>
      <div class="modal-footer">
        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">
          Cancel
        </button>
        <button type="button" class="btn btn-danger" id="confirmDelete">
          <i class="fa-solid fa-trash me-2"></i>
          Delete Playbook
        </button>
      </div>
    </div>
  </div>
</div>
```

---

### 6. Pagination and Infinite Scroll

#### Cursor-based Pagination
```javascript
let cursor = null;

async function loadMore() {
  const data = await api.getPlaybooks({ cursor, limit: 20 });
  appendItems(data.items);
  cursor = data.nextCursor;
  
  if (!data.hasMore) {
    hideLoadMoreButton();
  }
}
```

#### Load More Button
```html
<div class="text-center mt-4">
  <button class="btn btn-outline-primary" onclick="loadMore()">
    <i class="fa-solid fa-arrow-down me-2"></i>
    Load More
  </button>
  <div class="text-muted small mt-2">
    Showing 20 of 127 playbooks
  </div>
</div>
```

---

## Implementation Checklist

### Before Building Any Screen

- [ ] Review this IA guidelines document
- [ ] Identify which layout pattern to use (2-column, 3-column, grid, etc.)
- [ ] Identify all components needed (atoms, molecules, organisms)
- [ ] Check if components exist or need to be created
- [ ] Define all component states (default, hover, active, disabled, loading, error)
- [ ] Plan responsive behavior at each breakpoint
- [ ] Design loading states and error handling
- [ ] Add tooltips to all action buttons
- [ ] Ensure WCAG AA accessibility compliance
- [ ] Test keyboard navigation
- [ ] Validate with real data and edge cases

### Bootstrap-First Approach

1. **Start with Bootstrap**: Use Bootstrap classes and components as-is
2. **Customize sparingly**: Only add custom CSS when Bootstrap doesn't provide the pattern
3. **Extend, don't override**: Use CSS variables to customize Bootstrap rather than overriding
4. **Utility-first**: Prefer Bootstrap utilities over custom CSS
5. **Component composition**: Combine Bootstrap components rather than building from scratch

### Content Browser layout

The Content Browser (`templates/browser/browser_graph.html`) uses a full-viewport shell:

- **Body class**: `body.mm-content-browser` — rules in `static/css/design-system.css` (same pattern as `body.mm-landing`)
- **Panels & controls**: semantic `mm-browser-*` classes in `design-system.css`; avoid page-level `<style>` blocks
- **Icons**: Font Awesome Pro (`fa-solid fa-*`) for empty states and chrome
- **Tooltips**: Bootstrap tooltips on canvas action buttons (`data-bs-toggle="tooltip"`)
- **Detail embeds**: `mm-embed` wrapper + shared `.mm-embed .markdown-content` styles in `design-system.css`
- **Canvas exception**: Cytoscape node/edge colours live in `static/js/content-browser.js` (`_BOOTSTRAP_PALETTE`, `_PASTEL_NODE_PALETTE`) because the Cytoscape stylesheet API requires hex literals; JS-injected layout/routing/compound pickers use Bootstrap `dropdown-menu` classes with imperative fixed positioning

---

## References

- **Bootstrap 5.3 Documentation**: https://getbootstrap.com/docs/5.3
- **Font Awesome Pro**: https://fontawesome.com
- **WCAG 2.1 Guidelines**: https://www.w3.org/WAI/WCAG21/quickref/
- **Atomic Design**: https://atomicdesign.bradfrost.com/

---

**Document Version**: 1.0
**Last Updated**: November 20, 2024
**Maintained by**: Mimir UX Team
