import * as React from "react";
import { cn } from "@/lib/utils";

const toneMap = {
  neutral: "border-slate-500/25 bg-slate-400/10 text-slate-300",
  info: "border-sky-400/25 bg-sky-400/10 text-sky-200",
  success: "border-emerald-400/25 bg-emerald-400/10 text-emerald-200",
  warning: "border-amber-400/25 bg-amber-400/10 text-amber-200",
  danger: "border-red-400/25 bg-red-400/10 text-red-200"
};

export function Badge({
  className,
  tone = "neutral",
  ...props
}: React.HTMLAttributes<HTMLSpanElement> & { tone?: keyof typeof toneMap }) {
  return (
    <span
      className={cn("inline-flex items-center rounded-full border px-2 py-0.5 text-xs font-medium", toneMap[tone], className)}
      {...props}
    />
  );
}
