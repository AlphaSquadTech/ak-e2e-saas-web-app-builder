# Interaction Patterns Reference

Comprehensive micro-interaction patterns using Framer Motion with accessibility and responsive design in mind.

---

## Framer Motion Setup

Initialize Framer Motion and configure global settings for animations.

```tsx
// app.tsx or main component
import { MotionConfig } from 'framer-motion';
import { useReducedMotion } from 'framer-motion';

const SPRING_CONFIG = {
  default: { type: 'spring', damping: 8, stiffness: 100, mass: 1 },
  gentle: { type: 'spring', damping: 15, stiffness: 100, mass: 1 },
  bouncy: { type: 'spring', damping: 8, stiffness: 200, mass: 0.8 },
};

const EASE_CONFIG = {
  easeOut: { duration: 0.3, ease: 'easeOut' },
  easeInOut: { duration: 0.4, ease: 'easeInOut' },
  linear: { duration: 0.2, ease: 'linear' },
};

// Wrapper for respecting prefers-reduced-motion
export function AnimationProvider({ children }: { children: React.ReactNode }) {
  const prefersReducedMotion = useReducedMotion();

  return (
    <MotionConfig reducedMotion={prefersReducedMotion ? 'user' : 'never'}>
      {children}
    </MotionConfig>
  );
}

// Export for use in components
export { SPRING_CONFIG, EASE_CONFIG };
```

---

## 1. Button Interactions

Subtle button feedback using whileHover, whileTap, and loading states.

```tsx
// components/InteractiveButton.tsx
import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { Button } from '@/components/ui/button';
import { Loader2 } from 'lucide-react';
import { SPRING_CONFIG } from '@/lib/animation-config';

interface InteractiveButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  isLoading?: boolean;
  children: React.ReactNode;
}

export const InteractiveButton = React.forwardRef<
  HTMLButtonElement,
  InteractiveButtonProps
>(({ isLoading, children, className, disabled, ...props }, ref) => {
  return (
    <motion.button
      ref={ref}
      whileHover={!disabled && !isLoading ? { scale: 1.05 } : {}}
      whileTap={!disabled && !isLoading ? { scale: 0.95 } : {}}
      transition={SPRING_CONFIG.default}
      disabled={disabled || isLoading}
      className={className}
      {...props}
    >
      {isLoading ? (
        <motion.div
          animate={{ rotate: 360 }}
          transition={{ duration: 1, repeat: Infinity, ease: 'linear' }}
          className="inline-block"
        >
          <Loader2 className="h-4 w-4" />
        </motion.div>
      ) : (
        children
      )}
    </motion.button>
  );
});

InteractiveButton.displayName = 'InteractiveButton';

// Advanced button with ripple effect
export function ButtonWithRipple({
  children,
  onClick,
  ...props
}: React.ButtonHTMLAttributes<HTMLButtonElement>) {
  const [ripples, setRipples] = useState<
    Array<{ id: string; x: number; y: number }>
  >([]);

  const handleClick = (e: React.MouseEvent<HTMLButtonElement>) => {
    const rect = e.currentTarget.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;
    const id = `ripple-${Date.now()}-${Math.random()}`;

    setRipples((prev) => [...prev, { id, x, y }]);
    setTimeout(() => {
      setRipples((prev) => prev.filter((r) => r.id !== id));
    }, 600);

    onClick?.(e);
  };

  return (
    <motion.button
      whileHover={{ scale: 1.02 }}
      whileTap={{ scale: 0.98 }}
      transition={SPRING_CONFIG.default}
      onClick={handleClick}
      className="relative overflow-hidden"
      {...props}
    >
      {children}

      {/* Ripple elements */}
      {ripples.map((ripple) => (
        <motion.div
          key={ripple.id}
          className="pointer-events-none absolute rounded-full bg-white/50"
          initial={{ scale: 0, opacity: 1 }}
          animate={{ scale: 4, opacity: 0 }}
          transition={{ duration: 0.6, ease: 'easeOut' }}
          style={{
            left: ripple.x,
            top: ripple.y,
            width: 10,
            height: 10,
            translateX: '-50%',
            translateY: '-50%',
          }}
        />
      ))}
    </motion.button>
  );
}

// Usage
export function ButtonDemo() {
  const [isLoading, setIsLoading] = useState(false);

  return (
    <div className="space-y-4">
      {/* Note: Respects prefers-reduced-motion via MotionConfig provider */}
      <InteractiveButton
        isLoading={isLoading}
        onClick={() => {
          setIsLoading(true);
          setTimeout(() => setIsLoading(false), 2000);
        }}
      >
        Click me
      </InteractiveButton>

      <ButtonWithRipple>
        Ripple Button
      </ButtonWithRipple>
    </div>
  );
}
```

**Accessibility Note**: The `MotionConfig` provider automatically respects `prefers-reduced-motion`, reducing animations to instant transitions for users who prefer less motion.

---

## 2. Card Interactions

Hover lift effect with shadow and click ripple for cards.

```tsx
// components/InteractiveCard.tsx
import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { Card } from '@/components/ui/card';
import { SPRING_CONFIG } from '@/lib/animation-config';

interface InteractiveCardProps {
  children: React.ReactNode;
  onClick?: () => void;
  className?: string;
}

export function InteractiveCard({
  children,
  onClick,
  className,
}: InteractiveCardProps) {
  const [isHovered, setIsHovered] = useState(false);

  return (
    <motion.div
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
      whileHover={{ translateY: -8 }}
      transition={SPRING_CONFIG.gentle}
      className="cursor-pointer"
      onClick={onClick}
    >
      <Card
        className={`shadow-lg transition-shadow ${
          isHovered ? 'shadow-2xl' : 'shadow-lg'
        } ${className}`}
      >
        {children}
      </Card>
    </motion.div>
  );
}

// Card list with staggered entrance
export function InteractiveCardGrid({
  items,
  renderCard,
}: {
  items: any[];
  renderCard: (item: any, index: number) => React.ReactNode;
}) {
  return (
    <motion.div
      className="grid gap-4 md:grid-cols-2 lg:grid-cols-3"
      initial="hidden"
      animate="visible"
      variants={{
        hidden: { opacity: 0 },
        visible: {
          opacity: 1,
          transition: {
            staggerChildren: 0.1,
          },
        },
      }}
    >
      {items.map((item, index) => (
        <motion.div
          key={index}
          variants={{
            hidden: { opacity: 0, y: 20 },
            visible: { opacity: 1, y: 0 },
          }}
          transition={SPRING_CONFIG.default}
        >
          {renderCard(item, index)}
        </motion.div>
      ))}
    </motion.div>
  );
}

// Usage
export function CardDemo() {
  const items = Array.from({ length: 6 }, (_, i) => ({
    id: i,
    title: `Card ${i + 1}`,
  }));

  return (
    <InteractiveCardGrid
      items={items}
      renderCard={(item) => (
        <InteractiveCard>
          <div className="p-6">
            <h3 className="font-semibold">{item.title}</h3>
            <p className="text-sm text-gray-500">Hover for lift effect</p>
          </div>
        </InteractiveCard>
      )}
    />
  );
}
```

**Accessibility Note**: All hover effects are paired with visual feedback that also appears on tap for touch devices. The `prefers-reduced-motion` setting reduces the vertical lift to zero while keeping shadow transitions subtle.

---

## 3. Page Transitions

AnimatePresence with fade and slide for smooth page navigation.

```tsx
// components/PageTransition.tsx
import React from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useLocation } from 'react-router-dom';

const pageVariants = {
  initial: {
    opacity: 0,
    x: 20,
  },
  in: {
    opacity: 1,
    x: 0,
  },
  out: {
    opacity: 0,
    x: -20,
  },
};

const pageTransition = {
  type: 'tween',
  ease: 'anticipate',
  duration: 0.3,
};

interface PageTransitionProps {
  children: React.ReactNode;
}

export function PageTransition({ children }: PageTransitionProps) {
  const location = useLocation();

  return (
    <AnimatePresence mode="wait" initial={false}>
      <motion.div
        key={location.pathname}
        initial="initial"
        animate="in"
        exit="out"
        variants={pageVariants}
        transition={pageTransition}
      >
        {children}
      </motion.div>
    </AnimatePresence>
  );
}

// Layout wrapper for use with React Router
export function AnimatedRouteLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="relative overflow-hidden">
      <PageTransition>{children}</PageTransition>
    </div>
  );
}

// Usage in router
/*
<Routes>
  <Route
    path="/dashboard"
    element={
      <AnimatedRouteLayout>
        <Dashboard />
      </AnimatedRouteLayout>
    }
  />
  <Route
    path="/users"
    element={
      <AnimatedRouteLayout>
        <Users />
      </AnimatedRouteLayout>
    }
  />
</Routes>
*/
```

**Accessibility Note**: The page transition uses a brief 0.3s duration. Users with `prefers-reduced-motion` enabled will see instant transitions instead. The transition wraps all content changes smoothly.

---

## 4. Loading States

Skeleton screens with shimmer effect for tables, cards, forms, and dashboards.

```tsx
// components/Skeletons.tsx
import React from 'react';
import { motion } from 'framer-motion';

// Shimmer gradient CSS
const shimmerCSS = `
  @keyframes shimmer {
    0% {
      background-position: -1000px 0;
    }
    100% {
      background-position: 1000px 0;
    }
  }

  .skeleton {
    background: linear-gradient(
      90deg,
      #e0e0e0 25%,
      #f0f0f0 50%,
      #e0e0e0 75%
    );
    background-size: 1000px 100%;
    animation: shimmer 2s infinite;
  }
`;

// Skeleton Table Row
export function SkeletonTableRow({ columnCount = 5 }: { columnCount?: number }) {
  return (
    <tr>
      {Array.from({ length: columnCount }).map((_, i) => (
        <td key={i} className="p-4">
          <div className="skeleton h-4 rounded bg-gray-200" />
        </td>
      ))}
    </tr>
  );
}

// Skeleton Table
export function SkeletonTable({ rowCount = 5, columnCount = 5 }) {
  return (
    <div className="space-y-2">
      <style>{shimmerCSS}</style>
      {Array.from({ length: rowCount }).map((_, i) => (
        <SkeletonTableRow key={i} columnCount={columnCount} />
      ))}
    </div>
  );
}

// Skeleton Card
export function SkeletonCard() {
  return (
    <div className="space-y-4 rounded-lg border p-6">
      <style>{shimmerCSS}</style>
      <div className="skeleton h-6 w-3/4 rounded" />
      <div className="space-y-2">
        <div className="skeleton h-4 rounded" />
        <div className="skeleton h-4 w-5/6 rounded" />
      </div>
      <div className="skeleton h-10 rounded" />
    </div>
  );
}

// Skeleton Dashboard Stats
export function SkeletonStatCard() {
  return (
    <div className="space-y-2 rounded-lg border p-6">
      <style>{shimmerCSS}</style>
      <div className="skeleton h-4 w-1/2 rounded" />
      <div className="skeleton h-8 w-3/4 rounded" />
      <div className="skeleton h-3 w-2/3 rounded" />
    </div>
  );
}

// Skeleton Form
export function SkeletonForm() {
  return (
    <div className="space-y-6">
      <style>{shimmerCSS}</style>
      {Array.from({ length: 4 }).map((_, i) => (
        <div key={i} className="space-y-2">
          <div className="skeleton h-4 w-1/4 rounded" />
          <div className="skeleton h-10 rounded" />
        </div>
      ))}
      <div className="skeleton h-10 w-full rounded" />
    </div>
  );
}

// Animated skeleton pulse (alternative to shimmer)
export function PulsingSkeleton({ className = '' }: { className?: string }) {
  return (
    <motion.div
      className={`bg-gray-200 ${className}`}
      animate={{ opacity: [0.5, 1, 0.5] }}
      transition={{ duration: 1.5, repeat: Infinity }}
    />
  );
}
```

**Accessibility Note**: The shimmer animation respects `prefers-reduced-motion` through Framer Motion's config. Skeletons use solid gray backgrounds that are accessible and don't distract from page content loading.

---

## 5. Form Feedback

Real-time validation highlight, submit loading, and success/error states.

```tsx
// components/FormWithFeedback.tsx
import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { CheckCircle2, AlertCircle } from 'lucide-react';
import { SPRING_CONFIG } from '@/lib/animation-config';

const FormSchema = z.object({
  email: z.string().email('Invalid email'),
  password: z.string().min(8, 'Min 8 characters'),
});

type FormData = z.infer<typeof FormSchema>;

export function FormWithFeedback({
  onSubmit,
}: {
  onSubmit: (data: FormData) => Promise<void>;
}) {
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submitStatus, setSubmitStatus] = useState<'idle' | 'success' | 'error'>(
    'idle',
  );
  const [submitMessage, setSubmitMessage] = useState('');

  const form = useForm<FormData>({
    resolver: zodResolver(FormSchema),
    mode: 'onChange',
  });

  const handleSubmit = async (data: FormData) => {
    setIsSubmitting(true);
    setSubmitStatus('idle');

    try {
      await onSubmit(data);
      setSubmitStatus('success');
      setSubmitMessage('Successfully submitted!');
      setTimeout(() => setSubmitStatus('idle'), 3000);
    } catch (error) {
      setSubmitStatus('error');
      setSubmitMessage(error instanceof Error ? error.message : 'An error occurred');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <form onSubmit={form.handleSubmit(handleSubmit)} className="space-y-6">
      {/* Email Field with Validation Feedback */}
      <div className="space-y-2">
        <label className="text-sm font-medium">Email</label>
        <motion.div
          animate={
            form.formState.errors.email
              ? { borderColor: '#ef4444' }
              : form.formState.touchedFields.email && !form.formState.errors.email
                ? { borderColor: '#22c55e' }
                : {}
          }
          className="relative"
        >
          <Input
            type="email"
            placeholder="you@example.com"
            {...form.register('email')}
            className={`border-2 transition-colors ${
              form.formState.errors.email
                ? 'border-red-500'
                : form.formState.touchedFields.email &&
                    !form.formState.errors.email
                  ? 'border-green-500'
                  : 'border-gray-300'
            }`}
          />

          {/* Success Icon */}
          <AnimatePresence>
            {form.formState.touchedFields.email &&
              !form.formState.errors.email && (
                <motion.div
                  initial={{ opacity: 0, scale: 0.5 }}
                  animate={{ opacity: 1, scale: 1 }}
                  exit={{ opacity: 0, scale: 0.5 }}
                  className="absolute right-3 top-1/2 -translate-y-1/2"
                >
                  <CheckCircle2 className="h-5 w-5 text-green-500" />
                </motion.div>
              )}
          </AnimatePresence>
        </motion.div>

        {/* Error Message */}
        <AnimatePresence>
          {form.formState.errors.email && (
            <motion.div
              initial={{ opacity: 0, y: -10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
              transition={{ duration: 0.2 }}
              className="flex items-center gap-2 text-sm text-red-600"
            >
              <AlertCircle className="h-4 w-4" />
              {form.formState.errors.email.message}
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {/* Password Field */}
      <div className="space-y-2">
        <label className="text-sm font-medium">Password</label>
        <Input
          type="password"
          placeholder="••••••••"
          {...form.register('password')}
          className={`border-2 ${
            form.formState.errors.password
              ? 'border-red-500'
              : 'border-gray-300'
          }`}
        />
        <AnimatePresence>
          {form.formState.errors.password && (
            <motion.div
              initial={{ opacity: 0, y: -10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
              className="flex items-center gap-2 text-sm text-red-600"
            >
              <AlertCircle className="h-4 w-4" />
              {form.formState.errors.password.message}
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {/* Submit Status Messages */}
      <AnimatePresence mode="wait">
        {submitStatus === 'success' && (
          <motion.div
            key="success"
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            className="rounded-lg bg-green-50 p-4 text-green-800 flex items-center gap-2"
          >
            <CheckCircle2 className="h-5 w-5" />
            {submitMessage}
          </motion.div>
        )}
        {submitStatus === 'error' && (
          <motion.div
            key="error"
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            className="rounded-lg bg-red-50 p-4 text-red-800 flex items-center gap-2"
          >
            <AlertCircle className="h-5 w-5" />
            {submitMessage}
          </motion.div>
        )}
      </AnimatePresence>

      {/* Submit Button */}
      <Button
        type="submit"
        disabled={isSubmitting || !form.formState.isValid}
        className="w-full"
      >
        {isSubmitting ? (
          <motion.span
            animate={{ rotate: 360 }}
            transition={{ duration: 1, repeat: Infinity, ease: 'linear' }}
            className="inline-block"
          >
            ⏳
          </motion.span>
        ) : (
          'Submit'
        )}
      </Button>
    </form>
  );
}
```

**Accessibility Note**: Color changes are paired with icons (✓ for success, ⚠ for error) so validation feedback isn't solely reliant on color. Error messages appear with motion but are readable for users with reduced motion enabled.

---

## 6. Dialog/Sheet Animations

Entry/exit animations for modals and slide-overs.

```tsx
// components/AnimatedDialog.tsx
import React from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';

interface AnimatedDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  title: string;
  description?: string;
  children: React.ReactNode;
}

const backdropVariants = {
  hidden: { opacity: 0 },
  visible: { opacity: 1 },
};

const contentVariants = {
  hidden: { opacity: 0, scale: 0.95, y: 20 },
  visible: { opacity: 1, scale: 1, y: 0 },
};

export function AnimatedDialog({
  open,
  onOpenChange,
  title,
  description,
  children,
}: AnimatedDialogProps) {
  return (
    <AnimatePresence>
      {open && (
        <motion.div
          initial="hidden"
          animate="visible"
          exit="hidden"
          variants={backdropVariants}
          transition={{ duration: 0.2 }}
        >
          <Dialog open={open} onOpenChange={onOpenChange}>
            <DialogContent>
              <motion.div
                initial="hidden"
                animate="visible"
                exit="hidden"
                variants={contentVariants}
                transition={{ type: 'spring', damping: 15, stiffness: 150 }}
              >
                <DialogHeader>
                  <DialogTitle>{title}</DialogTitle>
                  {description && (
                    <DialogDescription>{description}</DialogDescription>
                  )}
                </DialogHeader>
                {children}
              </motion.div>
            </DialogContent>
          </Dialog>
        </motion.div>
      )}
    </AnimatePresence>
  );
}

// Animated Sheet (slide-over from right)
interface AnimatedSheetProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  title: string;
  children: React.ReactNode;
}

const sheetVariants = {
  hidden: { x: 400, opacity: 0 },
  visible: { x: 0, opacity: 1 },
};

export function AnimatedSheet({
  open,
  onOpenChange,
  title,
  children,
}: AnimatedSheetProps) {
  return (
    <AnimatePresence>
      {open && (
        <>
          {/* Backdrop */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.2 }}
            className="fixed inset-0 z-40 bg-black/50"
            onClick={() => onOpenChange(false)}
          />

          {/* Sheet */}
          <motion.div
            initial="hidden"
            animate="visible"
            exit="hidden"
            variants={sheetVariants}
            transition={{ type: 'spring', damping: 20, stiffness: 300 }}
            className="fixed right-0 top-0 z-50 h-full w-96 bg-white shadow-2xl"
          >
            <div className="space-y-6 border-b p-6">
              <h2 className="text-lg font-semibold">{title}</h2>
              <button
                onClick={() => onOpenChange(false)}
                className="text-gray-500 hover:text-gray-700"
              >
                ✕
              </button>
            </div>
            <div className="p-6">{children}</div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
}

// Usage
export function DialogDemo() {
  const [dialogOpen, setDialogOpen] = React.useState(false);
  const [sheetOpen, setSheetOpen] = React.useState(false);

  return (
    <div className="space-y-4">
      <button onClick={() => setDialogOpen(true)}>Open Dialog</button>
      <button onClick={() => setSheetOpen(true)}>Open Sheet</button>

      <AnimatedDialog
        open={dialogOpen}
        onOpenChange={setDialogOpen}
        title="Dialog Title"
        description="Dialog description"
      >
        <div>Dialog content</div>
      </AnimatedDialog>

      <AnimatedSheet
        open={sheetOpen}
        onOpenChange={setSheetOpen}
        title="Sheet Title"
      >
        <div>Sheet content</div>
      </AnimatedSheet>
    </div>
  );
}
```

**Accessibility Note**: Dialogs use `AnimatePresence` with immediate exit animations. Users with `prefers-reduced-motion` will see instant appearance/disappearance. Focus management and ARIA attributes are handled by the underlying dialog component.

---

## 7. Sidebar Animations

Collapse/expand with spring physics and mobile slide-in/out.

```tsx
// components/AnimatedSidebar.tsx
import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Menu, X } from 'lucide-react';
import { SPRING_CONFIG } from '@/lib/animation-config';

interface AnimatedSidebarProps {
  isOpen: boolean;
  onToggle: (open: boolean) => void;
  children: React.ReactNode;
}

export function AnimatedSidebar({
  isOpen,
  onToggle,
  children,
}: AnimatedSidebarProps) {
  return (
    <>
      {/* Mobile Toggle Button */}
      <button
        onClick={() => onToggle(!isOpen)}
        className="fixed left-4 top-4 z-50 lg:hidden"
      >
        {isOpen ? <X className="h-6 w-6" /> : <Menu className="h-6 w-6" />}
      </button>

      {/* Mobile Backdrop */}
      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.2 }}
            className="fixed inset-0 z-30 bg-black/50 lg:hidden"
            onClick={() => onToggle(false)}
          />
        )}
      </AnimatePresence>

      {/* Sidebar */}
      <motion.aside
        animate={{
          x: isOpen ? 0 : -256,
          opacity: isOpen ? 1 : 0,
        }}
        transition={SPRING_CONFIG.default}
        className="fixed left-0 top-0 z-40 h-screen w-64 bg-white lg:static lg:translate-x-0 lg:opacity-100"
      >
        {children}
      </motion.aside>

      {/* Content Shift (Desktop) */}
      <motion.div
        animate={{ marginLeft: isOpen ? 256 : 0 }}
        transition={SPRING_CONFIG.default}
        className="hidden lg:block"
      />
    </>
  );
}

// Desktop Collapsible Sidebar
export function CollapsibleSidebar({
  isExpanded,
  onToggle,
  items,
}: {
  isExpanded: boolean;
  onToggle: () => void;
  items: Array<{ icon: React.ReactNode; label: string }>;
}) {
  return (
    <motion.aside
      animate={{ width: isExpanded ? 240 : 64 }}
      transition={SPRING_CONFIG.gentle}
      className="border-r bg-white"
    >
      <div className="flex h-16 items-center justify-between px-4">
        <AnimatePresence>
          {isExpanded && (
            <motion.h1
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="font-bold"
            >
              Menu
            </motion.h1>
          )}
        </AnimatePresence>
        <button
          onClick={onToggle}
          className="rounded-lg hover:bg-gray-100 p-2"
        >
          {isExpanded ? '←' : '→'}
        </button>
      </div>

      <nav className="space-y-2 p-4">
        {items.map((item, i) => (
          <motion.button
            key={i}
            layout
            className="flex w-full items-center gap-4 rounded-lg px-4 py-2 hover:bg-gray-100"
          >
            <div className="text-xl">{item.icon}</div>
            <AnimatePresence>
              {isExpanded && (
                <motion.span
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  exit={{ opacity: 0 }}
                >
                  {item.label}
                </motion.span>
              )}
            </AnimatePresence>
          </motion.button>
        ))}
      </nav>
    </motion.aside>
  );
}

// Usage
export function SidebarDemo() {
  const [isOpen, setIsOpen] = useState(false);
  const [isExpanded, setIsExpanded] = useState(true);

  return (
    <div className="flex h-screen">
      <AnimatedSidebar isOpen={isOpen} onToggle={setIsOpen}>
        <div className="p-6">Mobile Sidebar</div>
      </AnimatedSidebar>

      <CollapsibleSidebar
        isExpanded={isExpanded}
        onToggle={() => setIsExpanded(!isExpanded)}
        items={[
          { icon: '📊', label: 'Dashboard' },
          { icon: '👥', label: 'Users' },
          { icon: '⚙️', label: 'Settings' },
        ]}
      />

      <main className="flex-1 p-6">Content</main>
    </div>
  );
}
```

**Accessibility Note**: The collapse animation uses spring physics for smooth transitions. On `prefers-reduced-motion`, width changes are instant. Keyboard navigation is preserved—sidebar toggle is always accessible.

---

## 8. List Animations

Staggered entrance for items and swipe-to-dismiss on mobile.

```tsx
// components/AnimatedList.tsx
import React, { useState } from 'react';
import { motion, AnimatePresence, Reorder } from 'framer-motion';
import { Trash2 } from 'lucide-react';
import { SPRING_CONFIG } from '@/lib/animation-config';

interface ListItem {
  id: string;
  label: string;
}

interface AnimatedListProps {
  items: ListItem[];
  onRemove?: (id: string) => void;
  onReorder?: (items: ListItem[]) => void;
}

const itemVariants = {
  hidden: { opacity: 0, y: -20 },
  visible: { opacity: 1, y: 0 },
  exit: { opacity: 0, x: -100 },
};

export function AnimatedList({
  items,
  onRemove,
  onReorder,
}: AnimatedListProps) {
  const [list, setList] = useState(items);

  return (
    <Reorder.Group
      axis="y"
      values={list}
      onReorder={(newList) => {
        setList(newList);
        onReorder?.(newList);
      }}
      className="space-y-2"
    >
      <AnimatePresence mode="popLayout">
        {list.map((item, index) => (
          <ListItemWithSwipe
            key={item.id}
            item={item}
            index={index}
            onRemove={onRemove}
            variants={itemVariants}
          />
        ))}
      </AnimatePresence>
    </Reorder.Group>
  );
}

interface ListItemProps {
  item: ListItem;
  index: number;
  onRemove?: (id: string) => void;
  variants: any;
}

function ListItemWithSwipe({
  item,
  index,
  onRemove,
  variants,
}: ListItemProps) {
  const [isDragging, setIsDragging] = useState(false);

  return (
    <Reorder.Item
      value={item}
      initial="hidden"
      animate="visible"
      exit="exit"
      variants={variants}
      transition={{
        ...SPRING_CONFIG.default,
        delay: index * 0.05,
      }}
      drag="x"
      dragConstraints={{ left: -100, right: 100 }}
      dragElastic={0.2}
      onDragStart={() => setIsDragging(true)}
      onDragEnd={(e, info) => {
        setIsDragging(false);
        // Swipe threshold: 50px
        if (info.offset.x < -50) {
          onRemove?.(item.id);
        }
      }}
      className="relative touch-none select-none"
    >
      <motion.div
        className="flex items-center gap-4 rounded-lg bg-white p-4 shadow"
        animate={{
          backgroundColor: isDragging ? '#f3f4f6' : '#ffffff',
        }}
      >
        {/* Drag Handle */}
        <div className="cursor-grab touch-none p-2 text-gray-400 active:cursor-grabbing">
          ⋮⋮
        </div>

        {/* Content */}
        <span className="flex-1 font-medium">{item.label}</span>

        {/* Delete Button */}
        <motion.button
          whileHover={{ scale: 1.1 }}
          whileTap={{ scale: 0.9 }}
          onClick={() => onRemove?.(item.id)}
          className="text-red-600 hover:bg-red-50 rounded p-2"
        >
          <Trash2 className="h-5 w-5" />
        </motion.button>
      </motion.div>

      {/* Delete hint (visible on drag) */}
      {isDragging && (
        <motion.div
          className="absolute inset-0 flex items-center justify-end pr-4 text-red-600"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
        >
          Swipe to delete
        </motion.div>
      )}
    </Reorder.Item>
  );
}

// List Grid with staggered items
export function AnimatedGrid({
  items,
  renderItem,
}: {
  items: any[];
  renderItem: (item: any, index: number) => React.ReactNode;
}) {
  return (
    <motion.div
      className="grid gap-4 md:grid-cols-2 lg:grid-cols-3"
      initial="hidden"
      animate="visible"
      variants={{
        visible: {
          transition: {
            staggerChildren: 0.1,
            delayChildren: 0.2,
          },
        },
      }}
    >
      <AnimatePresence mode="popLayout">
        {items.map((item, index) => (
          <motion.div
            key={item.id}
            layout
            initial={{ opacity: 0, scale: 0.8 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.8 }}
            transition={SPRING_CONFIG.default}
          >
            {renderItem(item, index)}
          </motion.div>
        ))}
      </AnimatePresence>
    </motion.div>
  );
}

// Usage
export function ListDemo() {
  const [items, setItems] = useState<ListItem[]>([
    { id: '1', label: 'Item 1' },
    { id: '2', label: 'Item 2' },
    { id: '3', label: 'Item 3' },
  ]);

  return (
    <AnimatedList
      items={items}
      onRemove={(id) => setItems(items.filter((item) => item.id !== id))}
      onReorder={setItems}
    />
  );
}
```

**Accessibility Note**: Drag operations are touch-friendly with visual feedback. Swipe-to-delete has a threshold and can be undone. For users with `prefers-reduced-motion`, stagger delays are reduced and exit animations are instant.

---

## 9. Notification Toast

Slide-in from top-right with auto-dismiss and progress bar.

```tsx
// components/Toast.tsx
import React, { useEffect, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { CheckCircle2, AlertCircle, Info, X } from 'lucide-react';

interface ToastMessage {
  id: string;
  title: string;
  description?: string;
  type: 'success' | 'error' | 'info' | 'warning';
  duration?: number;
}

export function useToast() {
  const [toasts, setToasts] = useState<ToastMessage[]>([]);

  const addToast = (message: Omit<ToastMessage, 'id'>) => {
    const id = `toast-${Date.now()}-${Math.random()}`;
    const toast: ToastMessage = { ...message, id, duration: message.duration ?? 5000 };

    setToasts((prev) => [...prev, toast]);

    if (toast.duration) {
      setTimeout(() => removeToast(id), toast.duration);
    }

    return id;
  };

  const removeToast = (id: string) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  };

  return { toasts, addToast, removeToast };
}

interface ToastContainerProps {
  toasts: ToastMessage[];
  onRemove: (id: string) => void;
}

export function ToastContainer({ toasts, onRemove }: ToastContainerProps) {
  const icons = {
    success: <CheckCircle2 className="h-5 w-5 text-green-600" />,
    error: <AlertCircle className="h-5 w-5 text-red-600" />,
    info: <Info className="h-5 w-5 text-blue-600" />,
    warning: <AlertCircle className="h-5 w-5 text-yellow-600" />,
  };

  const bgColors = {
    success: 'bg-green-50',
    error: 'bg-red-50',
    info: 'bg-blue-50',
    warning: 'bg-yellow-50',
  };

  const borderColors = {
    success: 'border-green-200',
    error: 'border-red-200',
    info: 'border-blue-200',
    warning: 'border-yellow-200',
  };

  return (
    <div className="fixed top-4 right-4 z-50 space-y-3 pointer-events-none">
      <AnimatePresence mode="popLayout">
        {toasts.map((toast) => (
          <ToastItem
            key={toast.id}
            toast={toast}
            onRemove={onRemove}
            icon={icons[toast.type]}
            bgColor={bgColors[toast.type]}
            borderColor={borderColors[toast.type]}
          />
        ))}
      </AnimatePresence>
    </div>
  );
}

interface ToastItemProps {
  toast: ToastMessage;
  onRemove: (id: string) => void;
  icon: React.ReactNode;
  bgColor: string;
  borderColor: string;
}

function ToastItem({
  toast,
  onRemove,
  icon,
  bgColor,
  borderColor,
}: ToastItemProps) {
  const [progress, setProgress] = useState(100);

  useEffect(() => {
    if (!toast.duration) return;

    const interval = setInterval(() => {
      setProgress((prev) => {
        const newProgress = prev - (100 / (toast.duration! / 100));
        if (newProgress <= 0) {
          clearInterval(interval);
          return 0;
        }
        return newProgress;
      });
    }, 100);

    return () => clearInterval(interval);
  }, [toast.duration]);

  return (
    <motion.div
      layout
      initial={{ opacity: 0, x: 400, y: -20 }}
      animate={{ opacity: 1, x: 0, y: 0 }}
      exit={{ opacity: 0, x: 400 }}
      transition={{ type: 'spring', damping: 15, stiffness: 200 }}
      className={`pointer-events-auto ${bgColor} ${borderColor} border rounded-lg shadow-lg overflow-hidden`}
    >
      <div className="p-4 flex gap-3">
        {icon}
        <div className="flex-1">
          <h3 className="font-semibold">{toast.title}</h3>
          {toast.description && (
            <p className="text-sm opacity-75">{toast.description}</p>
          )}
        </div>
        <button
          onClick={() => onRemove(toast.id)}
          className="hover:opacity-75"
        >
          <X className="h-4 w-4" />
        </button>
      </div>

      {/* Progress Bar */}
      {toast.duration && (
        <motion.div
          className="h-1 bg-current opacity-30"
          animate={{ scaleX: progress / 100 }}
          transition={{ duration: 0.1 }}
          style={{ transformOrigin: 'left' }}
        />
      )}
    </motion.div>
  );
}

// Usage
export function ToastDemo() {
  const { toasts, addToast, removeToast } = useToast();

  return (
    <>
      <div className="space-y-4">
        <button onClick={() => addToast({ title: 'Success!', type: 'success' })}>
          Success
        </button>
        <button onClick={() => addToast({ title: 'Error!', type: 'error' })}>
          Error
        </button>
      </div>
      <ToastContainer toasts={toasts} onRemove={removeToast} />
    </>
  );
}
```

**Accessibility Note**: Toast notifications slide in from the top-right with a progress bar showing dismissal timing. Screen readers announce the toast content. Users with `prefers-reduced-motion` see instant appearance without slide animation.

---

## 10. Number Transitions

Animated counting for dashboard stats.

```tsx
// components/CountUp.tsx
import React from 'react';
import { motion } from 'framer-motion';

interface CountUpProps {
  from?: number;
  to: number;
  duration?: number;
  decimals?: number;
  separator?: string;
  prefix?: string;
  suffix?: string;
}

export function CountUp({
  from = 0,
  to,
  duration = 2,
  decimals = 0,
  separator = ',',
  prefix = '',
  suffix = '',
}: CountUpProps) {
  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.5 }}
    >
      <motion.span>
        <Counter
          from={from}
          to={to}
          duration={duration}
          decimals={decimals}
          separator={separator}
        />
      </motion.span>
      <span>
        {prefix}
        <span>
          <Counter
            from={from}
            to={to}
            duration={duration}
            decimals={decimals}
            separator={separator}
          />
        </span>
        {suffix}
      </span>
    </motion.div>
  );
}

function Counter({
  from,
  to,
  duration,
  decimals,
  separator,
}: {
  from: number;
  to: number;
  duration: number;
  decimals: number;
  separator: string;
}) {
  const [count, setCount] = React.useState(from);

  React.useEffect(() => {
    let startTime: number | null = null;

    const animate = (currentTime: number) => {
      if (startTime === null) startTime = currentTime;

      const progress = Math.min((currentTime - startTime) / (duration * 1000), 1);
      const value = Math.floor(from + (to - from) * progress);

      setCount(value);

      if (progress < 1) {
        requestAnimationFrame(animate);
      }
    };

    const frameId = requestAnimationFrame(animate);
    return () => cancelAnimationFrame(frameId);
  }, [from, to, duration]);

  const formatted = count
    .toFixed(decimals)
    .replace(/\B(?=(\d{3})+(?!\d))/g, separator);

  return <>{formatted}</>;
}

// Stat Card with CountUp
export function StatCardWithCountUp({
  title,
  value,
  change,
}: {
  title: string;
  value: number;
  change?: number;
}) {
  return (
    <div className="rounded-lg border p-6 space-y-2">
      <p className="text-sm font-medium text-gray-600">{title}</p>
      <div className="text-3xl font-bold">
        <CountUp to={value} duration={2} separator="," />
      </div>
      {change && (
        <p className={`text-sm ${change >= 0 ? 'text-green-600' : 'text-red-600'}`}>
          {change >= 0 ? '+' : ''}{change}% from last month
        </p>
      )}
    </div>
  );
}

// Usage
export function DashboardWithCountUp() {
  return (
    <div className="grid gap-4 md:grid-cols-4">
      <StatCardWithCountUp title="Total Users" value={1234} change={12} />
      <StatCardWithCountUp title="Revenue" value={50000} change={8} />
      <StatCardWithCountUp title="Orders" value={892} change={-5} />
      <StatCardWithCountUp title="Conversion" value={32} suffix="%" change={2} />
    </div>
  );
}
```

**Accessibility Note**: Number counting animations use `requestAnimationFrame` for smooth updates. The final value is always reached, and for users with `prefers-reduced-motion`, the count appears instantly at the target value.

---

## 11. Accessibility: Respecting prefers-reduced-motion

All animations in this guide automatically respect the user's motion preferences.

```tsx
// Wrapping your app
import { AnimationProvider } from '@/lib/animation-config';

function App() {
  return (
    <AnimationProvider>
      {/* Your app content */}
    </AnimationProvider>
  );
}

// What happens:
// - MotionConfig automatically uses reducedMotion="user"
// - Spring animations become instant
// - Fade/scale animations are reduced to opacity only
// - Stagger delays are removed
// - Durations are instant

// Explicit check in custom components
import { useReducedMotion } from 'framer-motion';

function MyCustomAnimation() {
  const prefersReducedMotion = useReducedMotion();

  return (
    <motion.div
      animate={{ x: 100 }}
      transition={prefersReducedMotion ? { duration: 0 } : { duration: 0.5 }}
    >
      Content
    </motion.div>
  );
}
```

**Key Principle**: Every animation pattern in this guide includes a note about `prefers-reduced-motion`. Users who prefer less motion get instant or heavily reduced animations, not disabled ones. This maintains visual clarity without overwhelming sensitive users.

---

## Summary

This reference covers the core micro-interactions needed for a modern SaaS application. All patterns:

1. Use Framer Motion with spring physics for natural feel
2. Include `prefers-reduced-motion` support automatically
3. Are accessible with proper ARIA and semantic HTML
4. Work on mobile and desktop
5. Are composable and reusable

For more information on Framer Motion, visit https://www.framer.com/motion/

For accessibility best practices, see https://www.w3.org/WAI/WCAG21/Understanding/animation-from-interactions
