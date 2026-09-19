import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "GuardianMesh Command Center",
  description: "Local-first home intelligence and incident response",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return <html lang="en"><body>{children}</body></html>;
}
