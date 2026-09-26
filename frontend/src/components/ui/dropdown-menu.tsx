"use client";

import * as React from "react";

import { cn } from "@/lib/utils";

/**
 * DropdownMenu ligero (sin Radix) controlado por estado interno. Suficiente
 * para el menú de acciones de cada fila de la tabla de órdenes.
 */
interface DropdownContextValue {
  open: boolean;
  setOpen: (open: boolean) => void;
}

const DropdownContext = React.createContext<DropdownContextValue | null>(null);

function useDropdown(): DropdownContextValue {
  const ctx = React.useContext(DropdownContext);
  if (!ctx) throw new Error("DropdownMenu components must be used within <DropdownMenu>");
  return ctx;
}

export function DropdownMenu({ children }: { children: React.ReactNode }) {
  const [open, setOpen] = React.useState(false);
  const ref = React.useRef<HTMLDivElement>(null);

  React.useEffect(() => {
    function onClickOutside(e: MouseEvent) {
      if (ref.current && !ref.current.contains(e.target as Node)) {
        setOpen(false);
      }
    }
    if (open) document.addEventListener("mousedown", onClickOutside);
    return () => document.removeEventListener("mousedown", onClickOutside);
  }, [open]);

  return (
    <DropdownContext.Provider value={{ open, setOpen }}>
      <div className="relative inline-block text-left" ref={ref}>
        {children}
      </div>
    </DropdownContext.Provider>
  );
}

export function DropdownMenuTrigger({
  children,
}: {
  children: React.ReactNode;
}) {
  const { open, setOpen } = useDropdown();
  return (
    <span onClick={() => setOpen(!open)} className="inline-flex">
      {children}
    </span>
  );
}

export function DropdownMenuContent({
  children,
  align = "end",
  className,
}: {
  children: React.ReactNode;
  align?: "start" | "end";
  className?: string;
}) {
  const { open } = useDropdown();
  if (!open) return null;
  return (
    <div
      className={cn(
        "absolute z-50 mt-2 min-w-[10rem] rounded-md border border-border bg-card p-1 shadow-md",
        align === "end" ? "right-0" : "left-0",
        className
      )}
      role="menu"
    >
      {children}
    </div>
  );
}

export function DropdownMenuItem({
  children,
  onClick,
  className,
}: {
  children: React.ReactNode;
  onClick?: () => void;
  className?: string;
}) {
  const { setOpen } = useDropdown();
  return (
    <button
      type="button"
      role="menuitem"
      onClick={() => {
        onClick?.();
        setOpen(false);
      }}
      className={cn(
        "flex w-full cursor-pointer items-center gap-2 rounded-sm px-2 py-1.5 text-left text-sm hover:bg-accent hover:text-accent-foreground",
        className
      )}
    >
      {children}
    </button>
  );
}

export function DropdownMenuLabel({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="px-2 py-1.5 text-xs font-semibold text-muted-foreground">
      {children}
    </div>
  );
}

export function DropdownMenuSeparator() {
  return <div className="my-1 h-px bg-border" />;
}
