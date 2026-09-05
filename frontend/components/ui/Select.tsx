import React from "react";
import { ChevronDown } from "lucide-react";

interface SelectProps extends React.SelectHTMLAttributes<HTMLSelectElement> {
  label: string;
  tone?: "light" | "dark";
}

export function Select({
  label,
  tone = "dark",
  className = "",
  children,
  ...props
}: SelectProps) {
  const dark = tone === "dark";

  return (
    <label className="block min-w-0">
      <span
        className={`mb-8 block text-body-sm ${
          dark ? "text-chalk/70" : "text-obsidian/60"
        }`}
      >
        {label}
      </span>
      <span className="relative block">
        <select
          className={`w-full appearance-none rounded-inputs border-[1.5px] bg-transparent py-20 pl-24 pr-48 text-body outline-none transition-colors ${
            dark
              ? "border-chalk/45 text-chalk focus:border-chalk"
              : "border-obsidian/20 text-obsidian focus:border-obsidian"
          } ${className}`}
          {...props}
        >
          {children}
        </select>
        <ChevronDown
          aria-hidden="true"
          className={`pointer-events-none absolute right-20 top-1/2 h-18 w-18 -translate-y-1/2 ${
            dark ? "text-chalk/60" : "text-obsidian/50"
          }`}
        />
      </span>
    </label>
  );
}
