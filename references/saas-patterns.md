# SaaS UI Patterns Reference

Comprehensive patterns and code examples for building consistent, user-friendly SaaS applications using shadcn/ui, React Hook Form, and Zod.

---

## 1. Resource List Pattern

Data tables are the backbone of SaaS dashboards. This pattern combines shadcn Table with @tanstack/react-table for a feature-rich list experience.

### Features
- Search/filter by multiple columns
- Sortable columns
- Pagination (client-side or server-side)
- Bulk actions with checkboxes
- Row actions menu
- Column visibility toggle

### Component Structure

```tsx
// types/resources.ts
export interface Resource {
  id: string;
  name: string;
  email: string;
  status: 'active' | 'inactive' | 'pending';
  createdAt: string;
  updatedAt: string;
}

// components/ResourceList.tsx
import React, { useState } from 'react';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Checkbox } from '@/components/ui/checkbox';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import {
  ColumnDef,
  flexRender,
  getCoreRowModel,
  getPaginationRowModel,
  getSortedRowModel,
  getFilteredRowModel,
  SortingState,
  ColumnFiltersState,
  useReactTable,
  PaginationState,
} from '@tanstack/react-table';
import { ArrowUpDown, MoreHorizontal, ChevronDown } from 'lucide-react';
import { Badge } from '@/components/ui/badge';

export interface ResourceListProps {
  data: Resource[];
  onEdit?: (resource: Resource) => void;
  onDelete?: (resourceId: string) => void;
  isLoading?: boolean;
}

export function ResourceList({
  data,
  onEdit,
  onDelete,
  isLoading,
}: ResourceListProps) {
  const [sorting, setSorting] = useState<SortingState>([]);
  const [columnFilters, setColumnFilters] = useState<ColumnFiltersState>([]);
  const [rowSelection, setRowSelection] = useState({});
  const [globalFilter, setGlobalFilter] = useState('');
  const [pagination, setPagination] = useState<PaginationState>({
    pageIndex: 0,
    pageSize: 10,
  });

  const columns: ColumnDef<Resource>[] = [
    {
      id: 'select',
      header: ({ table }) => (
        <Checkbox
          checked={table.getIsAllPageRowsSelected()}
          onCheckedChange={(value) =>
            table.toggleAllPageRowsSelected(!!value)
          }
          aria-label="Select all"
        />
      ),
      cell: ({ row }) => (
        <Checkbox
          checked={row.getIsSelected()}
          onCheckedChange={(value) => row.toggleSelected(!!value)}
          aria-label="Select row"
        />
      ),
      enableSorting: false,
      enableHiding: false,
    },
    {
      accessorKey: 'name',
      header: ({ column }) => (
        <Button
          variant="ghost"
          onClick={() =>
            column.toggleSorting(column.getIsSortedDesc() === undefined ? false : !column.getIsSortedDesc())
          }
        >
          Name
          <ArrowUpDown className="ml-2 h-4 w-4" />
        </Button>
      ),
      cell: ({ row }) => <div className="font-medium">{row.getValue('name')}</div>,
    },
    {
      accessorKey: 'email',
      header: 'Email',
      cell: ({ row }) => <div>{row.getValue('email')}</div>,
    },
    {
      accessorKey: 'status',
      header: 'Status',
      cell: ({ row }) => {
        const status = row.getValue('status') as string;
        const variants: Record<string, 'default' | 'secondary' | 'destructive' | 'outline'> = {
          active: 'default',
          inactive: 'secondary',
          pending: 'outline',
        };
        return <Badge variant={variants[status] || 'default'}>{status}</Badge>;
      },
      filterFn: (row, id, value) => {
        return value.includes(row.getValue(id));
      },
    },
    {
      accessorKey: 'createdAt',
      header: 'Created',
      cell: ({ row }) => (
        <div className="text-sm text-gray-500">
          {new Date(row.getValue('createdAt')).toLocaleDateString()}
        </div>
      ),
    },
    {
      id: 'actions',
      enableHiding: false,
      cell: ({ row }) => (
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button variant="ghost" className="h-8 w-8 p-0">
              <span className="sr-only">Open menu</span>
              <MoreHorizontal className="h-4 w-4" />
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end">
            <DropdownMenuItem onClick={() => onEdit?.(row.original)}>
              Edit
            </DropdownMenuItem>
            <DropdownMenuItem
              onClick={() => onDelete?.(row.original.id)}
              className="text-red-600"
            >
              Delete
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      ),
    },
  ];

  const table = useReactTable({
    data,
    columns,
    getCoreRowModel: getCoreRowModel(),
    getPaginationRowModel: getPaginationRowModel(),
    getSortedRowModel: getSortedRowModel(),
    getFilteredRowModel: getFilteredRowModel(),
    onSortingChange: setSorting,
    onColumnFiltersChange: setColumnFilters,
    onRowSelectionChange: setRowSelection,
    onPaginationChange: setPagination,
    globalFilterFn: 'includesString',
    state: {
      sorting,
      columnFilters,
      rowSelection,
      globalFilter,
      pagination,
    },
  });

  const selectedCount = Object.keys(rowSelection).length;

  return (
    <div className="space-y-4">
      {/* Search Bar */}
      <div className="flex gap-4">
        <Input
          placeholder="Search resources..."
          value={globalFilter}
          onChange={(e) => setGlobalFilter(e.target.value)}
          className="max-w-sm"
        />
        {selectedCount > 0 && (
          <div className="flex items-center gap-2">
            <span className="text-sm text-gray-600">{selectedCount} selected</span>
            <Button
              variant="destructive"
              size="sm"
              onClick={() => {
                table.getSelectedRowModel().rows.forEach((row) => {
                  onDelete?.(row.original.id);
                });
                setRowSelection({});
              }}
            >
              Delete Selected
            </Button>
          </div>
        )}
      </div>

      {/* Table */}
      <div className="rounded-lg border">
        <Table>
          <TableHeader>
            {table.getHeaderGroups().map((headerGroup) => (
              <TableRow key={headerGroup.id}>
                {headerGroup.headers.map((header) => (
                  <TableHead key={header.id}>
                    {header.isPlaceholder
                      ? null
                      : flexRender(header.column.columnDef.header, header.getContext())}
                  </TableHead>
                ))}
              </TableRow>
            ))}
          </TableHeader>
          <TableBody>
            {isLoading ? (
              <TableRow>
                <TableCell colSpan={columns.length} className="h-24 text-center">
                  Loading...
                </TableCell>
              </TableRow>
            ) : table.getRowModel().rows.length === 0 ? (
              <TableRow>
                <TableCell colSpan={columns.length} className="h-24 text-center">
                  No results found.
                </TableCell>
              </TableRow>
            ) : (
              table.getRowModel().rows.map((row) => (
                <TableRow key={row.id} data-state={row.getIsSelected() && 'selected'}>
                  {row.getVisibleCells().map((cell) => (
                    <TableCell key={cell.id}>
                      {flexRender(cell.column.columnDef.cell, cell.getContext())}
                    </TableCell>
                  ))}
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      </div>

      {/* Pagination */}
      <div className="flex items-center justify-between">
        <div className="text-sm text-gray-600">
          Page {table.getState().pagination.pageIndex + 1} of{' '}
          {table.getPageCount()}
        </div>
        <div className="flex gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={() => table.previousPage()}
            disabled={!table.getCanPreviousPage()}
          >
            Previous
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={() => table.nextPage()}
            disabled={!table.getCanNextPage()}
          >
            Next
          </Button>
        </div>
      </div>
    </div>
  );
}
```

---

## 2. Resource Detail Pattern

Display detailed information about a single resource with tabbed navigation, related data tables, and action buttons.

### Component Structure

```tsx
// components/ResourceDetail.tsx
import React from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogTitle,
  AlertDialogTrigger,
} from '@/components/ui/alert-dialog';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Edit, Trash2, ChevronLeft } from 'lucide-react';

export interface ResourceDetailProps {
  resource: Resource;
  relatedData?: {
    label: string;
    items: any[];
  }[];
  onEdit?: () => void;
  onDelete?: () => void;
  onBack?: () => void;
}

export function ResourceDetail({
  resource,
  relatedData = [],
  onEdit,
  onDelete,
  onBack,
}: ResourceDetailProps) {
  return (
    <div className="space-y-6">
      {/* Header with back button and actions */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Button
            variant="ghost"
            size="sm"
            onClick={onBack}
            className="gap-2"
          >
            <ChevronLeft className="h-4 w-4" />
            Back
          </Button>
          <div>
            <h1 className="text-3xl font-bold">{resource.name}</h1>
            <p className="text-gray-500">{resource.email}</p>
          </div>
        </div>
        <div className="flex gap-2">
          <Button onClick={onEdit} gap-2>
            <Edit className="h-4 w-4" />
            Edit
          </Button>
          <AlertDialog>
            <AlertDialogTrigger asChild>
              <Button variant="destructive" className="gap-2">
                <Trash2 className="h-4 w-4" />
                Delete
              </Button>
            </AlertDialogTrigger>
            <AlertDialogContent>
              <AlertDialogTitle>Delete Resource?</AlertDialogTitle>
              <AlertDialogDescription>
                This action cannot be undone. This will permanently delete the resource
                and remove all associated data.
              </AlertDialogDescription>
              <div className="flex gap-2 justify-end">
                <AlertDialogCancel>Cancel</AlertDialogCancel>
                <AlertDialogAction onClick={onDelete} className="bg-red-600">
                  Delete
                </AlertDialogAction>
              </div>
            </AlertDialogContent>
          </AlertDialog>
        </div>
      </div>

      {/* Tabs: Overview, Related Data, Activity */}
      <Tabs defaultValue="overview" className="space-y-4">
        <TabsList>
          <TabsTrigger value="overview">Overview</TabsTrigger>
          {relatedData.map((rel) => (
            <TabsTrigger key={rel.label} value={rel.label}>
              {rel.label}
            </TabsTrigger>
          ))}
          <TabsTrigger value="activity">Activity</TabsTrigger>
        </TabsList>

        {/* Overview Tab */}
        <TabsContent value="overview" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Details</CardTitle>
            </CardHeader>
            <CardContent className="grid grid-cols-2 gap-6">
              <div>
                <h4 className="text-sm font-medium text-gray-600">Name</h4>
                <p className="mt-1 text-lg">{resource.name}</p>
              </div>
              <div>
                <h4 className="text-sm font-medium text-gray-600">Email</h4>
                <p className="mt-1 text-lg">{resource.email}</p>
              </div>
              <div>
                <h4 className="text-sm font-medium text-gray-600">Status</h4>
                <div className="mt-1">
                  <Badge>{resource.status}</Badge>
                </div>
              </div>
              <div>
                <h4 className="text-sm font-medium text-gray-600">Created</h4>
                <p className="mt-1 text-lg">
                  {new Date(resource.createdAt).toLocaleDateString()}
                </p>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Related Data Tabs */}
        {relatedData.map((rel) => (
          <TabsContent key={rel.label} value={rel.label}>
            <Card>
              <CardHeader>
                <CardTitle>{rel.label}</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="rounded-lg border">
                  <Table>
                    <TableHeader>
                      <TableRow>
                        {Object.keys(rel.items[0] || {}).map((key) => (
                          <TableHead key={key}>{key}</TableHead>
                        ))}
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {rel.items.length === 0 ? (
                        <TableRow>
                          <TableCell colSpan={Object.keys(rel.items[0] || {}).length}>
                            No items
                          </TableCell>
                        </TableRow>
                      ) : (
                        rel.items.map((item, idx) => (
                          <TableRow key={idx}>
                            {Object.values(item).map((val, vidx) => (
                              <TableCell key={vidx}>{String(val)}</TableCell>
                            ))}
                          </TableRow>
                        ))
                      )}
                    </TableBody>
                  </Table>
                </div>
              </CardContent>
            </Card>
          </TabsContent>
        ))}

        {/* Activity Tab */}
        <TabsContent value="activity">
          <Card>
            <CardHeader>
              <CardTitle>Activity Log</CardTitle>
              <CardDescription>Recent changes to this resource</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div className="flex gap-4 pb-4 border-b">
                  <div className="flex-1">
                    <p className="font-medium">Resource created</p>
                    <p className="text-sm text-gray-500">
                      {new Date(resource.createdAt).toLocaleString()}
                    </p>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}
```

---

## 3. CRUD Form Pattern

Create and edit forms using shadcn Form, React Hook Form, and Zod for type-safe validation.

### OpenAPI Type to Form Component Mapping

| OpenAPI Type | Form Component | Example |
|---|---|---|
| `string` | Input | `<Input type="text" />` |
| `string` (enum) | Select | `<Select><SelectItem>Option 1</SelectItem></Select>` |
| `string` (format: email) | Input | `<Input type="email" />` |
| `string` (format: date-time) | Date Picker | `<Popover>...<Calendar /></Popover>` |
| `string` (format: uri) | Input | `<Input type="url" />` |
| `integer`/`number` | Input | `<Input type="number" />` |
| `boolean` | Switch or Checkbox | `<Switch />` or `<Checkbox />` |
| `array` | Multi-select or Tag Input | `<MultiSelect />` |
| `object` (nested) | Fieldset/Card | `<fieldset><Card>...</Card></fieldset>` |

### Component Example

```tsx
// types/schemas.ts
import { z } from 'zod';

export const ResourceFormSchema = z.object({
  name: z.string().min(1, 'Name is required').max(255),
  email: z.string().email('Invalid email address'),
  status: z.enum(['active', 'inactive', 'pending']),
  description: z.string().optional(),
  website: z.string().url('Invalid URL').optional(),
  tags: z.array(z.string()).default([]),
  isPublished: z.boolean().default(false),
  metadata: z.object({
    color: z.string().optional(),
    priority: z.number().min(1).max(5).optional(),
  }).optional(),
  birthDate: z.string().datetime().optional(),
});

export type ResourceFormData = z.infer<typeof ResourceFormSchema>;

// components/ResourceForm.tsx
import React, { useState } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Checkbox } from '@/components/ui/checkbox';
import { Switch } from '@/components/ui/switch';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  Form,
  FormControl,
  FormDescription,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from '@/components/ui/form';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from '@/components/ui/popover';
import { Calendar } from '@/components/ui/calendar';
import { format } from 'date-fns';
import { CalendarIcon } from 'lucide-react';

interface ResourceFormProps {
  initialData?: ResourceFormData;
  isLoading?: boolean;
  onSubmit: (data: ResourceFormData) => Promise<void>;
}

export function ResourceForm({
  initialData,
  isLoading,
  onSubmit,
}: ResourceFormProps) {
  const [submitError, setSubmitError] = useState<string | null>(null);

  const form = useForm<ResourceFormData>({
    resolver: zodResolver(ResourceFormSchema),
    defaultValues: initialData || {
      name: '',
      email: '',
      status: 'active',
      description: '',
      website: '',
      tags: [],
      isPublished: false,
      metadata: {},
    },
  });

  const handleSubmit = async (data: ResourceFormData) => {
    try {
      setSubmitError(null);
      await onSubmit(data);
    } catch (error) {
      setSubmitError(error instanceof Error ? error.message : 'An error occurred');
    }
  };

  return (
    <Form {...form}>
      <form onSubmit={form.handleSubmit(handleSubmit)} className="space-y-8">
        {submitError && (
          <div className="rounded-lg bg-red-50 p-4 text-red-800">
            {submitError}
          </div>
        )}

        {/* Basic Info Section */}
        <Card>
          <CardHeader>
            <CardTitle>Basic Information</CardTitle>
          </CardHeader>
          <CardContent className="space-y-6">
            {/* String Input */}
            <FormField
              control={form.control}
              name="name"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Name</FormLabel>
                  <FormControl>
                    <Input placeholder="Enter resource name" {...field} />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />

            {/* Email Input */}
            <FormField
              control={form.control}
              name="email"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Email</FormLabel>
                  <FormControl>
                    <Input type="email" placeholder="example@domain.com" {...field} />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />

            {/* Select (Enum) */}
            <FormField
              control={form.control}
              name="status"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Status</FormLabel>
                  <Select onValueChange={field.onChange} defaultValue={field.value}>
                    <FormControl>
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                    </FormControl>
                    <SelectContent>
                      <SelectItem value="active">Active</SelectItem>
                      <SelectItem value="inactive">Inactive</SelectItem>
                      <SelectItem value="pending">Pending</SelectItem>
                    </SelectContent>
                  </Select>
                  <FormMessage />
                </FormItem>
              )}
            />

            {/* URL Input */}
            <FormField
              control={form.control}
              name="website"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Website</FormLabel>
                  <FormControl>
                    <Input type="url" placeholder="https://example.com" {...field} />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />

            {/* Text Area (Long String) */}
            <FormField
              control={form.control}
              name="description"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Description</FormLabel>
                  <FormControl>
                    <textarea
                      placeholder="Enter description"
                      className="min-h-24 w-full rounded-md border border-input bg-background px-3 py-2"
                      {...field}
                    />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />
          </CardContent>
        </Card>

        {/* Advanced Section */}
        <Card>
          <CardHeader>
            <CardTitle>Advanced Options</CardTitle>
          </CardHeader>
          <CardContent className="space-y-6">
            {/* DateTime Picker */}
            <FormField
              control={form.control}
              name="birthDate"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Birth Date</FormLabel>
                  <Popover>
                    <PopoverTrigger asChild>
                      <FormControl>
                        <Button
                          variant="outline"
                          className="w-full justify-start text-left font-normal"
                        >
                          {field.value
                            ? format(new Date(field.value), 'PPP')
                            : 'Pick a date'}
                          <CalendarIcon className="ml-auto h-4 w-4 opacity-50" />
                        </Button>
                      </FormControl>
                    </PopoverTrigger>
                    <PopoverContent className="w-auto p-0">
                      <Calendar
                        mode="single"
                        selected={field.value ? new Date(field.value) : undefined}
                        onSelect={(date) =>
                          field.onChange(date?.toISOString())
                        }
                      />
                    </PopoverContent>
                  </Popover>
                  <FormMessage />
                </FormItem>
              )}
            />

            {/* Boolean Switch */}
            <FormField
              control={form.control}
              name="isPublished"
              render={({ field }) => (
                <FormItem className="flex items-center justify-between">
                  <div>
                    <FormLabel>Published</FormLabel>
                    <FormDescription>Make this resource visible to others</FormDescription>
                  </div>
                  <FormControl>
                    <Switch
                      checked={field.value}
                      onCheckedChange={field.onChange}
                    />
                  </FormControl>
                </FormItem>
              )}
            />

            {/* Array (Tags) */}
            <FormField
              control={form.control}
              name="tags"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Tags</FormLabel>
                  <FormControl>
                    <div className="space-y-2">
                      <Input
                        placeholder="Type a tag and press Enter"
                        onKeyDown={(e) => {
                          if (e.key === 'Enter') {
                            e.preventDefault();
                            const value = (e.target as HTMLInputElement).value.trim();
                            if (value && !field.value.includes(value)) {
                              field.onChange([...field.value, value]);
                              (e.target as HTMLInputElement).value = '';
                            }
                          }
                        }}
                      />
                      <div className="flex flex-wrap gap-2">
                        {field.value.map((tag) => (
                          <button
                            key={tag}
                            onClick={() =>
                              field.onChange(field.value.filter((t) => t !== tag))
                            }
                            className="rounded-full bg-blue-100 px-3 py-1 text-sm text-blue-800 hover:bg-blue-200"
                          >
                            {tag} ×
                          </button>
                        ))}
                      </div>
                    </div>
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />
          </CardContent>
        </Card>

        {/* Nested Object (Metadata) */}
        <Card>
          <CardHeader>
            <CardTitle>Metadata</CardTitle>
          </CardHeader>
          <CardContent className="space-y-6">
            <FormField
              control={form.control}
              name="metadata.color"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Color</FormLabel>
                  <FormControl>
                    <Input type="color" {...field} />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />

            <FormField
              control={form.control}
              name="metadata.priority"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Priority</FormLabel>
                  <FormControl>
                    <Input
                      type="number"
                      min="1"
                      max="5"
                      {...field}
                      onChange={(e) => field.onChange(e.target.value ? parseInt(e.target.value) : undefined)}
                    />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />
          </CardContent>
        </Card>

        {/* Submit Button */}
        <Button type="submit" disabled={isLoading} className="w-full">
          {isLoading ? 'Saving...' : 'Save Resource'}
        </Button>
      </form>
    </Form>
  );
}
```

---

## 4. Dashboard Pattern

High-level overview with stat cards, charts, and recent activity.

```tsx
// components/Dashboard.tsx
import React from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { TrendingUp, Users, BarChart3, Activity } from 'lucide-react';

interface StatCardProps {
  title: string;
  value: string | number;
  change?: number;
  description?: string;
  icon?: React.ReactNode;
}

function StatCard({ title, value, change, description, icon }: StatCardProps) {
  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <CardTitle className="text-sm font-medium">{title}</CardTitle>
        {icon && <div className="text-gray-500">{icon}</div>}
      </CardHeader>
      <CardContent>
        <div className="text-2xl font-bold">{value}</div>
        {change !== undefined && (
          <p className={`text-xs ${change >= 0 ? 'text-green-600' : 'text-red-600'}`}>
            {change >= 0 ? '+' : ''}{change}% from last month
          </p>
        )}
        {description && <p className="text-xs text-gray-500">{description}</p>}
      </CardContent>
    </Card>
  );
}

export function Dashboard() {
  return (
    <div className="space-y-8">
      {/* Stats Grid */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <StatCard
          title="Total Users"
          value="1,234"
          change={12}
          icon={<Users className="h-4 w-4" />}
        />
        <StatCard
          title="Active Sessions"
          value="456"
          change={-3}
          icon={<Activity className="h-4 w-4" />}
        />
        <StatCard
          title="Revenue"
          value="$12,345"
          change={8}
          icon={<TrendingUp className="h-4 w-4" />}
        />
        <StatCard
          title="Conversion Rate"
          value="3.2%"
          change={0.5}
          icon={<BarChart3 className="h-4 w-4" />}
        />
      </div>

      {/* Charts Section */}
      <div className="grid gap-4 md:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Revenue Trend</CardTitle>
            <CardDescription>Last 30 days</CardDescription>
          </CardHeader>
          <CardContent className="h-64 flex items-center justify-center text-gray-500">
            Chart placeholder
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>User Distribution</CardTitle>
            <CardDescription>By region</CardDescription>
          </CardHeader>
          <CardContent className="h-64 flex items-center justify-center text-gray-500">
            Chart placeholder
          </CardContent>
        </Card>
      </div>

      {/* Recent Activity */}
      <Card>
        <CardHeader>
          <CardTitle>Recent Activity</CardTitle>
          <CardDescription>Last 10 activities</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {[...Array(5)].map((_, i) => (
              <div key={i} className="flex items-center gap-4 pb-4 border-b last:border-b-0">
                <div className="h-2 w-2 rounded-full bg-blue-500" />
                <div className="flex-1">
                  <p className="font-medium">Activity Item {i + 1}</p>
                  <p className="text-sm text-gray-500">2 hours ago</p>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
```

---

## 5. Auth Pattern

Login, register, and forgot password flows.

```tsx
// components/LoginForm.tsx
import React from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from '@/components/ui/form';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';

const LoginSchema = z.object({
  email: z.string().email('Invalid email'),
  password: z.string().min(8, 'Password must be at least 8 characters'),
});

type LoginFormData = z.infer<typeof LoginSchema>;

export function LoginForm({ onSubmit }: { onSubmit: (data: LoginFormData) => Promise<void> }) {
  const [isLoading, setIsLoading] = React.useState(false);

  const form = useForm<LoginFormData>({
    resolver: zodResolver(LoginSchema),
    defaultValues: { email: '', password: '' },
  });

  const handleSubmit = async (data: LoginFormData) => {
    setIsLoading(true);
    try {
      await onSubmit(data);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="flex items-center justify-center min-h-screen">
      <Card className="w-full max-w-md">
        <CardHeader>
          <CardTitle>Sign In</CardTitle>
          <CardDescription>Enter your credentials to access your account</CardDescription>
        </CardHeader>
        <CardContent>
          <Form {...form}>
            <form onSubmit={form.handleSubmit(handleSubmit)} className="space-y-4">
              <FormField
                control={form.control}
                name="email"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Email</FormLabel>
                    <FormControl>
                      <Input type="email" placeholder="you@example.com" {...field} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />

              <FormField
                control={form.control}
                name="password"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Password</FormLabel>
                    <FormControl>
                      <Input type="password" placeholder="••••••••" {...field} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />

              <Button type="submit" disabled={isLoading} className="w-full">
                {isLoading ? 'Signing in...' : 'Sign In'}
              </Button>
            </form>
          </Form>

          <div className="mt-4 space-y-2 text-sm">
            <a href="/forgot-password" className="text-blue-600 hover:underline">
              Forgot password?
            </a>
            <div>
              Don't have an account?{' '}
              <a href="/signup" className="text-blue-600 hover:underline">
                Sign up
              </a>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
```

---

## 6. Empty State Pattern

Show when there's no data in a list or section.

```tsx
// components/EmptyState.tsx
import React from 'react';
import { Button } from '@/components/ui/button';
import { AlertCircle } from 'lucide-react';

interface EmptyStateProps {
  title: string;
  description: string;
  action?: {
    label: string;
    onClick: () => void;
  };
  illustration?: React.ReactNode;
}

export function EmptyState({
  title,
  description,
  action,
  illustration,
}: EmptyStateProps) {
  return (
    <div className="flex flex-col items-center justify-center rounded-lg border border-dashed py-12 px-4">
      {illustration ? (
        <div className="mb-4 text-6xl">{illustration}</div>
      ) : (
        <AlertCircle className="mb-4 h-12 w-12 text-gray-400" />
      )}
      <h3 className="text-lg font-semibold">{title}</h3>
      <p className="mt-2 text-center text-sm text-gray-500">{description}</p>
      {action && (
        <Button onClick={action.onClick} className="mt-4">
          {action.label}
        </Button>
      )}
    </div>
  );
}

// Usage
<EmptyState
  title="No resources yet"
  description="Get started by creating your first resource"
  action={{
    label: 'Create Resource',
    onClick: () => navigate('/resources/new'),
  }}
  illustration="📁"
/>
```

---

## 7. Mock Data Pattern

Generate realistic mock data from OpenAPI schemas with search, filter, and pagination helpers.

```ts
// utils/mockData.ts
import { faker } from '@faker-js/faker';

export interface MockDataOptions {
  count?: number;
  seed?: number;
}

export function generateMockResources(options: MockDataOptions = {}) {
  const { count = 50, seed = 123 } = options;
  faker.seed(seed);

  return Array.from({ length: count }, (_, i) => ({
    id: `resource-${i + 1}`,
    name: faker.company.name(),
    email: faker.internet.email(),
    status: faker.helpers.arrayElement(['active', 'inactive', 'pending'] as const),
    createdAt: faker.date.past().toISOString(),
    updatedAt: faker.date.recent().toISOString(),
  }));
}

// Filter, Search, Paginate helpers
export function searchResources(
  data: Resource[],
  query: string,
  searchFields: (keyof Resource)[] = ['name', 'email'],
): Resource[] {
  if (!query) return data;

  const lower = query.toLowerCase();
  return data.filter((item) =>
    searchFields.some((field) =>
      String(item[field]).toLowerCase().includes(lower),
    ),
  );
}

export function filterResources(
  data: Resource[],
  filters: Partial<Record<keyof Resource, any>>,
): Resource[] {
  return data.filter((item) =>
    Object.entries(filters).every(
      ([key, value]) => item[key as keyof Resource] === value,
    ),
  );
}

export function paginateData<T>(
  data: T[],
  pageIndex: number,
  pageSize: number,
): T[] {
  return data.slice(pageIndex * pageSize, (pageIndex + 1) * pageSize);
}

// Simulate server delay
export async function withDelay<T>(value: T, ms = 300): Promise<T> {
  return new Promise((resolve) => setTimeout(() => resolve(value), ms));
}
```

---

## 8. Navigation Pattern

Sidebar with collapsible sections, active state, and responsive behavior.

```tsx
// components/Sidebar.tsx
import React, { useState } from 'react';
import { useLocation } from 'react-router-dom';
import {
  Layout,
  BarChart3,
  Users,
  Settings,
  ChevronDown,
  Menu,
  X,
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { cn } from '@/lib/utils';

interface NavItem {
  title: string;
  href: string;
  icon?: React.ReactNode;
  items?: NavItem[];
}

const navItems: NavItem[] = [
  {
    title: 'Dashboard',
    href: '/dashboard',
    icon: <Layout className="h-4 w-4" />,
  },
  {
    title: 'Analytics',
    href: '/analytics',
    icon: <BarChart3 className="h-4 w-4" />,
  },
  {
    title: 'Users',
    href: '/users',
    icon: <Users className="h-4 w-4" />,
    items: [
      { title: 'All Users', href: '/users' },
      { title: 'Active', href: '/users?status=active' },
      { title: 'Inactive', href: '/users?status=inactive' },
    ],
  },
  {
    title: 'Settings',
    href: '/settings',
    icon: <Settings className="h-4 w-4" />,
  },
];

export function Sidebar() {
  const [isOpen, setIsOpen] = useState(true);
  const [expandedItems, setExpandedItems] = useState<Set<string>>(new Set());
  const location = useLocation();

  const toggleExpand = (title: string) => {
    const newExpanded = new Set(expandedItems);
    if (newExpanded.has(title)) {
      newExpanded.delete(title);
    } else {
      newExpanded.add(title);
    }
    setExpandedItems(newExpanded);
  };

  const isActive = (href: string) => location.pathname === href;

  return (
    <>
      {/* Mobile Toggle */}
      <Button
        variant="ghost"
        size="sm"
        onClick={() => setIsOpen(!isOpen)}
        className="fixed left-4 top-4 z-50 lg:hidden"
      >
        {isOpen ? <X className="h-4 w-4" /> : <Menu className="h-4 w-4" />}
      </Button>

      {/* Sidebar */}
      <aside
        className={cn(
          'fixed left-0 top-0 z-40 h-screen w-64 border-r bg-white transition-transform lg:translate-x-0',
          isOpen ? 'translate-x-0' : '-translate-x-full',
        )}
      >
        <div className="p-6">
          <h1 className="text-xl font-bold">SaaS</h1>
        </div>

        <nav className="space-y-1 px-2">
          {navItems.map((item) => (
            <div key={item.title}>
              <a
                href={item.href}
                onClick={(e) => {
                  if (item.items) {
                    e.preventDefault();
                    toggleExpand(item.title);
                  }
                }}
                className={cn(
                  'flex items-center gap-2 rounded-lg px-4 py-2 text-sm font-medium transition-colors',
                  isActive(item.href)
                    ? 'bg-blue-100 text-blue-900'
                    : 'text-gray-700 hover:bg-gray-100',
                )}
              >
                {item.icon}
                <span className="flex-1">{item.title}</span>
                {item.items && (
                  <ChevronDown
                    className={cn(
                      'h-4 w-4 transition-transform',
                      expandedItems.has(item.title) ? 'rotate-180' : '',
                    )}
                  />
                )}
              </a>

              {/* Nested Items */}
              {item.items && expandedItems.has(item.title) && (
                <div className="space-y-1 pl-4">
                  {item.items.map((subItem) => (
                    <a
                      key={subItem.title}
                      href={subItem.href}
                      className={cn(
                        'block rounded-lg px-4 py-2 text-sm transition-colors',
                        isActive(subItem.href)
                          ? 'bg-blue-100 text-blue-900 font-medium'
                          : 'text-gray-600 hover:bg-gray-100',
                      )}
                    >
                      {subItem.title}
                    </a>
                  ))}
                </div>
              )}
            </div>
          ))}
        </nav>
      </aside>

      {/* Mobile Overlay */}
      {isOpen && (
        <div
          className="fixed inset-0 z-30 bg-black/50 lg:hidden"
          onClick={() => setIsOpen(false)}
        />
      )}

      {/* Content Offset */}
      <div className="lg:ml-64" />
    </>
  );
}
```

---

## Usage Guidelines

1. **Start with the Resource List** when building a new feature. It's the foundation for most SaaS apps.
2. **Compose patterns together**: List → Detail → Edit Form creates a complete CRUD workflow.
3. **Reuse components**: These patterns are building blocks. Mix and match shadcn/ui components.
4. **Type safety**: Use Zod schemas for forms and mock data generation to keep types aligned.
5. **Mock early**: Generate mock data before building backend integrations.
6. **Test responsiveness**: All patterns include responsive utilities (use Tailwind's md/lg breakpoints).

For more information on shadcn/ui components, visit https://ui.shadcn.com
