"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { Activity, AlertTriangle, BrainCircuit, GitBranch, LayoutDashboard, Network, Radio, ScrollText } from "lucide-react";
import { cn } from "@/lib/utils";
import { useAppStore } from "@/store/app-store";

const nav = [
  { href: "/", label: "Dashboard", icon: LayoutDashboard },
  { href: "/graph", label: "Graph", icon: Network },
  { href: "/timeline", label: "Timeline", icon: GitBranch },
  { href: "/conflicts", label: "Conflicts", icon: AlertTriangle },
  { href: "/decisions", label: "Decisions", icon: ScrollText }
];

export function AppShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const connected = useAppStore((s) => s.connected);

  return (
    <div className="min-h-screen">
      <aside className="fixed inset-y-0 left-0 z-30 hidden w-64 border-r border-white/10 bg-slate-950/70 backdrop-blur-xl lg:block">
        <div className="flex h-full flex-col">
          <div className="flex h-16 items-center gap-3 border-b border-white/10 px-5">
            <div className="grid h-9 w-9 place-items-center rounded-md bg-sky-300/14 text-sky-200 ring-1 ring-sky-300/25">
              <BrainCircuit size={19} />
            </div>
            <div>
              <div className="text-sm font-semibold text-white">Nexus-Graph AI</div>
              <div className="text-xs text-slate-400">Cognitive Memory</div>
            </div>
          </div>
          <nav className="space-y-1 p-3">
            {nav.map((item) => {
              const Icon = item.icon;
              const active = pathname === item.href;
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  className={cn(
                    "flex items-center gap-3 rounded-md px-3 py-2.5 text-sm text-slate-400 transition",
                    active && "bg-white/8 text-white shadow-glow",
                    !active && "hover:bg-white/6 hover:text-slate-100"
                  )}
                >
                  <Icon size={17} />
                  {item.label}
                </Link>
              );
            })}
          </nav>
          <div className="mt-auto border-t border-white/10 p-4">
            <div className="flex items-center justify-between rounded-md border border-white/10 bg-white/5 px-3 py-2">
              <div className="flex items-center gap-2 text-xs text-slate-300">
                <Radio size={14} className={connected ? "text-emerald-300" : "text-amber-300"} />
                Socket Stream
              </div>
              <span className={cn("h-2 w-2 rounded-full", connected ? "bg-emerald-300" : "bg-amber-300 animate-pulse")} />
            </div>
          </div>
        </div>
      </aside>
      <div className="lg:pl-64">
        <header className="sticky top-0 z-20 flex h-16 items-center justify-between border-b border-white/10 bg-slate-950/60 px-4 backdrop-blur-xl lg:px-8">
          <div className="flex items-center gap-2 text-sm text-slate-300">
            <Activity size={16} className="text-sky-200" />
            Phase 3 Real-Time Cognitive Interface
          </div>
          <div className="flex items-center gap-2 rounded-full border border-white/10 bg-white/5 px-3 py-1 text-xs text-slate-300">
            <span className={cn("h-2 w-2 rounded-full", connected ? "bg-emerald-300" : "bg-amber-300")} />
            {connected ? "Live" : "Demo Resilient"}
          </div>
        </header>
        <main className="mx-auto max-w-[1580px] px-4 py-6 lg:px-8">{children}</main>
      </div>
    </div>
  );
}
