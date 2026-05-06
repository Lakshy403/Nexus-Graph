import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "@/app/globals.css";
import { AppShell } from "@/components/layout/app-shell";
import { SocketBridge } from "@/components/realtime/socket-bridge";

const inter = Inter({ subsets: ["latin"], display: "swap" });

export const metadata: Metadata = {
  title: "Nexus-Graph AI",
  description: "Real-time cognitive dashboard and knowledge graph interface"
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className="dark">
      <body className={inter.className}>
        <SocketBridge />
        <AppShell>{children}</AppShell>
      </body>
    </html>
  );
}
