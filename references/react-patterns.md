# Essential React & Next.js Patterns for SaaS

Bundled subset of critical patterns from Vercel's react-best-practices.
If the full `vercel-react-best-practices` skill is installed, prefer that for comprehensive coverage.

## Server Components by Default

Next.js App Router uses Server Components by default. This means zero JavaScript shipped
to the client unless you explicitly opt in with `'use client'`.

**Rule**: Only add `'use client'` when the component needs:
- Event handlers (onClick, onChange, onSubmit)
- useState, useEffect, useRef, or other hooks
- Browser APIs (window, document, localStorage)

```typescript
// GOOD: Server Component (default) — no JS sent to client
export default function DataTable({ data }) {
  return (
    <table className="w-full">
      <tbody>
        {data.map(row => <tr key={row.id}><td>{row.name}</td></tr>)}
      </tbody>
    </table>
  )
}

// Client component only when interactivity is needed
'use client'
import { useState } from 'react'

export function TableSort({ initialData }) {
  const [sortBy, setSortBy] = useState('name')
  return (
    <button onClick={() => setSortBy('date')}>Sort by date</button>
  )
}
```

## Eliminate Async Waterfalls (CRITICAL)

Never await sequentially when requests are independent:

```typescript
// BAD: Sequential — each request waits for the previous
const users = await getUsers()
const stats = await getStats()
const recentActivity = await getRecentActivity()

// GOOD: Parallel — all requests fire simultaneously
const [users, stats, recentActivity] = await Promise.all([
  getUsers(),
  getStats(),
  getRecentActivity(),
])
```

## Bundle Size (CRITICAL)

### Avoid Barrel Imports
```typescript
// BAD: Imports entire library
import { Button } from '@/components/ui'

// GOOD: Direct import
import { Button } from '@/components/ui/button'
```

### Dynamic Imports for Heavy Components
```typescript
import dynamic from 'next/dynamic'

// Load chart component only when needed
const Chart = dynamic(() => import('@/components/chart'), {
  loading: () => <div className="h-64 animate-pulse bg-muted rounded" />,
})
```

### Don't Import What You Don't Need
```typescript
// BAD: Import entire icon library
import * as Icons from 'lucide-react'

// GOOD: Import specific icons
import { BarChart3, Settings, Users, ChevronDown } from 'lucide-react'
```

## Image Optimization

Always use `next/image`:

```typescript
import Image from 'next/image'

// With known dimensions (preferred)
<Image src="/dashboard.webp" alt="Dashboard interface" width={1200} height={630} priority />

// Fill mode for responsive containers
<div className="relative aspect-video">
  <Image src="/dashboard.webp" alt="Dashboard interface" fill className="object-cover" />
</div>
```

## Font Optimization

Use `next/font` to prevent layout shift:

```typescript
import { Inter, Poppins } from 'next/font/google'

const inter = Inter({ subsets: ['latin'], display: 'swap', variable: '--font-inter' })
const poppins = Poppins({
  subsets: ['latin'],
  weight: ['400', '600', '700'],
  display: 'swap',
  variable: '--font-poppins',
})
```

## Data Fetching Patterns

### Fetch in Server Components
```typescript
// Server Component — data fetched at build or request time, zero client JS
export default async function UsersPage() {
  const users = await getUsers()  // Runs on the server only
  return <UserTable users={users} />
}
```

### Use Suspense for Loading States
```typescript
import { Suspense } from 'react'

export default function Dashboard() {
  return (
    <main>
      <DashboardHeader />  {/* Renders immediately */}
      <Suspense fallback={<StatsSkeleton />}>
        <DashboardStats />  {/* Streams in when ready */}
      </Suspense>
    </main>
  )
}
```

## Client-Side State Management for Interactive SaaS Pages

SaaS applications require rich client-side interactions. Use hooks for form state, filters, and UI toggles:

```typescript
'use client'
import { useState } from 'react'

export function UsersList() {
  const [filter, setFilter] = useState('')
  const [sortBy, setSortBy] = useState('name')

  return (
    <div>
      <input
        value={filter}
        onChange={(e) => setFilter(e.target.value)}
        placeholder="Search users..."
      />
      <button onClick={() => setSortBy(sortBy === 'name' ? 'date' : 'name')}>
        Sort by {sortBy}
      </button>
    </div>
  )
}
```

## 'use client' Pattern for Interactive Components

Mark components as client-side only when they need interactivity:

```typescript
'use client'
import { useState } from 'react'
import { Menu, X } from 'lucide-react'

export function Sidebar() {
  const [isOpen, setIsOpen] = useState(true)

  return (
    <aside className={`w-${isOpen ? '64' : '16'}`}>
      <button
        onClick={() => setIsOpen(!isOpen)}
        aria-label="Toggle sidebar"
      >
        {isOpen ? <X size={20} /> : <Menu size={20} />}
      </button>
      {isOpen && <nav>Navigation items</nav>}
    </aside>
  )
}
```

### Form Component Pattern
```typescript
'use client'
import { useState } from 'react'

export function EditUserForm({ userId, initialData }) {
  const [name, setName] = useState(initialData.name)
  const [email, setEmail] = useState(initialData.email)
  const [errors, setErrors] = useState({})
  const [isSubmitting, setIsSubmitting] = useState(false)

  const handleSubmit = async (e) => {
    e.preventDefault()
    setIsSubmitting(true)

    try {
      const response = await fetch(`/api/users/${userId}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name, email })
      })

      if (!response.ok) {
        const data = await response.json()
        setErrors(data.errors)
      }
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <form onSubmit={handleSubmit}>
      <input value={name} onChange={(e) => setName(e.target.value)} />
      {errors.name && <span className="text-red-500">{errors.name}</span>}

      <input value={email} onChange={(e) => setEmail(e.target.value)} />
      {errors.email && <span className="text-red-500">{errors.email}</span>}

      <button disabled={isSubmitting}>{isSubmitting ? 'Saving...' : 'Save'}</button>
    </form>
  )
}
```

## Dynamic Imports with Loading Skeletons

For heavy interactive components, defer loading:

```typescript
import dynamic from 'next/dynamic'

const DataVisualization = dynamic(() => import('@/components/charts/data-viz'), {
  loading: () => (
    <div className="h-96 bg-muted animate-pulse rounded-lg" />
  ),
  ssr: false  // Don't render on server, only client
})

export function AnalyticsPage() {
  return (
    <div>
      <h1>Analytics</h1>
      <DataVisualization />
    </div>
  )
}
```

## Route Handlers Simulating API Calls

Create route handlers that return mock data during development:

```typescript
// app/api/users/route.ts
export async function GET(request: Request) {
  // During development, return mock data
  const users = [
    { id: 1, name: 'Alice', email: 'alice@example.com' },
    { id: 2, name: 'Bob', email: 'bob@example.com' },
  ]

  return Response.json(users)
}

// app/api/users/[id]/route.ts
export async function GET(
  request: Request,
  { params }: { params: { id: string } }
) {
  // Mock user by ID
  const user = {
    id: parseInt(params.id),
    name: 'Alice',
    email: 'alice@example.com',
  }

  return Response.json(user)
}

export async function PUT(
  request: Request,
  { params }: { params: { id: string } }
) {
  const body = await request.json()

  // Validate input
  if (!body.name || !body.email) {
    return Response.json(
      { errors: { name: 'Name required', email: 'Email required' } },
      { status: 400 }
    )
  }

  // Return updated user
  const updatedUser = {
    id: parseInt(params.id),
    ...body,
  }

  return Response.json(updatedUser)
}
```

## Server Components with Client Interactive Islands

Combine server-rendered content with client-side interactive elements:

```typescript
// app/dashboard/page.tsx (Server Component)
import { getUserData } from '@/lib/data'
import { DashboardStats } from '@/components/dashboard-stats'
import { InteractiveChart } from '@/components/interactive-chart'

export default async function DashboardPage() {
  // Fetch data on server
  const stats = await getUserData()

  return (
    <main>
      {/* Server component — just renders data */}
      <DashboardStats stats={stats} />

      {/* Client component — handles interactivity */}
      <InteractiveChart initialData={stats.chartData} />
    </main>
  )
}

// components/dashboard-stats.tsx (Server Component)
export function DashboardStats({ stats }) {
  return (
    <div className="grid grid-cols-4 gap-4">
      {stats.cards.map(card => (
        <div key={card.id} className="p-4 border rounded-lg">
          <p className="text-sm text-muted-foreground">{card.label}</p>
          <p className="text-2xl font-bold">{card.value}</p>
        </div>
      ))}
    </div>
  )
}

// components/interactive-chart.tsx (Client Component)
'use client'
import { useState } from 'react'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip } from 'recharts'

export function InteractiveChart({ initialData }) {
  const [timeRange, setTimeRange] = useState('7d')

  // Filter data based on selected time range
  const filteredData = initialData.filter(point => {
    // Filtering logic based on timeRange
    return true
  })

  return (
    <div>
      <div className="flex gap-2 mb-4">
        {['7d', '30d', '90d'].map(range => (
          <button
            key={range}
            onClick={() => setTimeRange(range)}
            className={timeRange === range ? 'font-bold' : ''}
          >
            {range}
          </button>
        ))}
      </div>
      <LineChart width={600} height={300} data={filteredData}>
        <CartesianGrid />
        <XAxis dataKey="date" />
        <YAxis />
        <Tooltip />
        <Line type="monotone" dataKey="value" />
      </LineChart>
    </div>
  )
}
```

## Error Handling

### error.tsx (per route)
```typescript
'use client'

export default function Error({ error, reset }: { error: Error; reset: () => void }) {
  return (
    <div className="flex min-h-[50vh] flex-col items-center justify-center gap-4">
      <h2 className="text-2xl font-bold">Something went wrong</h2>
      <p className="text-muted-foreground">{error.message}</p>
      <button onClick={reset} className="rounded bg-primary px-4 py-2 text-white">
        Try again
      </button>
    </div>
  )
}
```

### not-found.tsx
```typescript
import Link from 'next/link'

export default function NotFound() {
  return (
    <div className="flex min-h-[50vh] flex-col items-center justify-center gap-4">
      <h1 className="text-4xl font-bold">404</h1>
      <p className="text-muted-foreground">Page not found</p>
      <Link href="/dashboard" className="text-primary underline">Go to dashboard</Link>
    </div>
  )
}
```

## Performance Checklist

- [ ] Server Components used by default (no unnecessary 'use client')
- [ ] `next/image` for all images
- [ ] `next/font` for all fonts
- [ ] `next/link` for all internal links
- [ ] No barrel imports
- [ ] Dynamic imports for heavy/below-fold components
- [ ] Parallel data fetching (Promise.all)
- [ ] Suspense boundaries for async content
- [ ] No unnecessary re-renders (stable references for callbacks)
- [ ] Route handlers for mock API calls (development)
- [ ] Form validation on both client and server
- [ ] Loading states for async operations
