# SaaS Application Design Guidelines

Essential design rules for building professional SaaS applications.
If the full `web-design-guidelines` skill is installed, also run it for comprehensive coverage.

## Layout Fundamentals

### Responsive Grid
- Use a consistent container width: `max-w-7xl mx-auto px-4 md:px-6`
- Design mobile-first, then layer on tablet and desktop styles
- Use CSS Grid or Flexbox — never absolute positioning for layout
- Content should be readable at every breakpoint from 320px to 2560px

### Spacing System
Use a consistent spacing scale. Tailwind's default scale works well:
- Between major sections: `py-6 md:py-8` (dashboard sections)
- Between dashboard cards: `gap-4` or `gap-6`
- Between form fields: `space-y-3` or `space-y-4`
- Between table rows: Use Tailwind's border utilities
- Never mix arbitrary spacing values — stick to the scale

### Visual Hierarchy
Content importance should be immediately clear through:
- **Size**: Larger = more important (h1 > h2 > h3 > body)
- **Weight**: Bolder = more important for headings
- **Color**: Primary/accent for emphasis, muted for supporting text
- **Position**: Most important data at top-left
- **Whitespace**: Important elements get more surrounding space

## Mandatory Spacing Minimums

These are non-negotiable minimums. Violating any of these is a verification failure.

### Container Padding
- **Page content area**: `px-6 py-6` minimum (24px on all sides)
- **Cards**: `p-6` minimum (24px internal padding)
- **Table cells**: `px-4 py-3` minimum (16px horizontal, 12px vertical)
- **Nav bar**: `px-4 py-3` minimum (16px horizontal, 12px vertical)
- **Sidebar nav items**: `px-3 py-2` minimum with `gap-1` between items
- **List items**: `px-4 py-3` minimum
- **Badges/tags**: `px-2.5 py-0.5` minimum (never let text touch the badge border)
- **Buttons**: `px-4 py-2` minimum for default, `px-6 py-3` for primary CTAs
- **Form inputs**: `px-3 py-2` minimum internal padding
- **Dialog/Sheet content**: `p-6` minimum

### Gaps Between Elements
- **Between cards in a grid**: `gap-4` minimum (16px), prefer `gap-6` (24px)
- **Between form fields**: `space-y-4` minimum (16px)
- **Between sections on a page**: `space-y-6` minimum (24px), prefer `space-y-8`
- **Between table rows**: built into cell padding, no extra needed
- **Between nav items in sidebar**: `gap-1` minimum (4px)
- **Between icon and text**: `gap-2` minimum (8px)
- **Between avatar and name**: `gap-3` minimum (12px)

### Alignment Rules
- **Nav bar items**: All items must be vertically centered using `items-center` on the flex container. Test: draw an imaginary horizontal line through the middle — every item's center should touch it.
- **Table columns**: Header text alignment must match data text alignment (left-aligned headers = left-aligned data)
- **Form labels**: Choose one alignment (top-aligned or left-aligned) and apply consistently across ALL forms
- **Sidebar icons**: All icons must be the same size and vertically aligned with their labels
- **Status badges in tables**: Vertically centered within their row

### Common Anti-Patterns to Avoid
- **Cramped nav bars**: Logo, center items, and right items must be in a proper flex layout with `justify-between` and `items-center`. Never use absolute positioning for nav items.
- **Tables without cell padding**: Always use shadcn Table with proper `TableCell` components. Never use raw `<td>` without padding classes.
- **Cards touching their container**: Cards must have margin/gap from their parent container, not sit flush against edges.
- **Messages/list items without left padding**: Every list item needs at least `pl-4` from its container edge.
- **Notification badges floating away**: Use `relative` on the parent icon and `absolute -top-1 -right-1` on the badge — never loose positioning.

## Typography

### Font Selection
- Use 1-2 font families max (one for headings, one for body — or the same for both)
- Sans-serif fonts are standard for SaaS (Inter, Plus Jakarta Sans, DM Sans)
- Load via `next/font` to prevent layout shift

### Type Scale
```
h1: text-3xl md:text-4xl font-bold tracking-tight
h2: text-2xl md:text-3xl font-bold tracking-tight
h3: text-lg md:text-xl font-semibold
h4: text-base font-semibold
body: text-base (16px)
small: text-sm
caption: text-xs
data/table: text-sm (12-14px)
```

### Line Length
- Body text: 45-75 characters per line (use `max-w-prose` or `max-w-2xl`)
- Headings can be wider but shouldn't span the full page width
- Form labels should be concise and left-aligned

## Color

### System Structure
Every SaaS app needs:
- **Primary**: Brand color for CTAs, active states, and key interactive elements
- **Secondary**: Supporting color for variety in UI
- **Background**: Page background (usually white or very light gray)
- **Foreground**: Primary text color (usually near-black)
- **Muted**: Secondary text, borders, subtle backgrounds
- **Accent**: Highlight color for badges, tags, alerts

### Contrast Requirements (WCAG AA)
- Normal text (< 18px): 4.5:1 contrast ratio minimum
- Large text (>= 18px bold or >= 24px): 3:1 minimum
- UI components and graphical objects: 3:1 minimum
- Data tables should have sufficient contrast between rows

### Dark Mode Design Considerations
- Primary CTA buttons should stand out in both modes
- Don't use pure black (#000) for dark mode backgrounds — use dark gray (#0a0a0a, #111)
- Don't use pure white (#fff) for light mode text backgrounds if it feels harsh — try #fafafa
- Ensure data-dense tables remain readable in dark mode
- Use muted colors strategically to avoid eye strain in dark mode

## Sidebar & Navigation

### Sidebar Width Guidelines
- **Expanded state**: 240-280px wide (standard SaaS sidebar)
- **Collapsed state**: 64px wide (icon-only)
- **Mobile**: Full-screen overlay or bottom navigation
- Active nav item should have distinctive background or left border
- Include clear collapse/expand button with icon feedback

### Sidebar Navigation Pattern
```typescript
'use client'
import { useState } from 'react'
import { ChevronLeft, ChevronRight, Home, Users, Settings } from 'lucide-react'

export function Sidebar() {
  const [isExpanded, setIsExpanded] = useState(true)

  return (
    <aside className={`${isExpanded ? 'w-72' : 'w-16'} bg-muted border-r transition-all duration-300`}>
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="p-4"
      >
        {isExpanded ? <ChevronLeft /> : <ChevronRight />}
      </button>
      <nav className="space-y-1 px-2">
        <NavItem icon={Home} label="Dashboard" isExpanded={isExpanded} />
        <NavItem icon={Users} label="Users" isExpanded={isExpanded} />
        <NavItem icon={Settings} label="Settings" isExpanded={isExpanded} />
      </nav>
    </aside>
  )
}
```

## Forms

### Labels & Inputs
- Every input must have a visible label (not just placeholder)
- Use `htmlFor`/`id` to associate labels with inputs
- Group related fields with `<fieldset>` and `<legend>`
- Show validation errors inline, below the relevant field
- Use `type` attributes correctly (email, tel, url, etc.)

### UX
- Keep forms short — ask for the minimum needed
- Use a single-column layout for forms (easier to scan)
- Disable the submit button while submitting (with loading indicator)
- Show a clear success message after submission
- Don't clear the form on validation error
- Provide helpful error messages (not just "Invalid input")

### Form Layout Pattern
```typescript
'use client'

export function UserForm() {
  return (
    <form className="space-y-4 max-w-md">
      <div className="space-y-1">
        <label htmlFor="name" className="text-sm font-medium">Full Name</label>
        <input id="name" type="text" className="w-full px-3 py-2 border rounded" />
        <p className="text-xs text-red-500">Error message if validation fails</p>
      </div>

      <div className="space-y-1">
        <label htmlFor="email" className="text-sm font-medium">Email</label>
        <input id="email" type="email" className="w-full px-3 py-2 border rounded" />
      </div>

      <button className="w-full bg-primary text-white py-2 rounded font-medium">Save</button>
    </form>
  )
}
```

## Data Tables

### Table Structure & Styling
- Use semantic `<table>` with `<thead>`, `<tbody>`, `<tfoot>`
- Zebra striping (alternating row colors) improves readability
- Sticky headers for horizontal scrolling on mobile
- Sortable columns should have visual indicator (arrow icon)
- Pagination controls below the table (if needed)

### Data Density Considerations
- For data-dense tables, use smaller padding: `py-2 px-3`
- Column width should be proportional to content type (dates < names < emails)
- Right-align numeric data, left-align text
- Use monospace font for numbers/IDs for better scanning
- Provide a "compact" vs "comfortable" view toggle for large datasets

### Table Pattern
```typescript
export function UsersTable({ users }) {
  return (
    <div className="overflow-x-auto border rounded-lg">
      <table className="w-full text-sm">
        <thead className="bg-muted border-b">
          <tr>
            <th className="px-4 py-3 text-left font-semibold">Name</th>
            <th className="px-4 py-3 text-left font-semibold">Email</th>
            <th className="px-4 py-3 text-left font-semibold">Status</th>
            <th className="px-4 py-3 text-right font-semibold">Actions</th>
          </tr>
        </thead>
        <tbody>
          {users.map((user, idx) => (
            <tr key={user.id} className={idx % 2 ? 'bg-white' : 'bg-muted/50'}>
              <td className="px-4 py-3">{user.name}</td>
              <td className="px-4 py-3">{user.email}</td>
              <td className="px-4 py-3">
                <span className="inline-block px-2 py-1 text-xs font-medium bg-green-100 text-green-700 rounded">
                  {user.status}
                </span>
              </td>
              <td className="px-4 py-3 text-right">
                <a href={`/users/${user.id}`} className="text-primary hover:underline">Edit</a>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
```

## Dashboard Components

### Dashboard Layout
- Use a grid layout: `grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4`
- Stat cards in top row, larger visualizations below
- Cards should be consistent size unless they span multiple columns

### Stat Cards with Consistent Styling
```typescript
export function StatCard({ label, value, icon: Icon, trend }) {
  return (
    <div className="p-4 border rounded-lg bg-white">
      <div className="flex items-start justify-between">
        <div>
          <p className="text-sm text-muted-foreground">{label}</p>
          <p className="text-2xl font-bold mt-1">{value}</p>
        </div>
        <div className="p-2 bg-primary/10 rounded-lg">
          <Icon className="h-5 w-5 text-primary" />
        </div>
      </div>
      {trend && (
        <p className="text-xs text-green-600 mt-3">↑ {trend} from last month</p>
      )}
    </div>
  )
}
```

### Dashboard Section Spacing
- Top-level sections: `py-6 md:py-8` (consistent breathing room)
- Section titles: `text-2xl font-bold mb-6`
- Card gaps within a grid: `gap-4` to `gap-6`
- Multiple card grids in one section: `space-y-8` between grids

### Dashboard Pattern
```typescript
export default async function Dashboard() {
  const stats = await getDashboardStats()

  return (
    <main className="p-6 md:p-8">
      <h1 className="text-3xl font-bold mb-8">Dashboard</h1>

      {/* Stats row */}
      <section className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
        {stats.cards.map(card => (
          <StatCard key={card.id} {...card} />
        ))}
      </section>

      {/* Charts section */}
      <section className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
        <RevenueChart data={stats.revenueData} />
        <ConversionChart data={stats.conversionData} />
      </section>

      {/* Recent activity */}
      <section>
        <h2 className="text-xl font-semibold mb-4">Recent Activity</h2>
        <ActivityTable activities={stats.recentActivity} />
      </section>
    </main>
  )
}
```

## Empty States

### Empty State Pattern
```typescript
export function EmptyState({
  icon: Icon,
  title,
  description,
  action
}) {
  return (
    <div className="flex flex-col items-center justify-center py-12 text-center">
      <div className="mb-4 p-3 bg-muted rounded-full">
        <Icon className="h-8 w-8 text-muted-foreground" />
      </div>
      <h3 className="text-lg font-semibold mb-1">{title}</h3>
      <p className="text-sm text-muted-foreground mb-6 max-w-xs">{description}</p>
      {action && (
        <button className="bg-primary text-white px-4 py-2 rounded font-medium">
          {action.label}
        </button>
      )}
    </div>
  )
}
```

### Usage in Lists
```typescript
export function UsersList({ users }) {
  if (users.length === 0) {
    return (
      <EmptyState
        icon={Users}
        title="No users yet"
        description="Get started by inviting your first team member."
        action={{ label: 'Invite user' }}
      />
    )
  }

  return <UserTable users={users} />
}
```

## Error States

### Error Message Pattern
```typescript
export function ErrorState({
  title = 'Something went wrong',
  description,
  action
}) {
  return (
    <div className="flex flex-col items-center justify-center py-12 text-center">
      <div className="mb-4 p-3 bg-red-100 rounded-full">
        <AlertCircle className="h-8 w-8 text-red-600" />
      </div>
      <h3 className="text-lg font-semibold text-red-900 mb-1">{title}</h3>
      {description && (
        <p className="text-sm text-red-700 mb-6 max-w-xs">{description}</p>
      )}
      {action && (
        <button className="bg-primary text-white px-4 py-2 rounded font-medium">
          {action.label}
        </button>
      )}
    </div>
  )
}
```

## Loading States

### Skeleton Loader Pattern
```typescript
export function TableSkeleton() {
  return (
    <div className="border rounded-lg">
      {[...Array(5)].map((_, i) => (
        <div key={i} className="border-b p-4 flex gap-4">
          <div className="h-4 bg-muted rounded w-32 animate-pulse" />
          <div className="h-4 bg-muted rounded flex-1 animate-pulse" />
          <div className="h-4 bg-muted rounded w-24 animate-pulse" />
        </div>
      ))}
    </div>
  )
}
```

## Buttons & CTAs

### Hierarchy
- **Primary CTA**: Solid fill, high contrast, used for main actions (1 per section max)
- **Secondary CTA**: Outlined or subdued, for alternative actions
- **Tertiary/Link**: Text with underline or arrow, for navigation
- **Danger**: Red background for destructive actions

### Sizing
- Minimum tap target: 44x44px on mobile
- Standard button padding: `px-4 py-2` (comfortable click area)
- Full-width on mobile for primary actions: `w-full md:w-auto`

### Labels
- Use action verbs: "Save", "Delete", "Export", "Add new"
- Be specific: "Export to CSV" > "Export" > "Download"
- Keep to 2-3 words when possible

## Images & Media

### Hero Images
- Full-width or contained, always above the fold
- Use `priority` prop in `next/image` to prevent LCP delays
- Provide a meaningful `alt` description
- Consider using product screenshots or illustration over stock photos

### Icons
- Use a consistent icon set (Lucide React recommended)
- Icons should enhance, not replace, text labels
- Minimum size: 16x16px for UI icons, 20x20px for standalone
- Use `aria-hidden="true"` on decorative icons

### Aspect Ratios
- Dashboard cards: 1:1 or variable (content-based)
- Charts/visualizations: 16:9 or 4:3
- User avatars: 1:1
- Feature illustrations: 1:1 or 4:3

## Navigation

### Header/Top Bar
- Logo or app name on the left
- Breadcrumbs or section title in center (for detail pages)
- User menu and settings on right
- Sticky header optional (common for SaaS) — `sticky top-0 z-50`

### Sidebar Navigation (See Sidebar & Navigation section above)

### Internal Linking
- Every page should be reachable within 2-3 clicks
- Active nav item should be visually distinct
- Breadcrumbs on detail pages for clear navigation path

## Accessibility Essentials

- **Semantic HTML**: Use the right element (button for actions, a for navigation)
- **Keyboard navigation**: All interactive elements must be reachable via Tab
- **Focus indicators**: Never remove outline without replacing it (`focus-visible:ring-2`)
- **Alt text**: Descriptive for informational images, empty (`alt=""`) for decorative
- **Color alone**: Don't convey meaning through color only (add icons or text)
- **Motion**: Respect `prefers-reduced-motion` for animations
- **Skip link**: Add a "Skip to content" link as the first focusable element

```typescript
// Skip to content link
<a href="#main" className="sr-only focus:not-sr-only focus:absolute focus:top-4 focus:left-4 focus:z-50 focus:rounded focus:bg-primary focus:px-4 focus:py-2 focus:text-white">
  Skip to main content
</a>
<main id="main">...</main>
```

## Animation & Motion

- Use subtle animations for polish — don't overdo it
- Fade-in on scroll for sections: `opacity-0 → opacity-100` with small `translateY`
- Hover effects on cards and buttons: scale or shadow change
- Keep transitions under 300ms for responsiveness
- Use `framer-motion` for complex animations, CSS transitions for simple ones
- Always respect `prefers-reduced-motion`

```css
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after {
    animation-duration: 0.01ms !important;
    transition-duration: 0.01ms !important;
  }
}
```
