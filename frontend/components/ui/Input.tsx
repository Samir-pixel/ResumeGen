import React from "react";
import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  variant?: "light" | "dark";
}

export function Input({ variant = "light", className, ...props }: InputProps) {
  return (
    <input
      className={cn(
        "rounded-inputs py-24 pl-32 pr-64 font-body text-body w-full outline-none transition-colors",
        // Light mode (default): Obsidian text, Pumice/Limestone background
        variant === "light" && "bg-transparent border-[1.5px] border-obsidian/20 text-obsidian focus:border-obsidian placeholder:text-obsidian/50",
        // Dark mode: Chalk text, Chalk border
        variant === "dark" && "bg-transparent border-[1.5px] border-chalk text-chalk focus:border-chalk placeholder:text-chalk/50",
        className
      )}
      {...props}
    />
  );
}

interface TextareaProps extends React.TextareaHTMLAttributes<HTMLTextAreaElement> {
  variant?: "light" | "dark";
}

export function Textarea({ variant = "light", className, ...props }: TextareaProps) {
  return (
    <textarea
      className={cn(
        "rounded-cards p-32 font-body text-body w-full outline-none transition-colors resize-none min-h-[200px]",
        // Light mode
        variant === "light" && "bg-transparent border-[1.5px] border-obsidian/20 text-obsidian focus:border-obsidian placeholder:text-obsidian/50",
        // Dark mode
        variant === "dark" && "bg-transparent border-[1.5px] border-chalk text-chalk focus:border-chalk placeholder:text-chalk/50",
        className
      )}
      {...props}
    />
  );
}
