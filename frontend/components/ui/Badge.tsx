import React from "react";
import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function Badge({ className, children, ...props }: React.HTMLAttributes<HTMLSpanElement>) {
  return (
    <span
      className={cn(
        "inline-flex items-center justify-center bg-sulfur text-obsidian rounded-pills",
        "px-10 py-4 font-body text-caption font-medium",
        className
      )}
      {...props}
    >
      {children}
    </span>
  );
}
