import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "NEXUS-Ω — Build anything. Ship everything. Forget nothing.",
  description: "The world's first memory-native multi-agentic vibe coding platform. 10x faster with Groq.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
