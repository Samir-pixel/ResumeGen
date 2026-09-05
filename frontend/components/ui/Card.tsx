import React from "react";
import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

interface CardProps extends React.HTMLAttributes<HTMLDivElement> {
  variant?: "limestone" | "ember" | "obsidian";
}

export function Card({ variant = "limestone", className, children, ...props }: CardProps) {
  return (
    <div
      className={cn(
        "rounded-cards p-40 shadow-none border-none",
        variant === "limestone" && "bg-limestone text-obsidian",
        variant === "ember" && "bg-ember text-chalk",
        variant === "obsidian" && "bg-obsidian text-chalk",
        className
      )}
      {...props}
    >
      {children}
    </div>
  );
}
