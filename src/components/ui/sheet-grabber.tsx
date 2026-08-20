'use client';

import { Drawer } from 'vaul';
import type { ComponentProps } from 'react';

/**
 * Bottom-sheet drag handle (t_f21260ee).
 *
 * Wraps vaul's <Drawer.Handle /> to fix the mobile "hard to grab" complaint:
 * the handle is now a FULL-WIDTH touch target, 44px tall (Apple HIG / WCAG
 * minimum), with an inset visual pill centered in it. The size overrides
 * live in globals.css (`html [data-vaul-handle]` — higher specificity than
 * vaul's injected stylesheet, which lands after the app CSS in <head>).
 *
 * Vaul's Handle also gives tap-to-expand for free: a tap cycles to the next
 * snap point (and dismisses from the top snap while dismissible), so the
 * sheet can be revealed without a drag at all.
 *
 * Must be rendered inside a <Drawer.Portal> so it inherits the drawer
 * context (used by WaterDetailSheet / NearbyWatersSheet /
 * AssociationDetailSheet).
 */
export function SheetGrabber(props: ComponentProps<typeof Drawer.Handle>) {
  return (
    <Drawer.Handle {...props} className={`shrink-0 select-none ${props.className ?? ''}`}>
      <span className="h-1 w-9 rounded-full bg-zinc-300 dark:bg-zinc-600" />
    </Drawer.Handle>
  );
}
