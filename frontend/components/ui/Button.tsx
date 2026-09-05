import React from "react";
import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: "primary" | "secondary" | "ghost";
  size?: "default" | "large";
}

export function Button({ variant = "primary", size = "default", className, children, ...props }: ButtonProps) {
  return (
    <button
      className={cn(
        "inline-flex items-center justify-center font-body transition-colors",
        // Primary CTA: Ember fill, Obsidian text, 800px pill radius
        variant === "primary" && "bg-ember text-obsidian rounded-pills hover:bg-opacity-90",
        // Secondary Pill: Transparent, Obsidian border (solid 1.5px), Obsidian text, 40px radius
        variant === "secondary" && "bg-transparent border-[1.5px] border-obsidian text-obsidian rounded-buttons hover:bg-obsidian/5",
        // Ghost: Transparent, Obsidian text, 800px pill radius
        variant === "ghost" && "bg-transparent text-obsidian rounded-pills hover:bg-obsidian/5",
        
        // Sizes
        size === "default" && "text-body px-24 py-12",
        size === "large" && "text-heading-sm px-40 py-20", // For the giant generation button
        
        // Custom secondary padding (16px all sides per DESIGN.md)
        variant === "secondary" && size === "default" && "p-16",
        
        // Ghost padding (0 vertical, 12px horizontal)
        variant === "ghost" && "py-0 px-12 h-auto",
        
        // Disabled
        "disabled:opacity-50 disabled:cursor-not-allowed",
        className
      )}
      {...props}
    >
      {children}
    </button>
  );
}
