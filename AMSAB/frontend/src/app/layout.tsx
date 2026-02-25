import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "AMSAB — Autonomous Multi-Step Agent Builder",
  description: "Visual, sandboxed, human-in-the-loop AI agent orchestration",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
